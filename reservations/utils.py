from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reservation

@receiver(post_save, sender=Reservation)
def envoyer_email_confirmation(sender, instance, created, **kwargs):
    if created:
        send_mail(
            subject="Confirmation de votre réservation",
            message=f"Bonjour {instance.utilisateur.first_name},\n\n"
                    f"Votre réservation pour le voyage \"{instance.voyage}\" est bien enregistrée !\n"
                    f"Nombre de personnes : {instance.nombre_personnes} (+ {instance.nombre_enfants} enfants)\n"
                    f"Date de départ : {instance.voyage.date_depart}\n\n"
                    f"Merci de votre confiance !",
            from_email="noreply@voyages.com",
            recipient_list=[instance.utilisateur.email],
        )
