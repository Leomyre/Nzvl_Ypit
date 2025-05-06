from rest_framework import serializers
from .models import PreferenceUtilisateur, Recommandation, Feedback
from voyages.serializers import VoyageSerializer, DestinationSerializer

class PreferenceUtilisateurSerializer(serializers.ModelSerializer):
    destinations_favorites_details = DestinationSerializer(source='destinations_favorites', many=True, read_only=True)
    
    class Meta:
        model = PreferenceUtilisateur
        fields = '__all__'
        read_only_fields = ['utilisateur', 'created_at', 'updated_at']

class RecommandationSerializer(serializers.ModelSerializer):
    voyage_details = VoyageSerializer(source='voyage', read_only=True)
    
    class Meta:
        model = Recommandation
        fields = '__all__'
        read_only_fields = ['utilisateur', 'date_creation']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'