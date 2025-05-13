from rest_framework import serializers
from .models import User, Profile, TourOperatorInfo
from .utils import send_confirmation_email

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'is_client', 'is_responsable', 'phone_number','nationality'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {
                'validators': []  # Désactive temporairement la validation unique
            },
            'username': {
                'validators': []  # Désactive temporairement la validation unique
            }
        }

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Profile
        fields = ['photoUrl', 'user']
        extra_kwargs = {
            'photoUrl': {
                'required': False,
                'allow_null': True
            }
        }

    def validate(self, attrs):
        user_data = attrs.get('user', {})
        request_user = self.context['request'].user
        
        # Vérification email unique
        if 'email' in user_data:
            if User.objects.filter(email=user_data['email']).exclude(id=request_user.id).exists():
                raise serializers.ValidationError({
                    'user': {'email': 'Cet email est déjà utilisé.'}
                })
        
        # Vérification username unique
        if 'username' in user_data:
            if User.objects.filter(username=user_data['username']).exclude(id=request_user.id).exists():
                raise serializers.ValidationError({
                    'user': {'username': 'Ce nom d\'utilisateur est déjà pris.'}
                })
        
        return attrs

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        # Mise à jour utilisateur
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Mise à jour profil
        if 'photoUrl' in validated_data:
            # Si photoUrl est une string et pas un fichier, ne pas écraser
            if not isinstance(validated_data['photoUrl'], str):
                instance.photoUrl = validated_data['photoUrl']
        
        instance.save()
        return instance
    user = UserSerializer()
    
    class Meta:
        model = Profile
        fields = ['photoUrl', 'date_of_birth', 'address', 'preferences', 'user']
        extra_kwargs = {
            'photoUrl': {'required': False, 'allow_null': True}
        }

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        # Mise à jour de l'utilisateur
        if user_data:
            user_serializer = UserSerializer(user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        
        # Mise à jour du profil
        return super().update(instance, validated_data)

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
        fields = ('id', 'username', 'email', 'password','nationality' ,'is_client', 'is_responsable', 'phone_number', 'tour_operator_info')
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
