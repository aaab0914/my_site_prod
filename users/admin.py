from django.contrib import admin

from .models import Profile, UserActivity, UserPreference

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'location', 'birth_date']
    search_fields = ['user__username']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'action']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'email_notifications', 'push_notifications']
    list_filter = ['theme', 'email_notifications']
    search_fields = ['user__username']