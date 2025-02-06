from django.contrib import admin
from .models import TypesTransport, AgenceVoyage, Voyage, AvisVoyage

@admin.register(TypesTransport)
class TypesTransportAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom')
    search_fields = ('nom',)

@admin.register(AgenceVoyage)
class AgenceVoyageAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'adresse', 'nif', 'stat', 'mail', 'responsable')
    search_fields = ('nom', 'mail', 'responsable__username')  # Recherche aussi par le nom du responsable
    list_filter = ('nom', 'responsable')

@admin.register(Voyage)
class VoyageAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'ville_depart', 'ville_arrive', 'date_depart', 'date_arrive_prevu', 'prix', 'place', 'agence', 'moyenne_notes', 'nombre_avis')
    search_fields = ('nom', 'ville_depart', 'ville_arrive')
    list_filter = ('ville_depart', 'ville_arrive', 'date_depart', 'agence')
    date_hierarchy = 'date_depart'
    filter_horizontal = ("types_transport",)
    readonly_fields = ('moyenne_notes', 'nombre_avis')

    def nombre_avis(self, obj):
        return obj.avis.count()
    nombre_avis.short_description = "Nombre d'avis"

    def moyenne_notes(self, obj):
        return obj.moyenne_notes()
    moyenne_notes.short_description = "Note Moyenne"

@admin.register(AvisVoyage)
class AvisVoyageAdmin(admin.ModelAdmin):
    list_display = ('voyage', 'utilisateur', 'note', 'date_ajout')
    list_filter = ('note', 'date_ajout')
    search_fields = ('voyage__nom', 'utilisateur__username')
