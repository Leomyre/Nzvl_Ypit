from django.db import models
from django.conf import settings
from finances.models import RapportFinancier

class FinancialInsight(models.Model):
    TYPE_CHOICES = [
        ('tendance', 'Tendance'),
        ('recommandation', 'Recommandation'),
        ('alerte', 'Alerte'),
        ('opportunite', 'Opportunité'),
    ]
    
    PRIORITY_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
        ('critique', 'Critique'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priorite = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    rapport = models.ForeignKey(RapportFinancier, on_delete=models.CASCADE, related_name='insights')
    date_creation = models.DateTimeField(auto_now_add=True)
    actions_recommandees = models.JSONField(default=list)
    metriques = models.JSONField(default=dict)
    est_lu = models.BooleanField(default=False)
    est_archive = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_creation']

class TravelTrend(models.Model):
    destination = models.CharField(max_length=100)
    variation_pourcentage = models.DecimalField(max_digits=5, decimal_places=2)
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    nombre_reservations = models.IntegerField()
    revenu_total = models.DecimalField(max_digits=12, decimal_places=2)
    est_en_hausse = models.BooleanField()
    facteurs = models.JSONField(default=list)
    date_analyse = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-variation_pourcentage']

class AIRecommendation(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    impact_estime = models.DecimalField(max_digits=5, decimal_places=2)  # en pourcentage
    cout_implementation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    benefice_potentiel = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    details = models.JSONField(default=dict)
    date_creation = models.DateTimeField(auto_now_add=True)
    est_implementee = models.BooleanField(default=False)
    date_implementation = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-impact_estime']