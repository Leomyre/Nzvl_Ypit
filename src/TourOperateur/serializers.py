from rest_framework import serializers
from .models import Voyage, Trajet, TypesTransport, ReservationVoyage

# Serializer pour TypesTransport
class TypesTransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypesTransport
        fields = ['id', 'nom']

# Serializer pour Trajet
class TrajetSerializer(serializers.ModelSerializer):
    types_transport = TypesTransportSerializer(many=True)

    class Meta:
        model = Trajet
        fields = ['id', 'ville_depart', 'date_depart', 'ville_arrive', 'date_arrive_prevu', 'types_transport']

# Serializer pour Voyage avec ses trajets
class VoyageSerializer(serializers.ModelSerializer):
    trajets = TrajetSerializer(many=True)
    moyenne_notes = serializers.SerializerMethodField()

    class Meta:
        model = Voyage
        fields = ['id', 'nom', 'prix', 'place', 'trajets', 'moyenne_notes']

    def get_moyenne_notes(self, obj):
        return obj.moyenne_notes()

class ReservationVoyageSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source="client.user.username", read_only=True)
    voyage_nom = serializers.CharField(source="voyage.nom", read_only=True)

    class Meta:
        model = ReservationVoyage
        fields = ["id", "client", "client_username", "voyage", "voyage_nom", "date_reservation"]