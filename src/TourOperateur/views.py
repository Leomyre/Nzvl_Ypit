from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Voyage
from .serializers import VoyageSerializer
from .models import ReservationVoyage
from .serializers import ReservationVoyageSerializer


class VoyageListView(APIView):
    permission_classes = [IsAuthenticated]  # Tous les utilisateurs authentifiés peuvent y accéder

    def get(self, request):
        # Récupérer tous les voyages
        voyages = Voyage.objects.all().order_by('-date_depart')  # Trie par date de départ (les plus récents en premier)
        
        # Sérialisation des données pour les voyages
        serializer = VoyageSerializer(voyages, many=True)
        
        return Response(serializer.data)
    
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

        # Sérialisation du voyage pour l'afficher
        serializer = VoyageSerializer(voyage)
        return Response(serializer.data)

    def put(self, request, pk):
        voyage = self.get_object(pk)
        if voyage is None:
            return Response({"detail": "Voyage non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        # Vérification que l'utilisateur est un Responsable
        if request.user.user_type != 2:  # Responsable
            return Response({"detail": "Vous n'êtes pas autorisé à modifier ce voyage."}, status=status.HTTP_403_FORBIDDEN)

        # Sérialisation des données et mise à jour du voyage
        serializer = VoyageSerializer(voyage, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Vue pour obtenir les voyages populaires
class VoyagePopulaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        voyages = Voyage.voyages_populaires()
        serializer = VoyageSerializer(voyages, many=True)
        return Response(serializer.data)

# Vue pour obtenir tous les voyages disponibles
class VoyageDisponibleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        voyages = Voyage.objects.all().order_by('-date_depart')
        serializer = VoyageSerializer(voyages, many=True)
        return Response(serializer.data)



class ReservationVoyageListView(generics.ListAPIView):
    serializer_class = ReservationVoyageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Récupère les réservations du client authentifié.
        """
        return ReservationVoyage.objects.filter(client=self.request.user.client).order_by("-date_reservation")