from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
import uuid
import pandas as pd
from .models import Transaction, RapportFinancier, Prevision
from .serializers import TransactionSerializer, RapportFinancierSerializer, PrevisionSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'categorie', 'voyage', 'reservation']
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        request.data['reference'] = str(uuid.uuid4())
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        periode = request.query_params.get('periode', 'mois')
        
        # Définir la date de début en fonction de la période
        now = timezone.now()
        if periode == 'jour':
            date_debut = now - timezone.timedelta(days=1)
        elif periode == 'semaine':
            date_debut = now - timezone.timedelta(weeks=1)
        elif periode == 'mois':
            date_debut = now - timezone.timedelta(days=30)
        elif periode == 'trimestre':
            date_debut = now - timezone.timedelta(days=90)
        elif periode == 'annee':
            date_debut = now - timezone.timedelta(days=365)
        else:
            date_debut = request.query_params.get('date_debut')
            if not date_debut:
                return Response({"detail": "Date de début requise pour la période personnalisée"}, 
                               status=status.HTTP_400_BAD_REQUEST)
        
        # Calculer les statistiques
        revenus = Transaction.objects.filter(
            type='revenu', 
            date__gte=date_debut
        ).aggregate(total=Sum('montant'))
        
        depenses = Transaction.objects.filter(
            type='depense', 
            date__gte=date_debut
        ).aggregate(total=Sum('montant'))
        
        remboursements = Transaction.objects.filter(
            type='remboursement', 
            date__gte=date_debut
        ).aggregate(total=Sum('montant'))
        
        # Statistiques par catégorie
        categories = Transaction.objects.filter(
            date__gte=date_debut
        ).values('categorie').annotate(
            total=Sum('montant'),
            count=Count('id')
        )
        
        return Response({
            'revenus': revenus['total'] or 0,
            'depenses': depenses['total'] or 0,
            'remboursements': remboursements['total'] or 0,
            'benefice_net': (revenus['total'] or 0) - (depenses['total'] or 0) + (remboursements['total'] or 0),
            'categories': categories
        })

class RapportFinancierViewSet(viewsets.ModelViewSet):
    queryset = RapportFinancier.objects.all()
    serializer_class = RapportFinancierSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generer(self, request):
        date_debut = request.data.get('date_debut')
        date_fin = request.data.get('date_fin')
        periode = request.data.get('periode')
        titre = request.data.get('titre')
        
        if not all([date_debut, date_fin, periode, titre]):
            return Response({"detail": "Paramètres manquants"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculer les revenus et dépenses
        revenus = Transaction.objects.filter(
            type='revenu', 
            date__gte=date_debut,
            date__lte=date_fin
        ).aggregate(total=Sum('montant'))
        
        depenses = Transaction.objects.filter(
            type='depense', 
            date__gte=date_debut,
            date__lte=date_fin
        ).aggregate(total=Sum('montant'))
        
        # Détails par catégorie
        categories = Transaction.objects.filter(
            date__gte=date_debut,
            date__lte=date_fin
        ).values('categorie', 'type').annotate(
            total=Sum('montant'),
            count=Count('id')
        )
        
        # Créer le rapport
        rapport = RapportFinancier.objects.create(
            titre=titre,
            date_debut=date_debut,
            date_fin=date_fin,
            periode=periode,
            revenus_totaux=revenus['total'] or 0,
            depenses_totales=depenses['total'] or 0,
            details={'categories': list(categories)},
            cree_par=request.user
        )
        
        serializer = self.get_serializer(rapport)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PrevisionViewSet(viewsets.ModelViewSet):
    queryset = Prevision.objects.all()
    serializer_class = PrevisionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generer_prevision(self, request):
        date_debut = request.data.get('date_debut')
        date_fin = request.data.get('date_fin')
        titre = request.data.get('titre')
        
        if not all([date_debut, date_fin, titre]):
            return Response({"detail": "Paramètres manquants"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer les données historiques
        transactions = Transaction.objects.all().values('date', 'montant', 'type')
        
        # Utiliser pandas pour l'analyse prédictive
        df = pd.DataFrame(list(transactions))
        
        # Logique simplifiée de prévision (à remplacer par un modèle ML réel)
        revenus_moyens = df[df['type'] == 'revenu']['montant'].mean() or 0
        depenses_moyennes = df[df['type'] == 'depense']['montant'].mean() or 0
        
        # Calculer le nombre de jours dans la période
        from datetime import datetime
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d')
        nb_jours = (date_fin_obj - date_debut_obj).days
        
        # Estimer les revenus et dépenses pour la période
        revenus_prevus = revenus_moyens * nb_jours
        depenses_prevues = depenses_moyennes * nb_jours
        
        # Créer la prévision
        prevision = Prevision.objects.create(
            titre=titre,
            date_debut=date_debut,
            date_fin=date_fin,
            revenus_prevus=revenus_prevus,
            depenses_prevues=depenses_prevues,
            details={
                'methode': 'moyenne_historique',
                'revenus_moyens_par_jour': float(revenus_moyens),
                'depenses_moyennes_par_jour': float(depenses_moyennes),
                'nb_jours': nb_jours
            },
            cree_par=request.user
        )
        
        serializer = self.get_serializer(prevision)
        return Response(serializer.data, status=status.HTTP_201_CREATED)