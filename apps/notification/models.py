import uuid
from django.conf import settings
from django.db import models


class NotificationTemplate(models.Model):
    CHANNEL_EMAIL = 'EMAIL'
    CHANNEL_IN_APP = 'IN_APP'
    CHANNEL_SMS = 'SMS'

    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, 'Email'),
        (CHANNEL_IN_APP, 'In-App'),
        (CHANNEL_SMS, 'SMS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    subject = models.CharField(max_length=500, blank=True)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notif_template'
        unique_together = ['code', 'channel']
        ordering = ['code']

    def __str__(self):
        return f"[{self.channel}] {self.code}"


class Notification(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_SENT = 'SENT'
    STATUS_FAILED = 'FAILED'
    STATUS_READ = 'READ'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_READ, 'Read'),
    ]

    CHANNEL_EMAIL = 'EMAIL'
    CHANNEL_IN_APP = 'IN_APP'
    CHANNEL_SMS = 'SMS'

    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, 'Email'),
        (CHANNEL_IN_APP, 'In-App'),
        (CHANNEL_SMS, 'SMS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    template = models.ForeignKey(
        NotificationTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name='notifications'
    )
    reference_type = models.CharField(max_length=100, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notif_notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.channel}] → {self.recipient} ({self.status})"


class NotificationPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preference'
    )
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    workflow_notifications = models.BooleanField(default=True)
    leave_notifications = models.BooleanField(default=True)
    performance_notifications = models.BooleanField(default=True)
    learning_notifications = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notif_preference'

    def __str__(self):
        return f"Preferences for {self.user}"
