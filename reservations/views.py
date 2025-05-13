from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q, Sum, Count, F, DecimalField, ExpressionWrapper
from .models import Reservation, Paiement
from voyages.models import Voyage
from users.models import User
from .serializers import ReservationSerializer, MinimalReservationSerializer, PaiementSerializer, StatsReservationsSerializer, ClientReservationSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from datetime import timedelta
from decimal import Decimal
import uuid

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['voyage', 'est_confirmee']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Filtres supplémentaires via query params
        voyage_id = self.request.query_params.get('voyage_id')
        if voyage_id:
            queryset = queryset.filter(voyage_id=voyage_id)

        # Si l'utilisateur est staff/admin, il voit tout
        if user.is_staff:
            return queryset

        # Si l'utilisateur est responsable de voyage
        if hasattr(user, 'responsable_voyages'):
            return queryset.filter(
                Q(utilisateur=user) |
                Q(voyage__responsable=user))
            
        # Utilisateur normal - seulement ses réservations
        return queryset.filter(utilisateur=user)

    def create(self, request, *args, **kwargs):
        voyage_id = request.data.get('voyage')
        utilisateur = request.user
        
        try:
            # Essaye de récupérer une réservation existante
            reservation = Reservation.objects.get(
                utilisateur=utilisateur,
                voyage_id=voyage_id
            )
            
            # Mise à jour complète de la réservation existante
            serializer = self.get_serializer(reservation, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Reservation.DoesNotExist:
            # Création d'une nouvelle réservation
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(utilisateur=utilisateur)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    
    @action(detail=False, methods=['post'], url_path='verifier-reservation')
    def verifier_reservation(self, request):
        voyage_id = request.data.get('voyage')
        utilisateur = request.user
        
        try:
            voyage = Voyage.objects.get(pk=voyage_id)
        except Voyage.DoesNotExist:
            return Response(
                {"detail": "Voyage introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reservation = Reservation.objects.filter(
            utilisateur=utilisateur,
            voyage=voyage
        ).exclude(statut='annulee').first()
        
        if reservation:
            if reservation.est_payee():
                return Response({
                    "status": "deja_reserve",
                    "message": "Vous avez déjà une réservation payée pour ce voyage",
                    "reservation_id": reservation.id
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": "paiement_requis",
                    "message": "Vous avez une réservation en attente de paiement",
                    "reservation_id": reservation.id,
                    "montant_restant": reservation.prix_total - reservation.montant_paye()
                }, status=status.HTTP_200_OK)
        
        # Aucune réservation existante - prêt pour nouvelle réservation
        return Response({
            "status": "nouvelle_reservation",
            "message": "Aucune réservation existante"
        }, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user
        
        # Staff peut tout modifier
        if user.is_staff:
            serializer.save()
            return
            
        # Responsable peut modifier les réservations de ses voyages
        if hasattr(user, 'responsable_voyages') and instance.voyage.responsable == user:
            # Ne permet pas de changer l'utilisateur
            if 'utilisateur' in serializer.validated_data:
                raise PermissionDenied("Vous ne pouvez pas changer le client associé")
            serializer.save()
            return
            
        # Client peut modifier sa propre réservation
        if instance.utilisateur == user:
            # Vérifications supplémentaires pour le client
            if 'voyage' in serializer.validated_data:
                raise PermissionDenied("Vous ne pouvez pas changer le voyage")
            serializer.save()
            return
            
        raise PermissionDenied("Vous n'avez pas la permission de modifier cette réservation")

    def perform_destroy(self, instance):
        user = self.request.user
        
        if user.is_staff:
            instance.delete()
            return
            
        if hasattr(user, 'responsable_voyages') and instance.voyage.responsable == user:
            instance.delete()
            return
            
        if instance.utilisateur == user:
            instance.delete()
            return
            
        raise PermissionDenied("Vous n'avez pas la permission de supprimer cette réservation")

    def get_serializer_class(self):
        if self.action == 'list' and self.request.query_params.get('minimal'):
            return MinimalReservationSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Retourne les statistiques globales des réservations confirmées"""

        reservations = self.get_queryset().filter(est_confirmee=True)

        total_reservations = reservations.count()

        total_participants = reservations.aggregate(
            total=Sum(F('nombre_adultes') + F('nombre_enfants'))
        )['total'] or 0

        chiffre_affaire = reservations.aggregate(
            total=Sum(
                F('nombre_adultes') * F('voyage__prix') +
                F('nombre_enfants') * ExpressionWrapper(
                    F('voyage__prix') * 0.7,
                    output_field=DecimalField()
                )
            )
        )['total'] or 0.0

        total_reservations_confirmees = reservations.filter(est_confirmee=True).count()

        data = {
            'total_reservations': total_reservations,
            'total_reservations_confirmees': total_reservations_confirmees,
            'total_participants': total_participants,
            'chiffre_affaire': chiffre_affaire
        }

        serializer = StatsReservationsSerializer(data)
        return Response(serializer.data)
    

class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['reservation', 'statut', 'methode']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Admins voient tout
        if user.is_staff:
            return queryset

        # Responsables voient les paiements de leurs voyages
        if hasattr(user, 'responsable_voyages'):
            return queryset.filter(
                Q(reservation__utilisateur=user) |
                Q(reservation__voyage__responsable=user))
            
        # Clients normaux voient leurs propres paiements
        return queryset.filter(reservation__utilisateur=user)
    
    def perform_create(self, serializer):
        # Assure qu'une référence unique est générée
        if not serializer.validated_data.get('reference'):
            serializer.validated_data['reference'] = str(uuid.uuid4())
        
        paiement = serializer.save()
        
        if paiement.montant > 0 and paiement.statut == "complete":
            reservation = paiement.reservation
            reservation.est_confirmee = True
            reservation.save()


    @action(detail=True, methods=['post'])
    def marquer_complete(self, request, pk=None):
        paiement = self.get_object()
        
        # Validation métier
        if paiement.statut != 'en_attente':
            return Response(
                {"detail": "Seuls les paiements en attente peuvent être complétés"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        paiement.statut = 'complete'
        paiement.save()
        
        # Mise à jour de la réservation associée
        if paiement.montant >= paiement.reservation.prix_total:
            paiement.reservation.est_confirmee = True
            paiement.reservation.save()
        
        return Response({"status": "Paiement marqué comme complété"})

    @action(detail=True, methods=['post'])
    def demander_remboursement(self, request, pk=None):
        paiement = self.get_object()
        
        if not paiement.peut_etre_rembourse():
            return Response(
                {"detail": "Ce paiement ne peut pas être remboursé"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        paiement.statut = 'rembourse'
        paiement.save()
        
        return Response({"status": "Demande de remboursement enregistrée"})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    total_reservations = Reservation.objects.count()
    new_clients = get_user_model().objects.filter(date_joined__month=request.user.date_joined.month).count()
    total_revenue = Paiement.objects.filter(statut='complete').aggregate(somme=Sum('montant'))['somme'] or Decimal('0')
    total_users = get_user_model().objects.count()
    conversion_rate = (total_reservations / total_users * 100) if total_users else 0

    return Response({
        "total_reservations": total_reservations,
        "new_clients": new_clients,
        "total_revenue": f"{total_revenue:.2f} €",
        "conversion_rate": f"{conversion_rate:.1f}%",
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reservations_par_mois(request):
    data = (
        Reservation.objects.annotate(mois=TruncMonth('date_reservation'))
        .values('mois')
        .annotate(total=Count('id'))
        .order_by('mois')
    )
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revenus_par_destination(request):
    today = now()
    start_current = today.replace(day=1)
    start_previous = (start_current - timedelta(days=1)).replace(day=1)

    # Revenu ce mois-ci par destination
    current_month_data = (
        Paiement.objects.filter(
            statut="complete",
            date_mise_a_jour__gte=start_current
        )
        .annotate(nom_destination=F('reservation__voyage__destination__nom'))
        .values('nom_destination')
        .annotate(total=Sum('montant'))
    )

    # Revenu le mois dernier par destination
    previous_month_data = (
        Paiement.objects.filter(
            statut="complete",
            date_mise_a_jour__gte=start_previous,
            date_mise_a_jour__lt=start_current
        )
        .annotate(nom_destination=F('reservation__voyage__destination__nom'))
        .values('nom_destination')
        .annotate(total=Sum('montant'))
    )

    # Convertir en dictionnaires {destination: total}
    current_dict = {item['nom_destination']: item['total'] for item in current_month_data}
    previous_dict = {item['nom_destination']: item['total'] for item in previous_month_data}

    # Fusionner et calculer le trend
    all_destinations = set(current_dict.keys()) | set(previous_dict.keys())
    results = []

    for destination in all_destinations:
        current_total = current_dict.get(destination, 0)
        previous_total = previous_dict.get(destination, 0)

        if previous_total > 0:
            trend = round(((current_total - previous_total) / previous_total) * 100, 2)
        else:
            trend = None if current_total == 0 else 100.0  # ou une autre logique

        results.append({
            "nom_destination": destination,
            "total": current_total,
            "trend": trend,
        })

    # Tri par total décroissant
    results.sort(key=lambda x: x["total"], reverse=True)

    return Response(results)


class ClientListView(viewsets.ViewSet):
    """ permission_classes = [IsAuthenticated] """

    def list(self, request):
        # Récupère tous les utilisateurs avec des réservations
        clients = User.objects.filter(
            reservations__isnull=False
        ).distinct().prefetch_related('reservations')

        # Filtre optionnel par statut de réservation
        status = request.query_params.get('status')
        if status:
            clients = clients.filter(
                reservations__statut=status
            ).distinct()

        serializer = ClientReservationSerializer(clients, many=True)
        return Response(serializer.data)
    
from django.utils.dateparse import parse_date

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reservations_distribution(request):
    date_min = request.GET.get('date_reservation__gte')
    date_max = request.GET.get('date_reservation__lte')

    filters = {}
    if date_min:
        filters['date_reservation__gte'] = parse_date(date_min)
    if date_max:
        filters['date_reservation__lte'] = parse_date(date_max)

    # Grouper par utilisateur et annoter le nombre de réservations
    reservations_par_client = (
        Reservation.objects.filter(**filters)
        .values('utilisateur__username')  # accès au username via la FK 'utilisateur'
        .annotate(count=Count('id'))
        .order_by('-count')  # optionnel : ordre décroissant
    )

    # Renommer le champ pour correspondre à l’attendu
    distribution = [
        {"username": item["utilisateur__username"], "count": item["count"]}
        for item in reservations_par_client
    ]

    return Response(distribution)