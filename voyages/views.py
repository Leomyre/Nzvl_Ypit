from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import models
from .models import Destination, Voyage, ProgrammeJour, Inclusion, Activite, Avis, HistoriqueConsultation
from .serializers import (
    DestinationSerializer, VoyageSerializer, VoyageDetailSerializer,
    ProgrammeJourSerializer, InclusionSerializer, ActiviteSerializer,
    AvisSerializer, CreateAvisSerializer
)
from reservations.serializers import ReservationSerializer
from rest_framework.views import APIView

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [AllowAny]

     # Update (PUT/PATCH)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    # Delete (DELETE)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Endpoint custom pour stats
    @action(detail=False, methods=['get'])
    def stats(self, request):
        count = Destination.objects.count()
        popular = Destination.objects.annotate(
            reservation_count=models.Count('voyages__reservations')
        ).order_by('-reservation_count')[:3]
        serializer = self.get_serializer(popular, many=True)
        return Response({
            'total_destinations': count,
            'most_popular': serializer.data
        })

class VoyageViewSet(viewsets.ModelViewSet):
    queryset = Voyage.objects.select_related('destination').prefetch_related(
        'programmes_jour', 'inclusions'
    )
    permission_classes = [AllowAny]  # Vous pouvez changer cela en IsAuthenticated si nécessaire.
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VoyageSerializer
        return VoyageDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = VoyageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reserver(self, request, pk=None):
        voyage = self.get_object()
        serializer = ReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nb_adultes = serializer.validated_data['nb_adultes']
        nb_enfants = serializer.validated_data['nb_enfants']

        # 🔥 Ici, tu peux faire ce que tu veux avec les infos : création de réservation, email, paiement, etc.
        # Exemple basique :
        total_participants = nb_adultes + nb_enfants

        # Enregistrer la réservation ici (non encore codé, dépend si tu veux créer un modèle Réservation)
        return Response({
            'message': 'Réservation enregistrée',
            'voyage': voyage.titre,
            'participants': total_participants,
            'adultes': nb_adultes,
            'enfants': nb_enfants
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def activites(self, request, pk=None):
        voyage = self.get_object()
        activites = Activite.objects.filter(destination=voyage.destination)
        serializer = ActiviteSerializer(activites, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated:
            HistoriqueConsultation.objects.get_or_create(
                utilisateur=request.user,
                voyage=instance
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ProgrammeJourViewSet(viewsets.ModelViewSet):
    queryset = ProgrammeJour.objects.all()
    serializer_class = ProgrammeJourSerializer
    

    def get_queryset(self):
        return self.queryset.filter(voyage_id=self.kwargs['voyage_pk'])

    def perform_create(self, serializer):
        voyage = get_object_or_404(Voyage, pk=self.kwargs['voyage_pk'])
        if not serializer.is_valid():
            print(serializer.errors)
        serializer.save(voyage=voyage)


class InclusionViewSet(viewsets.ModelViewSet):
    queryset = Inclusion.objects.all()
    serializer_class = InclusionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return self.queryset.filter(voyage_id=self.kwargs['voyage_pk'])

    def perform_create(self, serializer):
        voyage = get_object_or_404(Voyage, pk=self.kwargs['voyage_pk'])
        serializer.save(voyage=voyage)

class ActiviteViewSet(viewsets.ModelViewSet):
    queryset = Activite.objects.select_related('destination')
    serializer_class = ActiviteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        destination_id = self.request.query_params.get('destination')
        if destination_id:
            queryset = queryset.filter(destination_id=destination_id)
        return queryset

class AvisViewSet(viewsets.ModelViewSet):
    queryset = Avis.objects.select_related('utilisateur', 'voyage')
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateAvisSerializer
        return AvisSerializer

    def get_queryset(self):
        return self.queryset.filter(voyage_id=self.kwargs['voyage_pk'])

    def perform_create(self, serializer):
        voyage = get_object_or_404(Voyage, pk=self.kwargs['voyage_pk'])
        serializer.save(utilisateur=self.request.user, voyage=voyage)

class VoyagesPopulairesView(generics.ListAPIView):
    queryset = Voyage.objects.filter(est_populaire=True)
    serializer_class = VoyageSerializer

class VoyagesRecommandesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # On récupère les destinations où l'utilisateur a réservé ou consulté
        voyages_reserves = Voyage.objects.filter(responsable=user)
        destinations_vues = HistoriqueConsultation.objects.filter(utilisateur=user).values_list('voyage__destination', flat=True)

        destinations_interessees = set(voyages_reserves.values_list('destination', flat=True)) | set(destinations_vues)

        voyages_recommandes = Voyage.objects.filter(destination_id__in=destinations_interessees, est_recommande=True).exclude(responsable=user)[:10]

        serializer = VoyageSerializer(voyages_recommandes, many=True)
        return Response(serializer.data)