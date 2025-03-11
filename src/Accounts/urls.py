from django.urls import path
from .views import RegisterView, LoginView, update_profile, VerifyEmailView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('update-profile/', update_profile, name='update_profile'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
]
