from rest_framework import serializers
from .models import Transaction, RapportFinancier, Prevision

class TransactionSerializer(serializers.ModelSerializer):
    reservation_details = serializers.SerializerMethodField()
    voyage_titre = serializers.ReadOnlyField(source='voyage.titre')
    utilisateur_nom = serializers.ReadOnlyField(source='utilisateur.username')
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['reference']
    
    def get_reservation_details(self, obj):
        if obj.reservation:
            return {
                'id': obj.reservation.id,
                'statut': obj.reservation.statut,
                'prix_total': str(obj.reservation.prix_total)
            }
        return None

class RapportFinancierSerializer(serializers.ModelSerializer):
    cree_par_nom = serializers.ReadOnlyField(source='cree_par.username')
    
    class Meta:
        model = RapportFinancier
        fields = '__all__'
        read_only_fields = ['benefice_net']

class PrevisionSerializer(serializers.ModelSerializer):
    cree_par_nom = serializers.ReadOnlyField(source='cree_par.username')
    
    class Meta:
        model = Prevision
        fields = '__all__'
        read_only_fields = ['benefice_prevu']