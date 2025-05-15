# services.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
from .models import Campagne
from reservations.models import Reservation
from django.db.models import Count
from voyages.models import Voyage
import logging
from django.template import Template, Context
import time

logger = logging.getLogger(__name__)

def get_destinataires_campagne(campagne):
    """
    Récupère les destinataires en fonction du type de campagne
    """
    try:
        if campagne.type == 'abandon':
            # Réservations non confirmées et non payées
            return Reservation.objects.filter(
                statut='en_attente',
                paiements__statut='en_attente'
            ).distinct()
        
        elif campagne.type == 'rappel':
            # Réservations confirmées, avec date de départ non nulle et complètement payées
            reservations = Reservation.objects.filter(
                date_depart__isnull=False
            )
            return [r for r in reservations if r.est_payee()]
        elif campagne.type == 'avis':
            # Réservations terminées (date de retour passée)
            return Reservation.objects.filter(
                statut='confirmee',
                voyage__date_retour__lt=timezone.now()
            )
            
        elif campagne.type == 'fidelite':
            # Clients avec plusieurs réservations
            return Reservation.objects.filter(
                statut='confirmee'
            ).values('utilisateur').annotate(
                total=Count('id')
            ).filter(total__gte=3).distinct()
            
        else:  # promotion
            # Tous les clients actifs
            return Reservation.objects.filter(
                statut='confirmee'
            ).distinct('utilisateur')
            
    except Exception as e:
        logger.error(f"Erreur récupération destinataires: {str(e)}")
        return Reservation.objects.none()

def preparer_contenu_email(modele, context):
    try:
        # Rendre d'abord le contenu brut comme un template Django
        template = Template(modele.contenu)
        html_content = template.render(Context(context))
        
        # Utiliser ce rendu dans ton template global
        final_html = render_to_string(
            'emails/campagne_template.html',
            {'contenu': html_content}
        )
        
        # Version texte brut à partir du contenu rendu
        text_content = strip_tags(html_content)
        
        return final_html, text_content
    except Exception as e:
        logger.error(f"Erreur génération contenu email: {str(e)}")
        raise

def envoyer_emails_campagne(destinataire, campagne):
    """
    Envoie un email individuel pour une campagne
    """
    try:
        # Préparation du contexte
        context = {
        'username': destinataire.utilisateur.username,
        'email': destinataire.utilisateur.email,
        'destination': destinataire.voyage.destination,
        'date_depart': destinataire.date_depart.strftime('%d/%m/%Y à %H:%M') if destinataire.date_depart else '',
        'nombre_adultes': destinataire.nombre_adultes,
        'nombre_enfants': destinataire.nombre_enfants,
        'responsable_phone': destinataire.voyage.responsable.phone_number if hasattr(destinataire.voyage, 'responsable') else '',
    }

        
        # Préparation du contenu
        html_content, text_content = preparer_contenu_email(
            campagne.modele, 
            context
        )
        
        # Création de l'email
        email = EmailMultiAlternatives(
            subject=campagne.modele.sujet.format(**context),
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinataire.utilisateur.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Envoi de l'email
        email.send()
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur envoi email à {destinataire.utilisateur.email}: {str(e)}")
        return False

def envoyer_campagne(campagne):
    """
    Fonction principale pour envoyer une campagne
    """
    try:
        if campagne.statut != 'active':
            logger.warning(f"Campagne {campagne.id} non active - annulation")
            return False
            
        logger.info(campagne.statut)
        destinataires = get_destinataires_campagne(campagne)
        total_envoyes = 0
        
        logger.info(f"Début envoi campagne {campagne.id} à {len(destinataires)} destinataires")

        
        for destinataire in destinataires:
            if envoyer_emails_campagne(destinataire, campagne):
                total_envoyes += 1
                
            # Petit sleep pour éviter de surcharger le serveur SMTP
            time.sleep(0.1)
        
        # Mise à jour des stats de la campagne
        Campagne.objects.filter(pk=campagne.id).update(
            destinataires=total_envoyes,
            date_derniere_execution=timezone.now(),
            date_prochaine_execution=calculer_prochaine_execution(campagne)
        )
        
        logger.info(f"Campagne {campagne.id} envoyée à {total_envoyes}/{len(destinataires)} destinataires")
        return True
        
    except Exception as e:
        logger.error(f"Erreur majeure dans l'envoi de campagne {campagne.id}: {str(e)}")
        return False

def calculer_prochaine_execution(campagne):
    """
    Calcule la prochaine date d'exécution selon le type de campagne
    """
    if campagne.type == 'promotion' and campagne.date_prochaine_execution:
        return campagne.date_prochaine_execution
        
    if campagne.delai:
        return timezone.now() + timezone.timedelta(hours=campagne.delai)
        
    return None