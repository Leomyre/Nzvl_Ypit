from reservations.models import Reservation
from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, FloatField, Count, Avg
from django.db.models.functions import TruncMonth
from .models import Destination, Voyage, ProgrammeJour, Inclusion, Activite, Avis, HistoriqueConsultation
from .serializers import (
    DestinationSerializer, VoyageSerializer, VoyageDetailSerializer,
    ProgrammeJourSerializer,  ActiviteSerializer,
    AvisSerializer, CreateAvisSerializer, HistoriqueConsultationSerializer
)
from decimal import Decimal
from reservations.serializers import ReservationSerializer
from rest_framework.views import APIView
from django.utils.timezone import now

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [AllowAny]

     # Update (PUT/PATCH)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    # Delete (DELETE)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def revenue_stats(self, request):
        """
        Retourne les statistiques de revenus par destination avec :
        - Revenu total
        - Revenu par destination
        - Revenu par pays
        - Tendance mensuelle
        """
        try:
            # 1. Revenu total
            total_revenue = self.calculate_total_revenue()
            
            # 2. Revenu par destination (détaillé)
            revenue_by_destination = self.get_revenue_by_destination()
            
            # 3. Revenu par pays
            revenue_by_country = self.get_revenue_by_country()
            
            # 4. Tendance mensuelle
            monthly_trend = self.get_monthly_revenue_trend()

            return Response({
                'success': True,
                'data': {
                    'total_revenue': total_revenue,
                    'by_destination': revenue_by_destination,
                    'by_country': revenue_by_country,
                    'monthly_trend': monthly_trend
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

    def calculate_total_revenue(self):
        """Calcule le revenu total de toutes les réservations"""
        from django.db.models import Sum
        from voyages.models import Voyage
        
        return Voyage.objects.aggregate(
            total_revenue=Sum(
                ExpressionWrapper(
                    F('reservations__nombre_adultes') * F('prix') + 
                    F('reservations__nombre_enfants') * F('prix') * Decimal("0.7"),
                    output_field=FloatField()
                )
            )
        )['total_revenue'] or 0

    def get_revenue_by_destination(self):
        """Retourne le revenu détaillé par destination"""
        from .models import Destination
        
        return Destination.objects.annotate(
            adult_reservations=Sum('voyages__reservations__nombre_adultes'),
            child_reservations=Sum('voyages__reservations__nombre_enfants'),
            adult_revenue=Sum(
                ExpressionWrapper(
                    F('voyages__reservations__nombre_adultes') * F('voyages__prix'),
                    output_field=FloatField()
                )
            ),
            child_revenue=Sum(
                ExpressionWrapper(
                    F('voyages__reservations__nombre_enfants') * F('voyages__prix') * Decimal("0.7"),
                    output_field=FloatField()
                )
            ),
            total_revenue=F('adult_revenue') + F('child_revenue')
        ).values(
            'id',
            'nom',
            'pays',
            'adult_reservations',
            'child_reservations',
            'adult_revenue',
            'child_revenue',
            'total_revenue'
        ).order_by('-total_revenue')

    def get_revenue_by_country(self):
        """Retourne le revenu agrégé par pays"""
        from .models import Destination
        
        return Destination.objects.values('pays').annotate(
            total_revenue=Sum(
                ExpressionWrapper(
                    F('voyages__reservations__nombre_adultes') * F('voyages__prix') +
                    F('voyages__reservations__nombre_enfants') * F('voyages__prix')*Decimal("0.7"),
                    output_field=FloatField()
                )
            ),
            destination_count=Count('id', distinct=True),
            voyage_count=Count('voyages', distinct=True)
        ).order_by('-total_revenue')

    def get_monthly_revenue_trend(self, months=12):
        """Retourne l'évolution mensuelle des revenus"""
        from django.db.models.functions import TruncMonth
        from reservations.models import Reservation
        
        return Reservation.objects.annotate(
            month=TruncMonth('date_reservation')
        ).values('month').annotate(
            total_revenue=Sum(
                ExpressionWrapper(
                    F('nombre_adultes') * F('voyage__prix') +
                    F('nombre_enfants') * F('voyage__prix')* Decimal("0.7"),
                    output_field=FloatField()
                )
            ),
            reservation_count=Count('id')
        ).order_by('-month')[:months]

    # Endpoint custom pour stats
    @action(detail=False, methods=['get'])
    def stats(self, request):
        from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, FloatField
        from django.db.models.functions import TruncMonth
        from decimal import Decimal
        from reservations.models import Reservation

        # Base statistics
        count = Destination.objects.count()

        # Most popular destinations
        popular = Destination.objects.annotate(
            reservation_count=Count('voyages__reservations', distinct=True),
            total_revenue=Sum(
                ExpressionWrapper(
                    F('voyages__reservations__nombre_adultes') * F('voyages__prix') +
                    F('voyages__reservations__nombre_enfants') * (F('voyages__prix') * Decimal('0.7')),
                    output_field=FloatField()
                )
            ),
        ).order_by('-reservation_count')[:5]

        # Statistics by country
        countries = Destination.objects.values('pays').annotate(
            count=Count('id', distinct=True),
            reservations=Count('voyages__reservations', distinct=True),
            revenue=Sum(
                ExpressionWrapper(
                    F('voyages__reservations__nombre_adultes') * F('voyages__prix') +
                    F('voyages__reservations__nombre_enfants') * (F('voyages__prix') * Decimal('0.7')),
                    output_field=FloatField()
                )
            )
        ).order_by('-reservations')

        # Monthly statistics
        monthly_stats = Reservation.objects.annotate(
            month=TruncMonth('date_reservation')
        ).values('month').annotate(
            count=Count('id'),
            revenue=Sum(
                ExpressionWrapper(
                    F('nombre_adultes') * F('voyage__prix') +
                    F('nombre_enfants') * (F('voyage__prix') * Decimal('0.7')),
                    output_field=FloatField()
                )
            )
        ).order_by('month')[:12]

        serializer = self.get_serializer(popular, many=True)
        
        return Response({
            'total_destinations': count,
            'most_popular': serializer.data,
            'by_country': list(countries)[:5],
            'monthly_stats': list(monthly_stats),
            'total_reservations': Reservation.objects.count(),
            'total_revenue': sum(d.total_revenue or 0 for d in popular)  # Changé d['total_revenue'] en d.total_revenue
        })


class VoyageViewSet(viewsets.ModelViewSet):
    queryset = Voyage.objects.select_related('destination').prefetch_related(
        'programmes_jour', 'inclusions'
    )
    permission_classes = [AllowAny]  # Vous pouvez changer cela en IsAuthenticated si nécessaire.
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VoyageSerializer
        return VoyageDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = VoyageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reserver(self, request, pk=None):
        voyage = self.get_object()
        serializer = ReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nombre_adultes = serializer.validated_data['nombre_adultes']
        nombre_enfants = serializer.validated_data['nombre_enfants']

        # 🔥 Ici, tu peux faire ce que tu veux avec les infos : création de réservation, email, paiement, etc.
        # Exemple basique :
        total_participants = nombre_adultes + nombre_enfants

        # Enregistrer la réservation ici (non encore codé, dépend si tu veux créer un modèle Réservation)
        return Response({
            'message': 'Réservation enregistrée',
            'voyage': voyage.titre,
            'participants': total_participants,
            'adultes': nombre_adultes,
            'enfants': nombre_enfants
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def activites(self, request, pk=None):
        voyage = self.get_object()
        activites = Activite.objects.filter(destination=voyage.destination)
        serializer = ActiviteSerializer(activites, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated:
            HistoriqueConsultation.objects.get_or_create(
                utilisateur=request.user,
                voyage=instance
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ProgrammeJourViewSet(viewsets.ModelViewSet):
    queryset = ProgrammeJour.objects.all()
    serializer_class = ProgrammeJourSerializer
    

    def get_queryset(self):
        return self.queryset.filter(voyage_id=self.kwargs['voyage_pk'])

    def perform_create(self, serializer):
        voyage = get_object_or_404(Voyage, pk=self.kwargs['voyage_pk'])
        if not serializer.is_valid():
            print(serializer.errors)
        serializer.save(voyage=voyage)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == 400:
            print("Erreur de validation PUT:", response.data)
        return response

class ActiviteViewSet(viewsets.ModelViewSet):
    queryset = Activite.objects.select_related('destination')
    serializer_class = ActiviteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        destination_id = self.request.query_params.get('destination')
        if destination_id:
            queryset = queryset.filter(destination_id=destination_id)
        return queryset

class AvisViewSet(viewsets.ModelViewSet):
    queryset = Avis.objects.select_related('utilisateur', 'voyage')
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateAvisSerializer
        return AvisSerializer

    def get_queryset(self):
        return self.queryset.filter(voyage_id=self.kwargs['voyage_pk'])

    def perform_create(self, serializer):
        voyage = get_object_or_404(Voyage, pk=self.kwargs['voyage_pk'])
        serializer.save(utilisateur=self.request.user, voyage=voyage)

class VoyagesPopulairesView(generics.ListAPIView):
    queryset = Voyage.objects.filter(est_populaire=True)
    serializer_class = VoyageSerializer

class VoyagesRecommandesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # On récupère les destinations où l'utilisateur a réservé ou consulté
        voyages_reserves = Voyage.objects.filter(responsable=user)
        destinations_vues = HistoriqueConsultation.objects.filter(utilisateur=user).values_list('voyage__destination', flat=True)

        destinations_interessees = set(voyages_reserves.values_list('destination', flat=True)) | set(destinations_vues)

        voyages_recommandes = Voyage.objects.filter(destination_id__in=destinations_interessees, est_recommande=True).exclude(responsable=user)[:10]

        serializer = VoyageSerializer(voyages_recommandes, many=True)
        return Response(serializer.data)
    
class HistoriqueConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = HistoriqueConsultationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Renvoie les consultations de l'utilisateur connecté
        return HistoriqueConsultation.objects.filter(utilisateur=self.request.user).order_by('-date_consultation')

    def perform_create(self, serializer):
        # Si une consultation existe déjà, on la met à jour plutôt que de créer un doublon
        voyage = serializer.validated_data['voyage']
        instance, created = HistoriqueConsultation.objects.update_or_create(
            utilisateur=self.request.user,
            voyage=voyage,
            defaults={'date_consultation': now()}
        )
        return instance

    @action(detail=False, methods=['post'], url_path='enregistrer')
    def enregistrer_consultation(self, request):
        voyage_id = request.data.get("voyage")
        if not voyage_id:
            return Response({"detail": "ID de voyage manquant."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            voyage = Voyage.objects.get(pk=voyage_id)
        except Voyage.DoesNotExist:
            return Response({"detail": "Voyage introuvable."}, status=status.HTTP_404_NOT_FOUND)

        obj, _ = HistoriqueConsultation.objects.update_or_create(
            utilisateur=request.user,
            voyage=voyage,
            defaults={"date_consultation": now()}
        )

        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)