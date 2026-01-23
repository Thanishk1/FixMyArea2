from django.contrib import admin
from .models import IssueCategory, Issue, IssueUpdate


@admin.register(IssueCategory)
class IssueCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'description']
    search_fields = ['name']


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'reporter', 'assigned_authority', 'status', 'created_at']
    list_filter = ['status', 'category', 'assigned_authority', 'created_at']
    search_fields = ['title', 'description', 'location_text']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(IssueUpdate)
class IssueUpdateAdmin(admin.ModelAdmin):
    list_display = ['issue', 'author', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['issue__title', 'notes']
