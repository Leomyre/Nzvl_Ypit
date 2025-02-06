from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import *
from .models import User, Client, Responsable, Admin
from rest_framework_simplejwt.tokens import AccessToken

# Get the custom User model
User = get_user_model()

class RegisterView(APIView):
    """
    View pour inscrire un nouvel utilisateur.
    """
    """ permission_classes = [permissions.AllowAny] """

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Si l'utilisateur est créé avec succès, on retourne ses données
            return Response(
                {
                    "message": "Utilisateur créé avec succès",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    View pour connecter un utilisateur et lui attribuer un token JWT.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            # Récupérer l'utilisateur et authentifier
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Nom d'utilisateur ou mot de passe incorrect."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not user.check_password(password):
                return Response(
                    {"detail": "Nom d'utilisateur ou mot de passe incorrect."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Créer les tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response(
                {
                    "access_token": access_token,
                    "refresh_token": str(refresh),
                    "token_type": "bearer",
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    View pour récupérer le profil de l'utilisateur connecté via JWT.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Si l'utilisateur est un Client, Responsable ou Admin, afficher les infos de son profil
        if hasattr(user, 'client'):
            profile_data = {
                "user": UserSerializer(user).data,
                "client_info": {
                    "address": user.client.address,
                    "phone_number": user.client.phone_number,
                }
            }
        elif hasattr(user, 'responsable'):
            profile_data = {
                "user": UserSerializer(user).data,
                "responsable_info": {
                    "department": user.responsable.department,
                }
            }
        elif hasattr(user, 'admin'):
            profile_data = {
                "user": UserSerializer(user).data,
                "admin_info": {
                    "privileges": user.admin.privileges,
                }
            }

        return Response(profile_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    View pour déconnecter l'utilisateur (révoquer le token JWT).
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Le simple fait de supprimer le token côté client permet de déconnecter l'utilisateur
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()  # Marquer le token comme révoqué
                return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_205_RESET_CONTENT)

            return Response({"detail": "Le token de déconnexion est manquant."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"detail": "Le token est invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)


class UpdateUserProfileView(APIView):
    """
    Vue pour mettre à jour les informations du profil de l'utilisateur connecté.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        
        # Assurez-vous que l'utilisateur existe dans la base de données
        if not user:
            return Response({"detail": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND)

        # Sérialiser l'utilisateur
        serializer = UpdateUserProfileSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            # Si l'utilisateur est un Client, on met à jour ses informations également
            if hasattr(user, 'client'):
                client_data = request.data.get("client_info")
                if client_data:
                    user.client.address = client_data.get('address', user.client.address)
                    user.client.phone_number = client_data.get('phone_number', user.client.phone_number)
                    user.client.save()

            # Si l'utilisateur est un Responsable, on met à jour son département
            if hasattr(user, 'responsable'):
                responsable_data = request.data.get("responsable_info")
                if responsable_data:
                    user.responsable.department = responsable_data.get('department', user.responsable.department)
                    user.responsable.save()

            # Si l'utilisateur est un Admin, on met à jour ses privilèges
            if hasattr(user, 'admin'):
                admin_data = request.data.get("admin_info")
                if admin_data:
                    user.admin.privileges = admin_data.get('privileges', user.admin.privileges)
                    user.admin.save()

            return Response(
                {"message": "Profil mis à jour avec succès", "user": serializer.data},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)