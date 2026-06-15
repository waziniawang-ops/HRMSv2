import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class WorkflowRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_code = models.CharField(max_length=100, unique=True)
    module_code = models.CharField(max_length=50)
    applies_to = models.CharField(max_length=100, help_text="e.g. recruitment.job_posting")
    description = models.TextField(blank=True)
    conditions = models.JSONField(default=dict, blank=True)
    steps = models.JSONField(
        default=list,
        help_text='[{"step": 1, "role": "HR_CHECKER", "sla_hours": 24}, ...]'
    )
    segregation_of_duties = models.BooleanField(default=True)
    maker_cannot_approve = models.BooleanField(default=True)
    audit_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    effective_from = models.DateField(default=timezone.localdate)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_rule'
        ordering = ['module_code', 'workflow_code']

    def __str__(self):
        return f"{self.workflow_code} v{self.version}"


class WorkflowRequest(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_RETURNED = 'RETURNED'
    STATUS_RESUBMITTED = 'RESUBMITTED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_ACTIVE = 'ACTIVE'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_IN_REVIEW, 'In Review'),
        (STATUS_RETURNED, 'Returned for Amendment'),
        (STATUS_RESUBMITTED, 'Resubmitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_ACTIVE, 'Active'),
    ]

    TERMINAL_STATUSES = [STATUS_APPROVED, STATUS_REJECTED, STATUS_CANCELLED]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_rule = models.ForeignKey(
        WorkflowRule, on_delete=models.PROTECT, related_name='requests'
    )
    module_code = models.CharField(max_length=50)
    object_type = models.CharField(max_length=100)
    object_id = models.UUIDField()
    maker_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='workflow_requests_made'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    current_step = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_request'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['module_code', 'object_type', 'object_id']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['maker_user', '-created_at']),
        ]

    def __str__(self):
        return f"WF-{str(self.id)[:8]} [{self.status}] {self.object_type}"

    @property
    def is_terminal(self):
        return self.status in self.TERMINAL_STATUSES

    @property
    def pending_step(self):
        return self.steps.filter(status='PENDING').order_by('step_number').first()


class WorkflowStep(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_RETURNED = 'RETURNED'
    STATUS_SKIPPED = 'SKIPPED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_REVIEW, 'In Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_RETURNED, 'Returned'),
        (STATUS_SKIPPED, 'Skipped'),
    ]

    ACTION_APPROVE = 'APPROVE'
    ACTION_REJECT = 'REJECT'
    ACTION_RETURN = 'RETURN'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_request = models.ForeignKey(
        WorkflowRequest, on_delete=models.CASCADE, related_name='steps'
    )
    step_number = models.PositiveIntegerField()
    approver_role = models.CharField(max_length=50)
    approver_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_steps_to_approve'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    action = models.CharField(max_length=20, blank=True)
    comment = models.TextField(blank=True)
    sla_hours = models.PositiveIntegerField(null=True, blank=True)
    acted_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workflow_step'
        ordering = ['step_number']
        unique_together = [['workflow_request', 'step_number']]

    def __str__(self):
        return f"Step {self.step_number} ({self.approver_role}) [{self.status}]"


class WorkflowComment(models.Model):
    VISIBILITY_ALL = 'ALL'
    VISIBILITY_INTERNAL = 'INTERNAL'

    VISIBILITY_CHOICES = [
        (VISIBILITY_ALL, 'All Parties'),
        (VISIBILITY_INTERNAL, 'Internal Only'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_request = models.ForeignKey(
        WorkflowRequest, on_delete=models.CASCADE, related_name='comments'
    )
    step = models.ForeignKey(
        WorkflowStep, null=True, blank=True, on_delete=models.SET_NULL
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment = models.TextField()
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_ALL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workflow_comment'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.workflow_request}"


class WorkflowHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_request = models.ForeignKey(
        WorkflowRequest, on_delete=models.CASCADE, related_name='history'
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    step_number = models.PositiveIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    before_snapshot = models.JSONField(null=True, blank=True)
    after_snapshot = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workflow_history'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.from_status} → {self.to_status} by {self.actor}"
