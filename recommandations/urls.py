from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PreferenceUtilisateurViewSet, RecommandationViewSet, FeedbackViewSet

router = DefaultRouter()
router.register(r'preferences', PreferenceUtilisateurViewSet)
router.register(r'recommandations', RecommandationViewSet)
router.register(r'feedbacks', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('mes-preferences/', PreferenceUtilisateurViewSet.as_view({'get': 'mes_preferences', 'put': 'mes_preferences', 'patch': 'mes_preferences'}), name='mes-preferences'),
    path('mes-recommandations/', RecommandationViewSet.as_view({'get': 'mes_recommandations'}), name='mes-recommandations'),
    path('generer-recommandations/', RecommandationViewSet.as_view({'post': 'generer'}), name='generer-recommandations'),
]