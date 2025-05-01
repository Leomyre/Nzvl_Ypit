from django.contrib import admin
from .models import User, Profile, TourOperatorInfo

@admin.register(TourOperatorInfo)
class TourOperatorInfoAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'company_email', 'website')
    search_fields = ('company_name', 'user__email')

admin.site.register(User)
admin.site.register(Profile)
