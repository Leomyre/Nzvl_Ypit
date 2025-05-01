from django.db import models
from django.conf import settings
from voyages.models import Voyage
from reservations.models import Reservation

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('revenu', 'Revenu'),
        ('depense', 'Dépense'),
        ('remboursement', 'Remboursement'),
    ]
    
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    voyage = models.ForeignKey(Voyage, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    categorie = models.CharField(max_length=50, blank=True, null=True)
    reference = models.CharField(max_length=100, unique=True)

class RapportFinancier(models.Model):
    PERIODE_CHOICES = [
        ('jour', 'Jour'),
        ('semaine', 'Semaine'),
        ('mois', 'Mois'),
        ('trimestre', 'Trimestre'),
        ('annee', 'Année'),
        ('personnalise', 'Personnalisé'),
    ]
    
    titre = models.CharField(max_length=200)
    date_debut = models.DateField()
    date_fin = models.DateField()
    periode = models.CharField(max_length=20, choices=PERIODE_CHOICES)
    revenus_totaux = models.DecimalField(max_digits=12, decimal_places=2)
    depenses_totales = models.DecimalField(max_digits=12, decimal_places=2)
    benefice_net = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.JSONField(default=dict)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.benefice_net = self.revenus_totaux - self.depenses_totales
        super().save(*args, **kwargs)

class Prevision(models.Model):
    titre = models.CharField(max_length=200)
    date_debut = models.DateField()
    date_fin = models.DateField()
    revenus_prevus = models.DecimalField(max_digits=12, decimal_places=2)
    depenses_prevues = models.DecimalField(max_digits=12, decimal_places=2)
    benefice_prevu = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.JSONField(default=dict)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.benefice_prevu = self.revenus_prevus - self.depenses_prevues
        super().save(*args, **kwargs)