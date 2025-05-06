from django.db import models
from django.conf import settings
from voyages.models import Voyage, Destination

class PreferenceUtilisateur(models.Model):
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preferences')
    destinations_favorites = models.ManyToManyField(Destination, blank=True, related_name='favoris_de')
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duree_voyage_min = models.IntegerField(null=True, blank=True, help_text="Durée minimale en jours")
    duree_voyage_max = models.IntegerField(null=True, blank=True, help_text="Durée maximale en jours")
    interets = models.JSONField(default=list)
    saisons_preferees = models.JSONField(default=list)
    types_hebergement = models.JSONField(default=list)
    activites_preferees = models.JSONField(default=list)
    voyageur_avec = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Recommandation(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommandations')
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name='recommandations')
    score = models.FloatField()
    raisons = models.JSONField(default=list)
    date_creation = models.DateTimeField(auto_now_add=True)
    vue = models.BooleanField(default=False)
    cliquee = models.BooleanField(default=False)
    reservee = models.BooleanField(default=False)

class Feedback(models.Model):
    PERTINENCE_CHOICES = [
        (1, 'Pas du tout pertinent'),
        (2, 'Peu pertinent'),
        (3, 'Moyennement pertinent'),
        (4, 'Pertinent'),
        (5, 'Très pertinent'),
    ]
    
    recommandation = models.ForeignKey(Recommandation, on_delete=models.CASCADE, related_name='feedbacks')
    pertinence = models.IntegerField(choices=PERTINENCE_CHOICES)
    commentaire = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)