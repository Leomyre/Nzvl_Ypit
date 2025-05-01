from rest_framework import serializers
from .models import Reservation, Paiement

class ReservationSerializer(serializers.ModelSerializer):
    total_participants = serializers.ReadOnlyField()
    prix_total = serializers.ReadOnlyField()
    utilisateur = serializers.HiddenField(default=serializers.CurrentUserDefault())

    # Champs du modèle Voyage
    titre = serializers.CharField(source='voyage.titre', read_only=True)
    destination = serializers.CharField(source='voyage.destination', read_only=True)
    date_depart = serializers.DateField(source='voyage.date_depart', read_only=True)

    # Champs liés au dernier paiement (si existant)
    statut = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'voyage',
            'titre',
            'destination',
            'date_depart',
            'nombre_adultes',
            'nombre_enfants',
            'date_reservation',
            'est_confirmee',
            'utilisateur',
            'total_participants',
            'prix_total',
            'statut',
            'reference',
        ]
        read_only_fields = ['date_reservation', 'total_participants', 'prix_total']

    def get_statut(self, obj):
        dernier_paiement = obj.paiements.order_by('-date_paiement').first()
        if dernier_paiement:
            mapping = {
                'complete': 'Payée',
                'en_attente': 'En attente',
                'rembourse': 'Annulée',
                'echoue': 'Annulée',
            }
            return mapping.get(dernier_paiement.statut, 'En attente')
        return 'En attente'

    def get_reference(self, obj):
        dernier_paiement = obj.paiements.order_by('-date_paiement').first()
        return dernier_paiement.reference if dernier_paiement else ""

    def get_titre(self, obj):
        return obj.voyage.titre if obj.voyage else None
