# images/admin.py
from django.contrib import admin
from .models import ImagePost

@admin.register(ImagePost)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'created', 'updated']
    list_filter = ['created', 'uploaded_by']
    search_fields = ['title', 'description']