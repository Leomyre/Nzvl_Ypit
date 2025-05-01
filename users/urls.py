from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet, ProfileViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    # Token routes
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Routes pour la création d'utilisateur et la confirmation de l'email
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register_user'),
    path('confirm_email/', UserViewSet.as_view({'get': 'confirm_email_token'}), name='confirm_email_token'),
    path('confirm_email/code/', UserViewSet.as_view({'post': 'confirm_email_code'}), name='confirm_email_code'),

    # Inclusion des routes générées automatiquement par le router
    path('', include(router.urls)),
]
