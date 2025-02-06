from django.urls import path
from .views import RegisterView, LoginView, UserProfileView, LogoutView, UpdateUserProfileView

urlpatterns = [
    # URL pour l'inscription
    path('register/', RegisterView.as_view(), name='register'),
    
    # URL pour la connexion
    path('login/', LoginView.as_view(), name='login'),
    
    # URL pour obtenir les informations du profil de l'utilisateur connecté
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # URL pour la déconnexion
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # URL pour mettre à jour les informations du profil de l'utilisateur connecté
    path('profile/update/', UpdateUserProfileView.as_view(), name='update-profile'),
]
