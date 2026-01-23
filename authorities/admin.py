from django.contrib import admin
from .models import Authority, AuthorityZone


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'created_at']
    search_fields = ['name', 'contact_email']
    filter_horizontal = ['authorized_users']


@admin.register(AuthorityZone)
class AuthorityZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'authority', 'created_at']
    list_filter = ['authority', 'created_at']
    search_fields = ['name', 'authority__name']
