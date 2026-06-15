from django.contrib import admin
from .models import Notification, NotificationTemplate, NotificationPreference


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'channel', 'is_active']
    list_filter = ['channel', 'is_active']
    search_fields = ['code', 'name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'channel', 'subject', 'status', 'sent_at', 'read_at', 'created_at']
    list_filter = ['channel', 'status']
    search_fields = ['recipient__username', 'subject']
    raw_id_fields = ['recipient', 'template']
    readonly_fields = ['sent_at', 'read_at', 'created_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_enabled', 'in_app_enabled', 'sms_enabled']
    raw_id_fields = ['user']
