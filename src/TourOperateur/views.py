from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.permissions import IsAuthenticated
from django.db.models import Min
from .models import HistoriqueConsultation, Voyage, Trajet, ReservationVoyage
from .serializers import VoyageSerializer, TrajetSerializer, ReservationVoyageSerializer


class VoyageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        voyages = Voyage.objects.annotate(date_depart=Min('trajets__date_depart')).order_by('-date_depart')
        serializer = VoyageSerializer(voyages, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.user_type != 2:  # Seuls les Responsables peuvent créer un voyage
            return Response({"detail": "Vous n'êtes pas autorisé à créer un voyage."}, status=status.HTTP_403_FORBIDDEN)

        serializer = VoyageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VoyageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Voyage.objects.get(pk=pk)
        except Voyage.DoesNotExist:
            return None

    def get(self, request, pk):
        voyage = self.get_object(pk)
        if voyage is None:
            return Response({"detail": "Voyage non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        serializer = VoyageSerializer(voyage)
        return Response(serializer.data)

    def put(self, request, pk):
        voyage = self.get_object(pk)
        if voyage is None:
            return Response({"detail": "Voyage non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.user_type != 2:
            return Response({"detail": "Vous n'êtes pas autorisé à modifier ce voyage."}, status=status.HTTP_403_FORBIDDEN)

        serializer = VoyageSerializer(voyage, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        voyage = self.get_object(pk)
        if voyage is None:
            return Response({"detail": "Voyage non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.user_type != 2:
            return Response({"detail": "Vous n'êtes pas autorisé à supprimer ce voyage."}, status=status.HTTP_403_FORBIDDEN)

        voyage.delete()
        return Response({"detail": "Voyage supprimé avec succès."}, status=status.HTTP_204_NO_CONTENT)


class TrajetListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TrajetSerializer

    def get_queryset(self):
        voyage_id = self.kwargs['voyage_id']
        return Trajet.objects.filter(voyage_id=voyage_id)

    def post(self, request, *args, **kwargs):
        if request.user.user_type != 2:  # Seuls les Responsables peuvent ajouter un trajet
            return Response({"detail": "Vous n'êtes pas autorisé à ajouter un trajet."}, status=status.HTTP_403_FORBIDDEN)
        
        return self.create(request, *args, **kwargs)


class TrajetDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TrajetSerializer

    def get_queryset(self):
        return Trajet.objects.all()

    def put(self, request, *args, **kwargs):
        if request.user.user_type != 2:
            return Response({"detail": "Vous n'êtes pas autorisé à modifier ce trajet."}, status=status.HTTP_403_FORBIDDEN)
        
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if request.user.user_type != 2:
            return Response({"detail": "Vous n'êtes pas autorisé à supprimer ce trajet."}, status=status.HTTP_403_FORBIDDEN)
        
        return self.destroy(request, *args, **kwargs)


class VoyagePopulaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        voyages = Voyage.voyages_populaires()
        serializer = VoyageSerializer(voyages, many=True)
        return Response(serializer.data)


class VoyageDisponibleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        voyages = Voyage.objects.annotate(date_depart=Min('trajets__date_depart')).order_by('-date_depart')
        serializer = VoyageSerializer(voyages, many=True)
        return Response(serializer.data)


class ReservationVoyageListView(generics.ListAPIView):
    serializer_class = ReservationVoyageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReservationVoyage.objects.filter(client=self.request.user.client).order_by("-date_reservation")


# Vue pour l'historique des réservations et consultations d'un client
class HistoriqueClientView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = request.user.client  # Récupérer le client actuel

        # Récupérer les réservations du client
        reservations = ReservationVoyage.objects.filter(client=client).order_by("-date_reservation")
        reservations_serializer = ReservationVoyageSerializer(reservations, many=True)

        # Récupérer les voyages consultés
        consultations = HistoriqueConsultation.objects.filter(client=client).order_by("-date_consultation")
        consultations_serializer = VoyageSerializer([h.voyage for h in consultations], many=True)

        return Response({
            "reservations": reservations_serializer.data,
            "consultations": consultations_serializer.data
        })

# Vue pour enregistrer l'historique des consultations lorsqu'un client consulte un voyage
class EnregistrerConsultationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, voyage_id):
        client = request.user.client
        voyage = Voyage.objects.filter(id=voyage_id).first()
        
        if not voyage:
            return Response({"detail": "Voyage non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        # Enregistrer la consultation
        HistoriqueConsultation.objects.create(client=client, voyage=voyage)

        return Response({"message": "Consultation enregistrée avec succès."}, status=status.HTTP_201_CREATED)

# Vue pour récupérer les réservations des voyages d'un responsable
class ReservationVoyageResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type != 2:  # Vérifier si l'utilisateur est un responsable
            return Response({"detail": "Vous n'êtes pas autorisé à voir ces réservations."}, status=status.HTTP_403_FORBIDDEN)

        # Récupérer les voyages de l'agence du responsable
        voyages = Voyage.objects.filter(agence=request.user.agence)
        reservations = ReservationVoyage.objects.filter(voyage__in=voyages).order_by("-date_reservation")

        serializer = ReservationVoyageSerializer(reservations, many=True)
        return Response(serializer.data)