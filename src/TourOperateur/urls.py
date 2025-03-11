from django.urls import path
from . import views

urlpatterns = [
    path('voyages/populaires/', views.VoyagePopulaireView.as_view(), name='voyages_populaires'),
    path('voyages/', views.VoyageDisponibleView.as_view(), name='voyages_disponibles'),
    path('voyages/<int:pk>/', views.VoyageDetailView.as_view(), name='voyage-detail'),
    path("reservations/", views.ReservationVoyageListView.as_view(), name="reservation-list"),
]
