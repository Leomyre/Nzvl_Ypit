from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Client'),
        (2, 'Responsable'),
        (3, 'Admin'),
    )
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)

    # Ajout des related_name pour éviter les conflits avec AbstractUser
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",
        blank=True
    )


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

class Responsable(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    department = models.CharField(max_length=100)

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    privileges = models.TextField()