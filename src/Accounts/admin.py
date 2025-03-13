from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'user_type', 'is_verified', 'registration_date')
    list_filter = ('user_type', 'is_verified', 'registration_date')
    search_fields = ('email', 'username', 'phone_number', 'city', 'country')
    ordering = ('-registration_date',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('username', 'gender', 'nationality', 'age', 'profile_picture', 'city', 'country', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Statut de vérification', {'fields': ('is_verified', 'verification_code')}),
        ('Autres informations', {'fields': ('user_type', 'registration_date')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'user_type'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """ Permet de modifier tous les champs sauf la date d'inscription """
        if obj:  # Modification d'un utilisateur existant
            return ('registration_date',)
        return ()  # Création d'un utilisateur, aucun champ en lecture seule

admin.site.register(CustomUser, CustomUserAdmin)
