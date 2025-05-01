from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FinancialInsightViewSet, TravelTrendViewSet, AIRecommendationViewSet

router = DefaultRouter()
router.register(r'financial-insights', FinancialInsightViewSet)
router.register(r'travel-trends', TravelTrendViewSet)
router.register(r'recommendations', AIRecommendationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]