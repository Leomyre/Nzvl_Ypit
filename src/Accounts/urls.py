from django.urls import path
from .views import RegisterView, LoginView, update_profile, VerifyEmailView,UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('update-profile/', update_profile, name='update_profile'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
]
