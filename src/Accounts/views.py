from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, ProfileUpdateSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.core.mail import send_mail


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Envoyer l'e-mail avec le code de vérification
        subject = "Vérification de votre compte"
        message = f"Bonjour {user.username},\n\nVotre code de validation est : {user.verification_code}\n\nMerci de l'entrer pour activer et validé votre compte."
        send_mail(subject, message, 'noreply@meetof.com', [user.email])

        return Response({
            "message": "Votre compte a été créé. Vérifiez votre email pour validé votre compte.",
            "user": serializer.data,
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])  # Assurer que l'utilisateur est authentifié
def update_profile(request):
    try:
        user = request.user  # L'utilisateur connecté
        
        # Vérification si l'utilisateur existe
        if not user:
            raise NotFound("Utilisateur non trouvé")
        
        # Sérialisation des données envoyées dans la requête
        serializer = ProfileUpdateSerializer(user, data=request.data)
        
        # Vérification de la validité des données
        if serializer.is_valid():
            serializer.save()  # Sauvegarde des changements
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except NotFound as e:
        # Retourne une erreur 404 si l'utilisateur n'est pas trouvé
        return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Gestion d'autres erreurs non prévues
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = User.objects.get(email=email)
            if user.verification_code == code:
                user.is_verified = True
                user.verification_code = ""  # On supprime le code après validation
                user.save()
                return Response({"message": "Email vérifié avec succès."}, status=status.HTTP_200_OK)
            return Response({"error": "Code invalide."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
