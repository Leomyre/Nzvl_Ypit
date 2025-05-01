from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 
                 'read', 'created_at', 'metadata']
        read_only_fields = ['id', 'created_at']

class MarkAsReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    all = serializers.BooleanField(default=False)