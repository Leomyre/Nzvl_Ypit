from rest_framework import serializers
from .models import User, Profile, TourOperatorInfo
from .utils import send_confirmation_email

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'is_client', 'is_responsable', 'phone_number'
        ]
        read_only_fields = ['id']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'avatar', 'date_of_birth', 'address', 
            'preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TourOperatorInfoSerializer(serializers.ModelSerializer):
    """ Serializer pour les infos de tour opérateur """
    class Meta:
        model = TourOperatorInfo
        fields = [
            'id', 'company_name', 'company_email', 'company_phone', 
            'website', 'address', 'description', 'logo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserRegistrationSerializer(serializers.ModelSerializer):
    tour_operator_info = TourOperatorInfoSerializer(required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'is_client', 'is_responsable', 'phone_number', 'tour_operator_info')
        extra_kwargs = {
            'password': {'write_only': True},
            'is_client': {'required': False},
            'is_responsable': {'required': False},
            'phone_number': {'required': False},
        }

    def create(self, validated_data):
        # Sépare les données tour_operator_info si présentes
        tour_operator_info_data = validated_data.pop('tour_operator_info', None)
        
        # Crée l'utilisateur
        user = User.objects.create_user(**validated_data)

        # Si c'est un responsable et qu'on a des infos tour opérateur, on les crée
        if user.is_responsable and tour_operator_info_data:
            TourOperatorInfo.objects.create(user=user, **tour_operator_info_data)

        # Envoie de l'email de confirmation
        send_confirmation_email(user)

        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class AvatarUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar']

class EmailConfirmationSerializer(serializers.Serializer):
    confirmation_code = serializers.CharField(required=True)
