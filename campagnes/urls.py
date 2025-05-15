# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'modeles', views.ModeleEmailViewSet)
router.register(r'campagnes', views.CampagneViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('campagnes/<int:pk>/toggle-status/', views.CampagneViewSet.as_view({'post': 'toggle_status'}), name='campagne-toggle-status'),
]