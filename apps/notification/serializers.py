from rest_framework import serializers
from .models import Notification, NotificationTemplate, NotificationPreference


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ['id', 'code', 'name', 'channel', 'subject', 'body_template', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'channel', 'subject', 'body', 'status',
            'reference_type', 'reference_id', 'sent_at', 'read_at', 'created_at',
        ]
        read_only_fields = ['id', 'recipient', 'status', 'sent_at', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'email_enabled', 'in_app_enabled', 'sms_enabled',
            'workflow_notifications', 'leave_notifications',
            'performance_notifications', 'learning_notifications', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'updated_at']
