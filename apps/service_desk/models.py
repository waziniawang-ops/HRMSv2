import uuid
from django.conf import settings
from django.db import models


class TicketCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories'
    )
    sla_hours = models.PositiveIntegerField(default=24)
    is_confidential = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sdesk_ticket_category'
        ordering = ['name']

    def __str__(self):
        return self.name


class HRTicket(models.Model):
    STATUS_OPEN = 'OPEN'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_PENDING_INFO = 'PENDING_INFO'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PENDING_INFO, 'Pending Info'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_URGENT = 'URGENT'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=30, unique=True, blank=True)
    category = models.ForeignKey(
        TicketCategory, on_delete=models.PROTECT, related_name='tickets'
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='tickets_raised'
    )
    on_behalf_of = models.ForeignKey(
        'core_hr.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tickets_on_behalf'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tickets_assigned'
    )
    due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    satisfaction_score = models.PositiveIntegerField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sdesk_hr_ticket'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.ticket_number} — {self.subject} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            from django.utils import timezone
            year = timezone.now().year
            last = HRTicket.objects.filter(created_at__year=year).order_by('-ticket_number').first()
            if last and last.ticket_number:
                try:
                    seq = int(last.ticket_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.ticket_number = f"HD-{year}-{seq:05d}"
        super().save(*args, **kwargs)


class TicketComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(HRTicket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ticket_comments'
    )
    content = models.TextField()
    is_internal = models.BooleanField(default=False)
    attachment = models.FileField(null=True, blank=True, upload_to='service_desk/attachments/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sdesk_ticket_comment'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket.ticket_number}"


class KnowledgeCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sdesk_knowledge_category'
        ordering = ['name']

    def __str__(self):
        return self.name


class KnowledgeArticle(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'
    STATUS_ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        KnowledgeCategory, on_delete=models.PROTECT, related_name='articles'
    )
    title = models.CharField(max_length=500)
    slug = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    helpful_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='knowledge_articles'
    )
    views_count = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sdesk_knowledge_article'
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class SatisfactionSurvey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(HRTicket, on_delete=models.CASCADE, related_name='satisfaction_surveys')
    score = models.PositiveIntegerField()
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sdesk_satisfaction_survey'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Survey for {self.ticket.ticket_number} — score {self.score}"
