import uuid
from django.conf import settings
from django.db import models


class OnboardingTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tasks = models.JSONField(
        default=list,
        help_text='[{"task_code": "PERSONAL_INFO", "title": "...", "required": true, "order": 1}]'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'onb_template'
        ordering = ['name']

    def __str__(self):
        return self.name


class OnboardingCase(models.Model):
    STATUS_STARTED = 'STARTED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_PENDING_HR = 'PENDING_HR'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_WAIVED = 'WAIVED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_STARTED, 'Started'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PENDING_HR, 'Pending HR Review'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_WAIVED, 'Waived'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.OneToOneField(
        'recruitment.Offer', on_delete=models.PROTECT, related_name='onboarding_case'
    )
    candidate_person = models.ForeignKey(
        'core_hr.Person', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='onboarding_cases'
    )
    template = models.ForeignKey(
        OnboardingTemplate, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='cases'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_STARTED)
    target_start_date = models.DateField()
    assigned_hr = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='onboarding_cases_managed'
    )
    hr_verified_at = models.DateTimeField(null=True, blank=True)
    hr_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='onboarding_cases_verified'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'onb_case'
        ordering = ['-created_at']

    def __str__(self):
        return f"Onboarding for {self.offer.application.applicant.full_name} [{self.status}]"

    @property
    def completion_percentage(self):
        tasks = self.tasks.all()
        if not tasks.exists():
            return 0
        completed = tasks.filter(status=OnboardingTask.STATUS_COMPLETED).count()
        return int((completed / tasks.count()) * 100)


class OnboardingTask(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_WAIVED = 'WAIVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_WAIVED, 'Waived'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    TASK_PERSONAL_INFO = 'PERSONAL_INFO'
    TASK_RESUME = 'RESUME'
    TASK_ACADEMIC_CERTS = 'ACADEMIC_CERTS'
    TASK_PROFESSIONAL_CERTS = 'PROFESSIONAL_CERTS'
    TASK_BANK_DETAILS = 'BANK_DETAILS'
    TASK_EMERGENCY_CONTACT = 'EMERGENCY_CONTACT'
    TASK_CONTRACT_SIGNING = 'CONTRACT_SIGNING'
    TASK_ACCESS_REQUEST = 'ACCESS_REQUEST'
    TASK_PAYROLL_SETUP = 'PAYROLL_SETUP'
    TASK_CUSTOM = 'CUSTOM'

    TASK_CHOICES = [
        (TASK_PERSONAL_INFO, 'Personal Information Verification'),
        (TASK_RESUME, 'Resume Verification'),
        (TASK_ACADEMIC_CERTS, 'Academic Certificates'),
        (TASK_PROFESSIONAL_CERTS, 'Professional Certifications'),
        (TASK_BANK_DETAILS, 'Bank Account Details'),
        (TASK_EMERGENCY_CONTACT, 'Emergency Contact'),
        (TASK_CONTRACT_SIGNING, 'Employment Contract Signing'),
        (TASK_ACCESS_REQUEST, 'Access Provisioning Request'),
        (TASK_PAYROLL_SETUP, 'Payroll Setup'),
        (TASK_CUSTOM, 'Custom Task'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    onboarding_case = models.ForeignKey(OnboardingCase, on_delete=models.CASCADE, related_name='tasks')
    task_code = models.CharField(max_length=30, choices=TASK_CHOICES, default=TASK_CUSTOM)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='onboarding_tasks_completed'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    hr_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'onb_task'
        ordering = ['order', 'task_code']

    def __str__(self):
        return f"{self.title} [{self.status}]"


class OnboardingDocument(models.Model):
    TYPE_RESUME = 'RESUME'
    TYPE_ID_COPY = 'ID_COPY'
    TYPE_ACADEMIC = 'ACADEMIC'
    TYPE_PROFESSIONAL = 'PROFESSIONAL'
    TYPE_BANK = 'BANK'
    TYPE_CONTRACT = 'CONTRACT'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_RESUME, 'Resume'),
        (TYPE_ID_COPY, 'ID Copy'),
        (TYPE_ACADEMIC, 'Academic Certificate'),
        (TYPE_PROFESSIONAL, 'Professional Certification'),
        (TYPE_BANK, 'Bank Details'),
        (TYPE_CONTRACT, 'Employment Contract'),
        (TYPE_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    onboarding_case = models.ForeignKey(OnboardingCase, on_delete=models.CASCADE, related_name='documents')
    task = models.ForeignKey(
        OnboardingTask, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='documents'
    )
    document_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='onboarding/documents/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='uploaded_onboarding_docs'
    )
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='verified_onboarding_docs'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'onb_document'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} ({self.document_type})"
