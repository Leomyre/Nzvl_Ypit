from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from .models import PreferenceUtilisateur, Recommandation, Feedback
from .serializers import PreferenceUtilisateurSerializer, RecommandationSerializer, FeedbackSerializer
from voyages.models import Voyage, Avis, Destination

class PreferenceUtilisateurViewSet(viewsets.ModelViewSet):
    queryset = PreferenceUtilisateur.objects.all()
    serializer_class = PreferenceUtilisateurSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_responsable:
            return PreferenceUtilisateur.objects.all()
        return PreferenceUtilisateur.objects.filter(utilisateur=user)
    
    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def mes_preferences(self, request):
        try:
            instance = PreferenceUtilisateur.objects.get(utilisateur=request.user)
        except PreferenceUtilisateur.DoesNotExist:
            instance = PreferenceUtilisateur.objects.create(utilisateur=request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

class RecommandationViewSet(viewsets.ModelViewSet):
    queryset = Recommandation.objects.all()
    serializer_class = RecommandationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['utilisateur', 'vue', 'cliquee', 'reservee']
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_responsable:
            return Recommandation.objects.all()
        return Recommandation.objects.filter(utilisateur=user)
    
    @action(detail=False, methods=['get'])
    def mes_recommandations(self, request):
        recommandations = Recommandation.objects.filter(
            utilisateur=request.user
        ).order_by('-score')
        
        # Marquer comme vues
        for rec in recommandations:
            if not rec.vue:
                rec.vue = True
                rec.save(update_fields=['vue'])
        
        serializer = self.get_serializer(recommandations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marquer_cliquee(self, request, pk=None):
        recommandation = self.get_object()
        recommandation.cliquee = True
        recommandation.save(update_fields=['cliquee'])
        
        serializer = self.get_serializer(recommandation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marquer_reservee(self, request, pk=None):
        recommandation = self.get_object()
        recommandation.reservee = True
        recommandation.save(update_fields=['reservee'])
        
        serializer = self.get_serializer(recommandation)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generer(self, request):
        user = request.user
        
        # Récupérer ou créer les préférences de l'utilisateur
        try:
            preferences = PreferenceUtilisateur.objects.get(utilisateur=user)
        except PreferenceUtilisateur.DoesNotExist:
            preferences = PreferenceUtilisateur.objects.create(utilisateur=user)
        
        # Récupérer tous les voyages disponibles
        voyages = Voyage.objects.filter(places_disponibles__gt=0)
        
        if not voyages:
            return Response({"detail": "Aucun voyage disponible"}, status=status.HTTP_404_NOT_FOUND)
        
        # Créer un DataFrame pour les voyages
        voyages_data = []
        for v in voyages:
            voyage_dict = {
                'id': v.id,
                'prix': float(v.prix),
                'destination_id': v.destination.id,
                'niveau_confort': v.niveau_confort,
            }
            
            # Calculer la durée en jours
            duree = (v.date_retour - v.date_depart).days
            voyage_dict['duree'] = duree
            
            # Ajouter au DataFrame
            voyages_data.append(voyage_dict)
        
        df_voyages = pd.DataFrame(voyages_data)
        
        # Calculer les scores de recommandation
        scores = []
        
        for _, voyage in df_voyages.iterrows():
            score = 0
            raisons = []
            
            # Score basé sur le budget
            if preferences.budget_min and preferences.budget_max:
                if preferences.budget_min <= voyage['prix'] <= preferences.budget_max:
                    score += 2
                    raisons.append("Correspond à votre budget")
                elif voyage['prix'] < preferences.budget_min:
                    score += 1
                    raisons.append("Prix inférieur à votre budget minimum")
                else:
                    score -= 1
            
            # Score basé sur la durée
            if preferences.duree_voyage_min and preferences.duree_voyage_max:
                if preferences.duree_voyage_min <= voyage['duree'] <= preferences.duree_voyage_max:
                    score += 2
                    raisons.append("Durée idéale pour vous")
                elif voyage['duree'] < preferences.duree_voyage_min:
                    score -= 1
                else:
                    score -= 0.5
            
            # Score basé sur les destinations favorites
            if preferences.destinations_favorites.filter(id=voyage['destination_id']).exists():
                score += 3
                raisons.append("Destination parmi vos favoris")
            
            # Score basé sur le niveau de confort
            if 'luxe' in preferences.interets and voyage['niveau_confort'] >= 4:
                score += 2
                raisons.append("Niveau de confort élevé")
            elif 'économique' in preferences.interets and voyage['niveau_confort'] <= 3:
                score += 2
                raisons.append("Bon rapport qualité-prix")
            
            # Normaliser le score entre 0 et 1
            score = max(0, min(score / 10, 1))
            
            scores.append({
                'voyage_id': voyage['id'],
                'score': score,
                'raisons': raisons
            })
        
        # Trier par score décroissant
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Créer ou mettre à jour les recommandations
        created_recommendations = []
        
        for score_data in scores[:10]:  # Top 10 recommandations
            voyage = Voyage.objects.get(id=score_data['voyage_id'])
            
            # Vérifier si une recommandation existe déjà
            try:
                recommandation = Recommandation.objects.get(
                    utilisateur=user,
                    voyage=voyage
                )
                # Mettre à jour le score et les raisons
                recommandation.score = score_data['score']
                recommandation.raisons = score_data['raisons']
                recommandation.save()
            except Recommandation.DoesNotExist:
                # Créer une nouvelle recommandation
                recommandation = Recommandation.objects.create(
                    utilisateur=user,
                    voyage=voyage,
                    score=score_data['score'],
                    raisons=score_data['raisons']
                )
            
            created_recommendations.append(recommandation)
        
        serializer = self.get_serializer(created_recommendations, many=True)
        return Response(serializer.data)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()