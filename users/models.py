from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
import random

def generate_confirmation_code():
    """ Génère un code de confirmation à 6 chiffres """
    return str(random.randint(100000, 999999))

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    is_client = models.BooleanField(default=False)
    is_responsable = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email_confirmed = models.BooleanField(default=False)
    confirmation_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)
    confirmation_sent_at = models.DateTimeField(blank=True, null=True)

    def regenerate_token(self):
        """ Régénère un token UUID pour la confirmation par lien """
        self.confirmation_token = uuid.uuid4()
        self.confirmation_sent_at = timezone.now()
        self.save(update_fields=['confirmation_token', 'confirmation_sent_at'])

    def generate_confirmation_code(self):
        """ Génère un code numérique (style 2FA) """
        self.confirmation_code = generate_confirmation_code()
        self.confirmation_sent_at = timezone.now()
        self.save(update_fields=['confirmation_code', 'confirmation_sent_at'])

    def confirmation_expired(self):
        """ Check si la confirmation a expiré (ex: après 24h) """
        if self.confirmation_sent_at:
            return timezone.now() > self.confirmation_sent_at + timezone.timedelta(hours=24)
        return True

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TourOperatorInfo(models.Model):
    """ Infos spécifiques pour les utilisateurs de type Responsable """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tour_operator_info')
    company_name = models.CharField(max_length=255)
    company_email = models.EmailField()
    company_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='tour_operators/logos/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name
