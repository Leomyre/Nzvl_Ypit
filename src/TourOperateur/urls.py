from django.urls import path
from . import views

urlpatterns = [
    path('voyages/', views.VoyageListView.as_view(), name='voyage-list'),
    path('voyages/<int:pk>/', views.VoyageDetailView.as_view(), name='voyage-detail'),
    path('voyages/populaires/', views.VoyagePopulaireView.as_view(), name='voyages_populaires'),
    path('voyages/disponibles/', views.VoyageDisponibleView.as_view(), name='voyages_disponibles'),
    path("reservations/", views.ReservationVoyageListView.as_view(), name="reservation-list"),

    # Nouveau : Historique des réservations et consultations pour les clients
    path("historique/", views.HistoriqueClientView.as_view(), name="historique-client"),
    path("historique/consultation/<int:voyage_id>/", views.EnregistrerConsultationView.as_view(), name="enregistrer-consultation"),

    # Nouveau : Voir les réservations des voyages pour un responsable
    path("reservations/responsable/", views.ReservationVoyageResponsableView.as_view(), name="reservation-responsable"),
]
