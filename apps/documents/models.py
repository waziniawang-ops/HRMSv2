import uuid
from django.conf import settings
from django.db import models


class DocCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_confidential = models.BooleanField(default=False)
    retention_years = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'doc_category'
        ordering = ['name']

    def __str__(self):
        return self.name


class DocTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(DocCategory, on_delete=models.PROTECT, related_name='templates')
    description = models.TextField(blank=True)
    template_file = models.FileField(upload_to='documents/templates/', null=True, blank=True)
    variables = models.JSONField(default=list, blank=True)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='doc_templates_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doc_template'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name} v{self.version}"


class DocRecord(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUPERSEDED = 'SUPERSEDED'
    STATUS_ARCHIVED = 'ARCHIVED'
    STATUS_EXPIRED = 'EXPIRED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUPERSEDED, 'Superseded'),
        (STATUS_ARCHIVED, 'Archived'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    category = models.ForeignKey(DocCategory, on_delete=models.PROTECT, related_name='records')
    employee = models.ForeignKey(
        'core_hr.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='documents'
    )
    template = models.ForeignKey(
        DocTemplate, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='generated_records'
    )
    file = models.FileField(upload_to='documents/records/')
    file_size = models.PositiveIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    expiry_date = models.DateField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_confidential = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='doc_records_uploaded'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doc_record'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.title} [{self.status}]"


class DocPolicy(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_PUBLISHED = 'PUBLISHED'
    STATUS_SUPERSEDED = 'SUPERSEDED'
    STATUS_ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_SUPERSEDED, 'Superseded'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(DocCategory, on_delete=models.PROTECT, related_name='policies')
    content = models.TextField()
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    requires_acknowledgement = models.BooleanField(default=False)
    acknowledgement_deadline = models.DateField(null=True, blank=True)
    document_file = models.FileField(upload_to='documents/policies/', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='doc_policies_created'
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='doc_policies_published'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doc_policy'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'effective_date']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} v{self.version} [{self.status}]"


class DocAcknowledgement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(DocPolicy, on_delete=models.PROTECT, related_name='acknowledgements')
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='policy_acknowledgements'
    )
    version_acknowledged = models.CharField(max_length=20)
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    digital_signature = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'doc_acknowledgement'
        unique_together = [['policy', 'employee', 'version_acknowledged']]

    def __str__(self):
        return f"{self.employee} acknowledged {self.policy.code} v{self.version_acknowledged}"


class RetentionRule(models.Model):
    DISPOSAL_PERMANENT_DELETE = 'PERMANENT_DELETE'
    DISPOSAL_ARCHIVE = 'ARCHIVE'
    DISPOSAL_REVIEW = 'REVIEW_BEFORE_DELETE'

    DISPOSAL_CHOICES = [
        (DISPOSAL_PERMANENT_DELETE, 'Permanent Delete'),
        (DISPOSAL_ARCHIVE, 'Archive'),
        (DISPOSAL_REVIEW, 'Review Before Delete'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        DocCategory, on_delete=models.CASCADE, related_name='retention_rules'
    )
    retention_years = models.PositiveIntegerField()
    disposal_action = models.CharField(max_length=30, choices=DISPOSAL_CHOICES)
    legal_hold_applicable = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'doc_retention_rule'

    def __str__(self):
        return f"{self.category.name} — retain {self.retention_years}y then {self.disposal_action}"
