from Accounts.models import Client, Responsable, User
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Récupère l'utilisateur à partir du token JWT.
        """

        try:
            user = User.objects.get(id=validated_token["user_id"])
        except User.DoesNotExist:
            raise AuthenticationFailed("Utilisateur non trouvé.", code="user_not_found")

        # Vérifie s'il s'agit d'un Client ou d'un Responsable
        if user.user_type == 1:  # Client
            try:
                client = Client.objects.get(user=user)
                return client.user  # Retourne l'utilisateur associé
            except Client.DoesNotExist:
                raise AuthenticationFailed("Client non trouvé.", code="client_not_found")

        elif user.user_type == 2:  # Responsable
            try:
                responsable = Responsable.objects.get(user=user)
                return responsable.user
            except Responsable.DoesNotExist:
                raise AuthenticationFailed("Responsable non trouvé.", code="responsable_not_found")

        # Retourne l'Admin directement
        return user
