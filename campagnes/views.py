# views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Campagne, ModeleEmail
from .serializers import CampagneSerializer, ModeleEmailSerializer
from django.utils import timezone
from .tasks import envoyer_campagne_immediatement  # Importez votre tâche Celery

class ModeleEmailViewSet(viewsets.ModelViewSet):
    queryset = ModeleEmail.objects.all()
    serializer_class = ModeleEmailSerializer
    permission_classes = [permissions.IsAuthenticated]

class CampagneViewSet(viewsets.ModelViewSet):
    queryset = Campagne.objects.all()
    serializer_class = CampagneSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Si la campagne est active, on définit la date d'exécution à maintenant
        if serializer.validated_data.get('statut') == 'active':
            serializer.validated_data['date_prochaine_execution'] = timezone.now()
        
        self.perform_create(serializer)
        
        # Si la campagne est active, on lance l'envoi immédiat
        campagne = serializer.instance
        if campagne.statut == 'active':
            envoyer_campagne_immediatement.delay(campagne.id)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    def toggle_status(self, request, pk=None):
        campagne = self.get_object()
        new_status = 'inactive' if campagne.statut == 'active' else 'active'
        
        # Mise à jour du statut et de la date d'exécution si activation
        update_data = {'statut': new_status}
        if new_status == 'active':
            update_data['date_prochaine_execution'] = timezone.now()
        
        # Utilisation de update plutôt que save() pour éviter les signaux multiples
        Campagne.objects.filter(pk=campagne.pk).update(**update_data)
        campagne.refresh_from_db()
        
        # Si activation, lancer l'envoi des emails
        if new_status == 'active':
            envoyer_campagne_immediatement.delay(campagne.id)
        
        return Response({'status': campagne.statut})