from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, RapportFinancierViewSet, PrevisionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)
router.register(r'rapports', RapportFinancierViewSet)
router.register(r'previsions', PrevisionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('transactions/statistiques/', TransactionViewSet.as_view({'get': 'statistiques'}), name='transactions-statistiques'),
    path('rapports/generer/', RapportFinancierViewSet.as_view({'post': 'generer'}), name='generer-rapport'),
    path('previsions/generer/', PrevisionViewSet.as_view({'post': 'generer_prevision'}), name='generer-prevision'),
]