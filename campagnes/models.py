from django.db import models

# Create your models here.
# models.py
from django.db import models
from django.utils import timezone

class ModeleEmail(models.Model):
    TYPE_CHOICES = [
        ('abandon', 'Panier abandonné'),
        ('promotion', 'Promotion'),
        ('rappel', 'Rappel'),
        ('avis', 'Avis'),
        ('fidelite', 'Fidélité'),
    ]
    
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    sujet = models.CharField(max_length=200)
    contenu = models.TextField()
    variables = models.JSONField(default=list)  # Liste des variables disponibles
    
    def __str__(self):
        return self.nom

class Campagne(models.Model):
    STATUT_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('planifiee', 'Planifiée'),
    ]
    
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ModeleEmail.TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='inactive')
    modele = models.ForeignKey(ModeleEmail, on_delete=models.CASCADE)
    delai = models.PositiveIntegerField(null=True, blank=True)  # En heures
    date_prochaine_execution = models.DateTimeField(null=True, blank=True)
    date_derniere_execution = models.DateTimeField(null=True, blank=True)
    destinataires = models.PositiveIntegerField(default=0)
    taux_ouverture = models.FloatField(null=True, blank=True)
    taux_conversion = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.nom
    
    def save(self, *args, **kwargs):
        if self.statut == 'active' and not self.date_prochaine_execution:
            if self.delai:
                self.date_prochaine_execution = timezone.now() + timezone.timedelta(hours=self.delai)
        super().save(*args, **kwargs)