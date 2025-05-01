from rest_framework import serializers
from .models import FinancialInsight, TravelTrend, AIRecommendation

class FinancialInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialInsight
        fields = '__all__'

class TravelTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelTrend
        fields = '__all__'

class AIRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRecommendation
        fields = '__all__'