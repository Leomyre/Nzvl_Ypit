from django.contrib import admin
from .models import User, Client, Responsable, Admin

# Personnalisation de l'affichage du modèle User dans l'admin
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('user_type', 'is_active')
    ordering = ('-date_joined',)

# Personnalisation de l'affichage du modèle Client dans l'admin
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'phone_number')
    search_fields = ('user__username', 'address', 'phone_number')

# Personnalisation de l'affichage du modèle Responsable dans l'admin
class ResponsableAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'department')

# Personnalisation de l'affichage du modèle Admin dans l'admin
class AdminAdmin(admin.ModelAdmin):
    list_display = ('user', 'privileges')
    search_fields = ('user__username', 'privileges')

# Enregistrer les modèles dans l'admin
admin.site.register(User, UserAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Responsable, ResponsableAdmin)
admin.site.register(Admin, AdminAdmin)
