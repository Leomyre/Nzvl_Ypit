from celery import shared_task
from .models import Campagne
from .services import envoyer_campagne

@shared_task(bind=True, max_retries=3)
def envoyer_campagne_immediatement(self, campagne_id):
    try:
        campagne = Campagne.objects.get(pk=campagne_id)
        if campagne.statut == 'active':
            envoyer_campagne(campagne)
    except Campagne.DoesNotExist:
        print(f"Campagne {campagne_id} non trouvée")
