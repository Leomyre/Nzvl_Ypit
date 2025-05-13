from django.db import models
from django.conf import settings
from voyages.models import Voyage
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Q, Sum
import uuid

class Reservation(models.Model):
    voyage = models.ForeignKey(
        Voyage, 
        on_delete=models.CASCADE, 
        related_name='reservations',
        verbose_name="Voyage associé"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Client",
        related_name='reservations'
    )
    nombre_adultes = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre d'adultes"
    )
    nombre_enfants = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'enfants"
    )
    date_depart = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de depart"
    )
    date_reservation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de réservation"
    )
    est_confirmee = models.BooleanField(
        default=False,
        verbose_name="Confirmée"
    )
    special_requests = models.TextField(
        blank=True,
        null=True,
        verbose_name="Demandes spéciales"
    )
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('annulee', 'Annulée'),
    ]
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-date_reservation']
        constraints = [
            models.UniqueConstraint(
                fields=['utilisateur', 'voyage'],
                name='unique_user_voyage',
                condition=~Q(statut='annulee')  # Permet plusieurs réservations si annulées
            )
        ]

    def __str__(self):
        return f"Réservation #{self.id} - {self.utilisateur.email} pour {self.voyage}"

    def clean(self):
        super().clean()
        if self.nombre_adultes <= 0:
            raise ValidationError("Le nombre d'adultes doit être supérieur à 0.")
        if self.nombre_enfants < 0:
            raise ValidationError("Le nombre d'enfants ne peut pas être négatif.")

    def est_payee(self):
        """Vérifie si la réservation est complètement payée"""
        total_paye = self.paiements.filter(statut='complete').aggregate(
            total=Sum('montant')
        )['total'] or 0
        return total_paye >= self.prix_total

    @property
    def total_participants(self):
        return self.nombre_adultes + self.nombre_enfants

    @property
    def prix_total(self):
        return (self.nombre_adultes * self.voyage.prix) + \
               (self.nombre_enfants * (self.voyage.prix * Decimal("0.7")))

    def get_responsable(self):
        """Retourne le responsable du voyage associé"""
        return self.voyage.responsable if hasattr(self.voyage, 'responsable') else None
    


class Paiement(models.Model):
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('complete', 'Complété'),
        ('rembourse', 'Remboursé'),
        ('echoue', 'Échoué'),
        ('annule', 'Annulé'),
    ]
    
    METHOD_CHOICES = [
        ('carte', 'Carte de crédit'),
        ('virement', 'Virement bancaire'),
        ('paypal', 'PayPal'),
        ('especes', 'Espèces'),
    ]
    
    reservation = models.ForeignKey(
        Reservation, 
        on_delete=models.PROTECT,  # Empêche la suppression si paiement existe
        related_name='paiements',
        verbose_name="Réservation associée"
    )
    montant = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Montant payé"
    )
    methode = models.CharField(
        max_length=20, 
        choices=METHOD_CHOICES,
        verbose_name="Méthode de paiement"
    )
    statut = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='en_attente',
        verbose_name="Statut du paiement"
    )
    reference = models.CharField(
        max_length=100, 
        unique=True,
        default=uuid.uuid4,  # Génère automatiquement un UUID
        editable=False,      # Empêche la modification manuelle
        verbose_name="Référence transaction"
    )
    date_paiement = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date du paiement"
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    details = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Détails techniques"
    )

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']
        unique_together = [('reservation',)]
        constraints = [
            models.CheckConstraint(
                check=models.Q(montant__gt=0),
                name="montant_paiement_positif"
            )
        ]

    def __str__(self):
        return f"Paiement #{self.reference} - {self.get_statut_display()}"

    def clean(self):
        super().clean()
        # Validation du montant par rapport à la réservation
        if self.montant > self.reservation.prix_total * Decimal('1.1'):  # Tolérance 10%
            raise ValidationError("Le montant payé dépasse significativement le prix total de la réservation")
        
        # Un paiement complété ne peut pas être modifié
        if self.pk and self.statut == 'complete':
            original = Paiement.objects.get(pk=self.pk)
            if original.statut == 'complete' and any(
                self.__dict__[field] != original.__dict__[field]
                for field in ['montant', 'methode', 'reference']
            ):
                raise ValidationError("Un paiement complété ne peut pas être modifié")

    @property
    def reste_a_payer(self):
        return max(0, self.reservation.prix_total - self.montant)

    def peut_etre_rembourse(self):
        return self.statut == 'complete' and not self.reservation.est_confirmee