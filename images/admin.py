from django.contrib import admin

from .forms import ImagePostForm
from .models import ImagePost

@admin.register(ImagePost)
class ImageAdmin(admin.ModelAdmin):
    form = ImagePostForm
    list_display = ["title", "uploaded_by", "created", "updated"]
    list_filter = ["created", "uploaded_by"]
    search_fields = ["title", "description"]
