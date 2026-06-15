from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor_display', 'action', 'object_type', 'object_id',
            'module', 'ip_address', 'correlation_id',
            'before_json', 'after_json',
            'created_at',
        ]

    def get_actor_display(self, obj):
        if obj.actor_user:
            return obj.actor_user.get_full_name() or obj.actor_user.username
        return 'System'
