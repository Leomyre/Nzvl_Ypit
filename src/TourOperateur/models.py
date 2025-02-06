from django.db import models
from django.db.models import Avg

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
    responsable = models.ForeignKey("Accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="agences")  # Responsable de l'agence

    def __str__(self):
        return self.nom

class Voyage(models.Model):
    nom = models.CharField(max_length=100)
    ville_depart = models.CharField(max_length=100)
    date_depart = models.DateTimeField()
    ville_arrive = models.CharField(max_length=100)
    date_arrive_prevu = models.DateTimeField()
    date_arrive_reel = models.DateTimeField(null=True, blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    place = models.IntegerField()

    types_transport = models.ManyToManyField(TypesTransport, related_name="voyages")  # Plusieurs types de transport possibles
    agence = models.ForeignKey(AgenceVoyage, on_delete=models.CASCADE, related_name="voyages")  # Une agence peut avoir plusieurs voyages

    def __str__(self):
        return self.nom

    def moyenne_notes(self):
        moyenne = self.avis.aggregate(Avg('note'))['note__avg']
        return round(moyenne, 1) if moyenne else 0

    @staticmethod
    def voyages_populaires():
        return Voyage.objects.annotate(moyenne=Avg('avis__note')).order_by('-moyenne')[:5]  # Top 5 voyages

class AvisVoyage(models.Model):
    voyage = models.ForeignKey(Voyage, on_delete=models.CASCADE, related_name="avis")
    utilisateur = models.ForeignKey("Accounts.User", on_delete=models.CASCADE)  # Adapté selon ton modèle User
    note = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # Notes de 1 à 5
    commentaire = models.TextField(blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avis {self.note}/5 pour {self.voyage.nom} par {self.utilisateur.username}"
