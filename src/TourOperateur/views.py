from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Voyage

@csrf_exempt
def voyages_disponibles(request):
    voyages = Voyage.objects.all().order_by('-date_depart')  # Trie par date de départ (les plus récents en premier)
    data = [
        {
            "id": v.id,
            "nom": v.nom,
            "ville_depart": v.ville_depart,
            "ville_arrive": v.ville_arrive,
            "date_depart": v.date_depart.strftime("%d-%m-%Y %H:%M"),
            "date_arrive_prevu": v.date_arrive_prevu.strftime("%d-%m-%Y %H:%M"),
            "prix": float(v.prix),
            "places_disponibles": v.place,
        }
        for v in voyages
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
def voyages_populaires(request):
    voyages = Voyage.voyages_populaires()
    data = [
        {
            "nom": v.nom,
            "ville_depart": v.ville_depart,
            "ville_arrive": v.ville_arrive,
            "prix": float(v.prix),
            "moyenne_notes": v.moyenne_notes(),
        }
        for v in voyages
    ]
    return JsonResponse(data, safe=False)
