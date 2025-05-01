from rest_framework import viewsets, permissions
from .models import Reservation
from .serializers import ReservationSerializer
from rest_framework.exceptions import PermissionDenied

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Limite les réservations à celles de l'utilisateur connecté
        return self.queryset.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    def perform_update(self, serializer):
        reservation = self.get_object()
        if reservation.utilisateur != self.request.user:
            raise PermissionDenied("Vous ne pouvez pas modifier cette réservation.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.utilisateur != self.request.user:
            raise PermissionDenied("Vous ne pouvez pas supprimer cette réservation.")
        instance.delete()
