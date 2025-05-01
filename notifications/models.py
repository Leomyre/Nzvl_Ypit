from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import User  

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('promotion', 'Promotion'),
        ('reservation', 'Réservation'),
        ('reminder', 'Rappel'),
        ('new_feature', 'Nouveauté'),
        ('info', 'Information'),
        ('alert', 'Alerte'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        self.read = True
        self.save()