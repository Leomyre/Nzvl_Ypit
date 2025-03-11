from django.contrib import admin
from .models import TypesTransport, AgenceVoyage, Trajet, Voyage, AvisVoyage, ReservationVoyage, InteractionVoyage

# Enregistrer TypesTransport
@admin.register(TypesTransport)
class TypesTransportAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

# Enregistrer AgenceVoyage
@admin.register(AgenceVoyage)
class AgenceVoyageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'adresse', 'nif', 'stat', 'mail', 'responsable')
    search_fields = ('nom', 'mail', 'responsable__user__username')
    list_filter = ('responsable',)

# Enregistrer Trajet
@admin.register(Trajet)
class TrajetAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'ville_depart', 'date_depart', 'ville_arrive', 'date_arrive_prevu')
    search_fields = ('voyage__nom', 'ville_depart', 'ville_arrive')

# Enregistrer Voyage
@admin.register(Voyage)
class VoyageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'place', 'agence')
    search_fields = ('nom', 'agence__nom')
    list_filter = ('agence',)

# Enregistrer AvisVoyage
@admin.register(AvisVoyage)
class AvisVoyageAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'utilisateur', 'note', 'date_ajout')
    search_fields = ('voyage__nom', 'utilisateur__username')
    list_filter = ('note',)

# Enregistrer ReservationVoyage
@admin.register(ReservationVoyage)
class ReservationVoyageAdmin(admin.ModelAdmin):
    list_display = ('client', 'voyage', 'date_reservation')
    search_fields = ('client__user__username', 'voyage__nom')
    list_filter = ('date_reservation',)

# Enregistrer InteractionVoyage
@admin.register(InteractionVoyage)
class InteractionVoyageAdmin(admin.ModelAdmin):
    list_display = ('client', 'voyage', 'type_interaction', 'date_interaction')
    search_fields = ('client__user__username', 'voyage__nom')
    list_filter = ('type_interaction',)
