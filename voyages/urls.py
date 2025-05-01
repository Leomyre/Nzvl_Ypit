from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'destinations', views.DestinationViewSet)
router.register(r'voyages', views.VoyageViewSet)
router.register(r'activites', views.ActiviteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # URLs imbriquées manuelles
    path('voyages/<int:voyage_pk>/programmes/', 
         views.ProgrammeJourViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='voyage-programmes'),
    path('voyages/<int:voyage_pk>/programmes/<int:pk>/', 
         views.ProgrammeJourViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='voyage-programmes-detail'),
    
    path('voyages/<int:voyage_pk>/inclusions/', 
         views.InclusionViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='voyage-inclusions'),
    path('voyages/<int:voyage_pk>/inclusions/<int:pk>/', 
         views.InclusionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='voyage-inclusions-detail'),
    
    path('voyages/<int:voyage_pk>/avis/', 
         views.AvisViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='voyage-avis'),
    path('voyages/<int:voyage_pk>/avis/<int:pk>/', 
         views.AvisViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='voyage-avis-detail'),
    
    path('populaires/', views.VoyagesPopulairesView.as_view(), name='voyages-populaires'),
    path('recommandes/', views.VoyagesRecommandesView.as_view(), name='voyages-recommandes'),
]