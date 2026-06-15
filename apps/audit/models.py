import uuid
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    ACTION_LOGIN_FAILURE = 'LOGIN_FAILURE'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_REGISTER = 'REGISTER'
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_APPROVE = 'APPROVE'
    ACTION_REJECT = 'REJECT'
    ACTION_RETURN = 'RETURN'
    ACTION_SUBMIT = 'SUBMIT'
    ACTION_PUBLISH = 'PUBLISH'
    ACTION_EXPORT = 'EXPORT'
    ACTION_DOCUMENT_DOWNLOAD = 'DOCUMENT_DOWNLOAD'
    ACTION_ROLE_CHANGED = 'ROLE_CHANGED'
    ACTION_BREAK_GLASS = 'BREAK_GLASS_USED'
    ACTION_PASSWORD_CHANGED = 'PASSWORD_CHANGED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255, blank=True)
    before_json = models.JSONField(null=True, blank=True)
    after_json = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    correlation_id = models.CharField(max_length=100, blank=True)
    module = models.CharField(max_length=50, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['object_type', 'object_id', '-created_at']),
            models.Index(fields=['actor_user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.action} on {self.object_type}:{self.object_id} by {self.actor_user}"

    def save(self, *args, **kwargs):
        if not self._state.adding and getattr(settings, 'AUDIT_IMMUTABLE_MODE', True):
            raise PermissionError("Audit logs are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit logs cannot be deleted.")
