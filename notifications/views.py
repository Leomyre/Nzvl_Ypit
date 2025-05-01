from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer, MarkAsReadSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filtres
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
            
        read = self.request.query_params.get('read')
        if read in ['true', 'false']:
            queryset = queryset.filter(read=(read == 'true'))
            
        return queryset

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(read=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['patch'])
    def mark_as_read(self, request):
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset().filter(read=False)
        
        if serializer.validated_data.get('all'):
            updated = queryset.update(read=True)
            return Response({'marked': updated})
        
        ids = serializer.validated_data.get('ids', [])
        if ids:
            updated = queryset.filter(id__in=ids).update(read=True)
            return Response({'marked': updated})
        
        return Response(
            {'detail': 'Aucune notification à marquer comme lue'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)