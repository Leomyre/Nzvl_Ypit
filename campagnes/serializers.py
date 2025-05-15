# serializers.py
from rest_framework import serializers
from .models import Campagne, ModeleEmail

class ModeleEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleEmail
        fields = '__all__'

class CampagneSerializer(serializers.ModelSerializer):
    modele = ModeleEmailSerializer(read_only=True)
    modele_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleEmail.objects.all(),
        source='modele',
        write_only=True
    )
    
    class Meta:
        model = Campagne
        fields = '__all__'