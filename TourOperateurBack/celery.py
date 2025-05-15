import os
from celery import Celery

# Définit le fichier de configuration Django par défaut pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TourOperateurBack.settings')

# Initialise l'application Celery
app = Celery('TourOperateurBack')

# Charge les configurations depuis les settings Django (avec préfixe CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches dans toutes les apps Django (fichiers tasks.py)
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
