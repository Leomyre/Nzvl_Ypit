from Accounts.models import Client, Responsable, User
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user = User.objects.get(id=validated_token["user_id"])
        except User.DoesNotExist:
            raise AuthenticationFailed("Utilisateur non trouvé.", code="user_not_found")

        # Validation du type d'utilisateur
        if user.user_type == 1:  # Client
            client = Client.objects.filter(user=user).first()
            if not client:
                raise AuthenticationFailed("Client non trouvé.", code="client_not_found")

        elif user.user_type == 2:  # Responsable
            responsable = Responsable.objects.filter(user=user).first()
            if not responsable:
                raise AuthenticationFailed("Responsable non trouvé.", code="responsable_not_found")

        return user
