from django.urls import path
from .views import voyages_disponibles, voyages_populaires

urlpatterns = [
    path('voyages/', voyages_disponibles, name='voyages-disponibles'),
    path('voyages-populaires/', voyages_populaires, name='voyages-populaires'),
]
