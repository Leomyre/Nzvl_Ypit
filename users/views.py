from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Profile
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import update_session_auth_hash
from .serializers import *

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'confirm_email_token', 'confirm_email_code']:
            return [permissions.AllowAny()]
        if self.action in ['me', 'change_password', 'update_avatar', 'resend_confirmation_email']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def confirm_email_token(self, request):
        """ Confirmation par lien avec token """
        token = request.query_params.get('token')
        try:
            user = User.objects.get(confirmation_token=token)
            user.email_confirmed = True
            user.confirmation_token = None
            user.save()
            return Response({'detail': 'Email confirmé avec succès'})
        except User.DoesNotExist:
            return Response({'detail': 'Token invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def confirm_email_code(self, request):
        """ Confirmation par code à 6 chiffres """
        serializer = EmailConfirmationSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['confirmation_code']
            try:
                user = User.objects.get(confirmation_code=code)
                user.email_confirmed = True
                user.confirmation_code = None
                user.save()
                return Response({'detail': 'Email confirmé avec succès'})
            except User.DoesNotExist:
                return Response({'detail': 'Code invalide'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def resend_confirmation_email(self, request):
        user = request.user
        if user.email_confirmed:
            return Response({'detail': 'Email déjà confirmé.'}, status=status.HTTP_400_BAD_REQUEST)
        send_confirmation_email(user)
        return Response({'detail': 'Email de confirmation renvoyé avec succès.'})

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'old_password': 'Incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            return Response({'detail': 'Mot de passe changé avec succès'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'])
    def update_avatar(self, request):
        profile = request.user.profile
        serializer = AvatarUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Avatar mis à jour', 'avatar_url': serializer.data.get('avatar')})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Retourne le profil de l'utilisateur connecté
        return self.request.user.profile