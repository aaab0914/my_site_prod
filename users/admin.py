from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from .models import Profile, UserActivity, UserPreference


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "is_staff", "is_superuser", "is_active", "last_login", "date_joined"]
    list_filter = ["is_staff", "is_superuser", "is_active", "groups", "date_joined", "last_login"]
    search_fields = ["username", "email", "first_name", "last_name"]
    list_editable = ["is_active"]
    ordering = ["-date_joined"]
    list_per_page = 50
    actions = ["activate_users", "deactivate_users"]

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)


try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ["key_preview", "user", "created"]
    list_filter = ["created"]
    search_fields = ["key", "user__username", "user__email"]
    autocomplete_fields = ["user"]
    readonly_fields = ["key", "created"]
    ordering = ["-created"]
    list_per_page = 50
    date_hierarchy = "created"

    @admin.display(description="Key")
    def key_preview(self, obj):
        return f"{obj.key[:8]}...{obj.key[-6:]}"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "location", "birth_date", "last_avatar_change"]
    list_filter = ["location", "birth_date", "last_avatar_change"]
    search_fields = ["user__username", "user__email", "bio", "location"]
    autocomplete_fields = ["user"]
    list_per_page = 50

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "ip_address", "timestamp"]
    list_filter = ["action", "timestamp"]
    search_fields = ["user__username", "user__email", "action", "ip_address"]
    autocomplete_fields = ["user"]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]
    list_per_page = 50

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "theme", "email_notifications", "push_notifications"]
    list_filter = ["theme", "email_notifications", "push_notifications"]
    search_fields = ["user__username", "user__email"]
    list_editable = ["email_notifications", "push_notifications"]
    autocomplete_fields = ["user"]
    list_per_page = 50
