#Dans TourOperateur/models.py
from django.db import models
from django.db.models import Avg
from django.conf import settings

class TypesTransport(models.Model):
    nom = models.CharField(max_length=50)

    def __str__(self):
        return self.nom

class AgenceVoyage(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    nif = models.CharField(max_length=50)
    stat = models.CharField(max_length=50)
    mail = models.EmailField()

    # Association à un responsable (filtrage sur le type d'utilisateur "Responsable")
    responsable = models.ForeignKey("Accounts.CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="agences", limit_choices_to={'user_type': 'Responsable'})

    def __str__(self):
        return self.nom

class Voyage(models.Model):
    nom = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    place = models.IntegerField()

    agence = models.ForeignKey(AgenceVoyage, on_delete=models.CASCADE, related_name="voyages")

    def __str__(self):
        return f"Voyage {self.nom}"

    def moyenne_notes(self):
        moyenne = self.avis.aggregate(Avg('note'))['note__avg']
        return round(moyenne, 1) if moyenne else 0

    @staticmethod
    def voyages_populaires():
        return Voyage.objects.annotate(moyenne=Avg('avis__note')).order_by('-moyenne')[:5]
    

class Trajet(models.Model):
    voyage = models.ForeignKey("Voyage", on_delete=models.CASCADE, related_name="trajets")
    ville_depart = models.CharField(max_length=100)
    date_depart = models.DateTimeField()
    ville_arrive = models.CharField(max_length=100)
    date_arrive_prevu = models.DateTimeField()
    date_arrive_reel = models.DateTimeField(null=True, blank=True)

    # Relation ManyToMany avec TypesTransport
    types_transport = models.ManyToManyField(TypesTransport, related_name="trajets")

    def __str__(self):
        return f"Trajet de {self.ville_depart} à {self.ville_arrive}"

class AvisVoyage(models.Model):
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name="avis")
    utilisateur = models.ForeignKey("Accounts.CustomUser", on_delete=models.CASCADE)
    note = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    commentaire = models.TextField(blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avis {self.note}/5 pour {self.voyage.nom} par {self.utilisateur.username}"

class ReservationVoyage(models.Model):
    client = models.ForeignKey("Accounts.CustomUser", on_delete=models.CASCADE, related_name="reservations")
    voyage = models.ForeignKey("Voyage", on_delete=models.CASCADE, related_name="reservations")
    date_reservation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Réservation de {self.client.username} pour {self.voyage.nom}"

class InteractionVoyage(models.Model):
    client = models.ForeignKey("Accounts.CustomUser", on_delete=models.CASCADE, related_name="interactions")
    voyage = models.ForeignKey("Voyage", on_delete=models.CASCADE, related_name="interactions")
    type_interaction = models.CharField(max_length=50, choices=[("view", "Consulté"), ("like", "Aimé"), ("favorite", "Favori")])
    date_interaction = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.client.username} - {self.type_interaction} - {self.voyage.nom}"

class HistoriqueConsultation(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voyage = models.ForeignKey('Voyage', on_delete=models.CASCADE)
    date_consultation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.email} a consulté {self.voyage} le {self.date_consultation}"