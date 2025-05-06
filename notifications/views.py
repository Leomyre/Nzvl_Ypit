from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer, MarkAsReadSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des notifications utilisateur.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'post', 'head', 'options']  # Désactive DELETE

    def get_queryset(self):
        """
        Retourne les notifications de l'utilisateur avec filtres optionnels.
        """
        queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Filtres avancés
        params = self.request.query_params
        filters = Q()
        
        # Filtre par type
        if notification_type := params.get('type'):
            filters &= Q(notification_type=notification_type)
            
        # Filtre par statut de lecture
        if read := params.get('read'):
            if read.lower() in ['true', 'false']:
                filters &= Q(read=(read.lower() == 'true'))
        
        # Filtre par priorité
        if priority := params.get('priority'):
            filters &= Q(priority=priority)
            
        return queryset.filter(filters)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Retourne le nombre de notifications non lues.
        """
        count = self.get_queryset().filter(read=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['patch'])
    def mark_as_read(self, request):
        """
        Marque une ou plusieurs notifications comme lues.
        """
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset().filter(read=False)
        data = {}
        
        if serializer.validated_data.get('all'):
            updated = queryset.update(read=True)
            data['marked_all'] = updated
        else:
            ids = serializer.validated_data.get('ids', [])
            if ids:
                updated = queryset.filter(id__in=ids).update(read=True)
                data['marked_ids'] = updated
        
        # Retourne le nouveau nombre de notifications non lues
        data['unread_count'] = queryset.filter(read=False).count()
        return Response(data)

    @action(detail=True, methods=['patch'])
    def mark_one_as_read(self, request, pk=None):
        """
        Marque une notification spécifique comme lue.
        """
        notification = self.get_object()
        if not notification.read:
            notification.read = True
            notification.save(update_fields=['read'])
            return Response({'status': 'marked', 'unread_count': self.get_queryset().filter(read=False).count()})
        return Response({'status': 'already_read'}, status=status.HTTP_304_NOT_MODIFIED)

    def perform_create(self, serializer):
        """
        Associe automatiquement l'utilisateur courant à la notification.
        """
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Liste des notifications avec métadonnées supplémentaires.
        """
        response = super().list(request, *args, **kwargs)
        response.data['unread_count'] = self.get_queryset().filter(read=False).count()
        return response