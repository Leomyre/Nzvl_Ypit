from django.db import models
from django.conf import settings
from voyages.models import Voyage
from django.core.exceptions import ValidationError

class Reservation(models.Model):
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name='reservations')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre_adultes = models.PositiveIntegerField(default=1)
    nombre_enfants = models.PositiveIntegerField(default=0)
    date_reservation = models.DateTimeField(auto_now_add=True)
    est_confirmee = models.BooleanField(default=False)

    class Meta:
        unique_together = ['voyage', 'utilisateur']  # à retirer si plusieurs réservations possibles par user

    def __str__(self):
        return f"Réservation de {self.utilisateur} pour {self.voyage}"

    def clean(self):
        super().clean()
        if self.nombre_adultes <= 0:
            raise ValidationError("Le nombre d'adultes doit être supérieur à 0.")

    @property
    def total_participants(self):
        return self.nombre_adultes + self.nombre_enfants

    @property
    def prix_total(self):
        return self.nombre_adultes * self.voyage.prix_par_personne


class Paiement(models.Model):
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('complete', 'Complété'),
        ('rembourse', 'Remboursé'),
        ('echoue', 'Échoué'),
    ]
    
    METHOD_CHOICES = [
        ('carte', 'Carte de crédit'),
        ('virement', 'Virement bancaire'),
        ('paypal', 'PayPal'),
    ]
    
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    methode = models.CharField(max_length=20, choices=METHOD_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    reference = models.CharField(max_length=100, unique=True)
    date_paiement = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)