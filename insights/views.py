from time import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FinancialInsight, TravelTrend, AIRecommendation
from .serializers import FinancialInsightSerializer, TravelTrendSerializer, AIRecommendationSerializer
from .services.gemini_service import GeminiService

class FinancialInsightViewSet(viewsets.ModelViewSet):
    queryset = FinancialInsight.objects.all()
    serializer_class = FinancialInsightSerializer
    
    @action(detail=False, methods=['post'])
    def generate_insights(self, request):
        rapport_id = request.data.get('rapport_id')
        if not rapport_id:
            return Response({"error": "rapport_id est requis"}, status=status.HTTP_400_BAD_REQUEST)
        
        gemini_service = GeminiService()
        insights = gemini_service.analyze_financial_report(rapport_id)
        
        if insights:
            serializer = self.get_serializer(insights, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "Impossible de générer des insights"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TravelTrendViewSet(viewsets.ModelViewSet):
    queryset = TravelTrend.objects.all()
    serializer_class = TravelTrendSerializer
    
    @action(detail=False, methods=['post'])
    def analyze_trends(self, request):
        gemini_service = GeminiService()
        trends = gemini_service.analyze_travel_trends()
        
        if trends:
            serializer = self.get_serializer(trends, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "Impossible d'analyser les tendances"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AIRecommendationViewSet(viewsets.ModelViewSet):
    queryset = AIRecommendation.objects.all()
    serializer_class = AIRecommendationSerializer
    
    @action(detail=True, methods=['post'])
    def mark_implemented(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.est_implementee = True
        recommendation.date_implementation = timezone.now()
        recommendation.save()
        
        serializer = self.get_serializer(recommendation)
        return Response(serializer.data)