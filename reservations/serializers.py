from rest_framework import serializers
from .models import Reservation, Paiement
from voyages.models import Voyage
from users.models import User
from voyages.serializers import VoyageSerializer
from users.serializers import UserSerializer
from decimal import Decimal
import uuid

class ReservationSerializer(serializers.ModelSerializer):
    voyage = VoyageSerializer(read_only=True)
    voyage_id = serializers.PrimaryKeyRelatedField(
        queryset=Voyage.objects.all(),
        source='voyage',
        write_only=True
    )
    utilisateur = UserSerializer(read_only=True)
    prix_total = serializers.SerializerMethodField()
    responsable_voyage = serializers.SerializerMethodField()
    statut = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            'id',
            'voyage',
            'voyage_id',
            'utilisateur',
            'date_depart',
            'statut',
            'nombre_adultes',
            'nombre_enfants',
            'date_reservation',
            'est_confirmee',
            'special_requests',
            'prix_total',
            'responsable_voyage'
        ]
        read_only_fields = ['date_reservation', 'utilisateur']

    def get_prix_total(self, obj):
        return obj.prix_total

    def get_responsable_voyage(self, obj):
        responsable = obj.get_responsable()
        return responsable.email if responsable else None
    
    def validate(self, data):
        voyage = data.get('voyage') or self.instance.voyage if self.instance else None
        utilisateur = self.context['request'].user
        
        if voyage and utilisateur:
            # Vérifie les réservations existantes
            reservation_existante = Reservation.objects.filter(
                utilisateur=utilisateur,
                voyage=voyage
            ).exclude(statut='annulee').first()
            
            if reservation_existante:
                # Vérifie si déjà payée
                if reservation_existante.est_payee():
                    raise serializers.ValidationError(
                        "Vous avez déjà une réservation payée pour ce voyage"
                    )
                # Si non payée, on permet la mise à jour
                if self.instance is None:  # Nouvelle tentative de réservation
                    raise serializers.ValidationError(
                        "Vous avez déjà une réservation en cours pour ce voyage. "
                        "Veuillez compléter le paiement."
                    )
        
        return data
    
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

class MinimalReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'voyage', 'utilisateur', 'date_reservation', 'est_confirmee']


class PaiementSerializer(serializers.ModelSerializer):
    reservation_info = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    methode_display = serializers.CharField(source='get_methode_display', read_only=True)

    class Meta:
        model = Paiement
        fields = [
            'id',
            'reservation',
            'reservation_info',
            'montant',
            'methode',
            'methode_display',
            'statut',
            'reference',
            'statut_display',
            'date_paiement',
            'date_mise_a_jour',
            'details',
            'reste_a_payer'
        ]
        extra_kwargs = {
            'reference': {'read_only': True}  # Empêche la modification via l'API
        }
        read_only_fields = ['date_paiement', 'date_mise_a_jour', 'reste_a_payer']

    def get_reservation_info(self, obj):
        return {
            'id': obj.reservation.id,
            'voyage': str(obj.reservation.voyage),
            'client': obj.reservation.utilisateur.email,
            'prix_total': obj.reservation.prix_total
        }

    def validate(self, data):
        # Validation du montant pour les nouveaux paiements
        if self.instance is None and 'montant' in data:
            reservation = data.get('reservation') or self.context.get('reservation')
            if data['montant'] > reservation.prix_total * Decimal('1.1'):
                raise serializers.ValidationError(
                    "Le montant ne peut excéder 110% du prix total"
                )
        
        return data

    def create(self, validated_data):
        # Génère une référence unique si elle n'est pas fournie
        if 'reference' not in validated_data:
            validated_data['reference'] = str(uuid.uuid4())
        
        return super().create(validated_data)
    
class StatsReservationsSerializer(serializers.Serializer):
    total_reservations = serializers.IntegerField()
    total_participants = serializers.IntegerField()
    total_reservations_confirmees = serializers.IntegerField()
    chiffre_affaire = serializers.DecimalField(max_digits=10, decimal_places=2)


class ClientReservationSerializer(serializers.ModelSerializer):
    reservations_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'reservations_count', 'total_spent']

    def get_reservations_count(self, obj):
        return obj.reservations.count()

    def get_total_spent(self, obj):
        total = sum(
            reservation.prix_total 
            for reservation in obj.reservations.all()
            if hasattr(reservation, 'prix_total')
        )
        return f"{total}€"
