import uuid
from django.conf import settings
from django.db import models


class ESSRequestType(models.Model):
    CATEGORY_PROFILE_UPDATE = 'PROFILE_UPDATE'
    CATEGORY_DOCUMENT_REQUEST = 'DOCUMENT_REQUEST'
    CATEGORY_LEAVE = 'LEAVE'
    CATEGORY_CLAIM = 'CLAIM'
    CATEGORY_TRAINING = 'TRAINING'
    CATEGORY_IT_ACCESS = 'IT_ACCESS'
    CATEGORY_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CATEGORY_PROFILE_UPDATE, 'Profile Update'),
        (CATEGORY_DOCUMENT_REQUEST, 'Document Request'),
        (CATEGORY_LEAVE, 'Leave'),
        (CATEGORY_CLAIM, 'Claim'),
        (CATEGORY_TRAINING, 'Training'),
        (CATEGORY_IT_ACCESS, 'IT Access'),
        (CATEGORY_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER)
    requires_approval = models.BooleanField(default=True)
    workflow_code = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ess_request_type'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ESSRequest(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_IN_REVIEW, 'In Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='ess_requests'
    )
    request_type = models.ForeignKey(
        ESSRequestType, on_delete=models.PROTECT, related_name='requests'
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    attachments = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='ess_resolved'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ess_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} — {self.subject} [{self.status}]"


class ProfileChangeRequest(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='profile_change_requests'
    )
    field_name = models.CharField(max_length=100)
    field_label = models.CharField(max_length=255, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField()
    reason = models.TextField(blank=True)
    evidence_document = models.FileField(
        null=True, blank=True, upload_to='ess/profile_changes/'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='profile_changes_reviewed'
    )
    review_notes = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ess_profile_change_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} — change {self.field_name} [{self.status}]"



class ManagerDelegation(models.Model):
    TYPE_LEAVE_APPROVAL = 'LEAVE_APPROVAL'
    TYPE_ALL_APPROVALS = 'ALL_APPROVALS'
    TYPE_SPECIFIC_WORKFLOW = 'SPECIFIC_WORKFLOW'

    TYPE_CHOICES = [
        (TYPE_LEAVE_APPROVAL, 'Leave Approval'),
        (TYPE_ALL_APPROVALS, 'All Approvals'),
        (TYPE_SPECIFIC_WORKFLOW, 'Specific Workflow'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delegator = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='delegations_given'
    )
    delegate = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='delegations_received'
    )
    delegation_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    workflow_code = models.CharField(max_length=100, blank=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='delegations_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ess_manager_delegation'
        ordering = ['-valid_from']

    def __str__(self):
        return f"{self.delegator} → {self.delegate} ({self.delegation_type})"
