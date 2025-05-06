from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReservationViewSet, ClientListView
from . import views
from .views import dashboard_stats, reservations_par_mois, revenus_par_destination, reservations_distribution

router = DefaultRouter()
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'clients', ClientListView, basename='clients')

urlpatterns = [
    path('', include(router.urls)),
    path('reservations/stats/', 
         views.ReservationViewSet.as_view({'get': 'stats'}), 
         name='reservations-stats'),
         path('dashboardStats/', dashboard_stats, name='dashboard-stats'),
         path('stats/reservations-mensuelles/', reservations_par_mois),
path('stats/revenus-destinations/', revenus_par_destination),
path('clients/distribution/', reservations_distribution, name='reservations-distribution'),

]
