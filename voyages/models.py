from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

# Destination
class Destination(models.Model):
    nom = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    description = models.TextField()
    latitude = models.FloatField(help_text="Latitude en degrés décimaux (WGS 84)")
    longitude = models.FloatField(help_text="Longitude en degrés décimaux (WGS 84)")
    image = models.ImageField(upload_to='destinations/', blank=True, null=True, help_text="Image principale de la destination")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['nom', 'pays']
        ordering = ['pays', 'nom']

    def __str__(self):
        return f"{self.nom}, {self.pays}"

    def get_popularity(self):
        return self.voyages.filter(est_populaire=True).count()

    @property
    def popularity(self):
        return self.get_popularity()

    def clean(self):
        super().clean()
        if not (-90 <= self.latitude <= 90):
            raise ValidationError("La latitude doit être entre -90 et 90 degrés.")
        if not (-180 <= self.longitude <= 180):
            raise ValidationError("La longitude doit être entre -180 et 180 degrés.")
        
class DestinationFinancialData(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='financial_data')
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    expenses = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['destination', 'year', 'month']
        ordering = ['year', 'month']

    def __str__(self):
        return f"{self.destination} - {self.year}-{self.month:02d}"

# Voyage
from users.models import User  # Assurez-vous que le modèle User est correct

class TypeVoyage(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "type de voyage"
        verbose_name_plural = "types de voyage"

    def __str__(self):
        return self.nom

class Voyage(models.Model):
    NIVEAU_CONFORT_CHOICES = [
        (1, '1 étoile'),
        (2, '2 étoiles'),
        (3, '3 étoiles'),
        (4, '4 étoiles'),
        (5, '5 étoiles')
    ]
    type_voyage = models.ForeignKey(TypeVoyage, on_delete=models.SET_NULL, null=True, blank=True, related_name='voyages')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    ville_depart = models.CharField(max_length=200)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='voyages')
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    niveau_confort = models.IntegerField(choices=NIVEAU_CONFORT_CHOICES)
    est_populaire = models.BooleanField(default=False)
    est_recommande = models.BooleanField(default=False)
    responsable = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responsable_voyages', null=True, blank=True)
    nb_consultations = models.IntegerField(default=0)
    images = models.ImageField(upload_to='voyages/', blank=True, null=True, help_text="Image principale du voyages")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "voyage"
        verbose_name_plural = "voyages"

    def clean(self):
        super().clean()
        if self.prix < 0:
            raise ValidationError("Le prix ne peut pas être négatif.")

    def duree(self):
        return self.programmes_jour.count()

    def date_fin_estimee(self):
        from datetime import timedelta
        return self.date_depart + timedelta(days=self.duree() - 1)
    
    @property
    def nombre_participants_total(self):
        return sum(r.nombre_personnes + r.nombre_enfants for r in self.reservations.all())

    @property
    def nombre_reservations(self):
        return self.reservations.count()


# ProgrammeJour
class ProgrammeJour(models.Model):
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name='programmes_jour')
    jour = models.PositiveIntegerField()
    titre = models.CharField(max_length=200, blank=True)
    activite = models.TextField()
    lieu = models.CharField(max_length=200, blank=True)
    repas_inclus = models.CharField(max_length=100, blank=True, help_text="Décrire les repas inclus ce jour-là")

    class Meta:
        ordering = ['jour']
        unique_together = ['voyage', 'jour']
        verbose_name = "programme jour"
        verbose_name_plural = "programmes jour"

    def __str__(self):
        return f"Jour {self.jour} – {self.titre or self.activite[:50]}"

# Inclusion
class Inclusion(models.Model):
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name='inclusions')
    description = models.CharField(max_length=255)
    est_inclus = models.BooleanField(default=True, help_text="Si faux, cela représente une exclusion")

    class Meta:
        verbose_name = "inclusion/exclusion"
        verbose_name_plural = "inclusions/exclusions"

    def __str__(self):
        prefix = "Inclus: " if self.est_inclus else "Non inclus: "
        return prefix + self.description

# Activite
class Activite(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='activites')
    duree = models.DurationField(help_text="Durée estimée de l'activité")
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='activites/', blank=True, null=True)
    est_optionnelle = models.BooleanField(default=False, help_text="Si l'activité est optionnelle (supplément possible)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['titre']
        verbose_name = "activité"
        verbose_name_plural = "activités"

    def __str__(self):
        return self.titre

    def clean(self):
        super().clean()
        if self.prix < 0:
            raise ValidationError("Le prix ne peut pas être négatif.")

# Avis
class Avis(models.Model):
    NOTE_CHOICES = [(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)]

    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name='avis')
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    note = models.IntegerField(choices=NOTE_CHOICES)
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    est_approuve = models.BooleanField(default=False, help_text="L'avis a-t-il été approuvé par un modérateur?")

    class Meta:
        ordering = ['-date_creation']
        unique_together = ['voyage', 'utilisateur']
        verbose_name = "avis"
        verbose_name_plural = "avis"

    def __str__(self):
        return f"Avis de {self.utilisateur} sur {self.voyage} ({self.note}/5)"

# HistoriqueConsultation
class HistoriqueConsultation(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE)
    date_consultation = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-date_consultation']

    def __str__(self):
        return f"{self.utilisateur} a consulté {self.voyage} le {self.date_consultation}"