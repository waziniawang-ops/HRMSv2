import uuid
from django.conf import settings
from django.db import models


class OffboardingCase(models.Model):
    STATUS_INITIATED = 'INITIATED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_CLEARANCE_PENDING = 'CLEARANCE_PENDING'
    STATUS_PENDING_SETTLEMENT = 'PENDING_SETTLEMENT'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Initiated'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_CLEARANCE_PENDING, 'Clearance Pending'),
        (STATUS_PENDING_SETTLEMENT, 'Pending Settlement'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    SETTLEMENT_NOT_APPLICABLE = 'NOT_APPLICABLE'
    SETTLEMENT_PENDING = 'PENDING'
    SETTLEMENT_PROCESSING = 'PROCESSING'
    SETTLEMENT_PAID = 'PAID'

    SETTLEMENT_STATUS_CHOICES = [
        (SETTLEMENT_NOT_APPLICABLE, 'Not Applicable'),
        (SETTLEMENT_PENDING, 'Pending'),
        (SETTLEMENT_PROCESSING, 'Processing'),
        (SETTLEMENT_PAID, 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='offboarding_case'
    )
    separation = models.ForeignKey(
        'workforce.Separation', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='offboarding_case'
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_INITIATED)
    notice_period_days = models.PositiveIntegerField(default=0)
    last_working_date = models.DateField(null=True, blank=True)
    exit_interview_scheduled_date = models.DateField(null=True, blank=True)
    knowledge_handover_due = models.DateField(null=True, blank=True)
    rehire_eligible = models.BooleanField(default=True)
    rehire_notes = models.TextField(blank=True)
    legal_hold = models.BooleanField(default=False)
    final_settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    settlement_status = models.CharField(
        max_length=20, choices=SETTLEMENT_STATUS_CHOICES, default=SETTLEMENT_PENDING
    )
    settlement_paid_at = models.DateField(null=True, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='offboarding_cases_initiated'
    )
    hr_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='offboarding_cases_owned'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'offboard_case'
        ordering = ['-created_at']

    def __str__(self):
        return f"Offboarding: {self.employee} [{self.status}]"


class ClearanceTask(models.Model):
    TYPE_IT_ACCESS = 'IT_ACCESS'
    TYPE_ASSET_RETURN = 'ASSET_RETURN'
    TYPE_FINANCE_CLEARANCE = 'FINANCE_CLEARANCE'
    TYPE_LIBRARY = 'LIBRARY'
    TYPE_ADMIN = 'ADMIN'
    TYPE_MEDICAL = 'MEDICAL'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_IT_ACCESS, 'IT Access'),
        (TYPE_ASSET_RETURN, 'Asset Return'),
        (TYPE_FINANCE_CLEARANCE, 'Finance Clearance'),
        (TYPE_LIBRARY, 'Library'),
        (TYPE_ADMIN, 'Admin'),
        (TYPE_MEDICAL, 'Medical'),
        (TYPE_OTHER, 'Other'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_WAIVED = 'WAIVED'
    STATUS_BLOCKED = 'BLOCKED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_WAIVED, 'Waived'),
        (STATUS_BLOCKED, 'Blocked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(OffboardingCase, on_delete=models.CASCADE, related_name='clearance_tasks')
    task_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_OTHER)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='clearance_tasks_assigned'
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    completion_notes = models.TextField(blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='clearance_tasks_completed'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offboard_clearance_task'
        ordering = ['due_date']

    def __str__(self):
        return f"{self.task_name} [{self.status}]"


class AssetClearance(models.Model):
    TYPE_LAPTOP = 'LAPTOP'
    TYPE_PHONE = 'PHONE'
    TYPE_TABLET = 'TABLET'
    TYPE_BADGE = 'BADGE'
    TYPE_VEHICLE = 'VEHICLE'
    TYPE_KEYS = 'KEYS'
    TYPE_EQUIPMENT = 'EQUIPMENT'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_LAPTOP, 'Laptop'),
        (TYPE_PHONE, 'Phone'),
        (TYPE_TABLET, 'Tablet'),
        (TYPE_BADGE, 'Badge/Card'),
        (TYPE_VEHICLE, 'Vehicle'),
        (TYPE_KEYS, 'Keys'),
        (TYPE_EQUIPMENT, 'Equipment'),
        (TYPE_OTHER, 'Other'),
    ]

    RETURN_PENDING = 'PENDING'
    RETURN_RETURNED = 'RETURNED'
    RETURN_DAMAGED = 'DAMAGED'
    RETURN_LOST = 'LOST'
    RETURN_NOT_APPLICABLE = 'NOT_APPLICABLE'

    RETURN_STATUS_CHOICES = [
        (RETURN_PENDING, 'Pending'),
        (RETURN_RETURNED, 'Returned'),
        (RETURN_DAMAGED, 'Damaged'),
        (RETURN_LOST, 'Lost'),
        (RETURN_NOT_APPLICABLE, 'Not Applicable'),
    ]

    CONDITION_GOOD = 'GOOD'
    CONDITION_FAIR = 'FAIR'
    CONDITION_DAMAGED = 'DAMAGED'
    CONDITION_UNUSABLE = 'UNUSABLE'

    CONDITION_CHOICES = [
        (CONDITION_GOOD, 'Good'),
        (CONDITION_FAIR, 'Fair'),
        (CONDITION_DAMAGED, 'Damaged'),
        (CONDITION_UNUSABLE, 'Unusable'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(OffboardingCase, on_delete=models.CASCADE, related_name='asset_clearances')
    asset_name = models.CharField(max_length=255)
    asset_code = models.CharField(max_length=100, blank=True)
    asset_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    issued_date = models.DateField(null=True, blank=True)
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default=RETURN_PENDING)
    return_date = models.DateField(null=True, blank=True)
    condition_on_return = models.CharField(max_length=20, choices=CONDITION_CHOICES, null=True, blank=True)
    condition_notes = models.TextField(blank=True)
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cleared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='asset_clearances_done'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offboard_asset_clearance'

    def __str__(self):
        return f"{self.asset_name} ({self.asset_type}) — {self.return_status}"


class AccessRevocation(models.Model):
    TYPE_NETWORK = 'NETWORK'
    TYPE_EMAIL = 'EMAIL'
    TYPE_VPN = 'VPN'
    TYPE_ERP = 'ERP'
    TYPE_PHYSICAL = 'PHYSICAL'
    TYPE_CLOUD = 'CLOUD'
    TYPE_DATABASE = 'DATABASE'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_NETWORK, 'Network'),
        (TYPE_EMAIL, 'Email'),
        (TYPE_VPN, 'VPN'),
        (TYPE_ERP, 'ERP System'),
        (TYPE_PHYSICAL, 'Physical Access'),
        (TYPE_CLOUD, 'Cloud Services'),
        (TYPE_DATABASE, 'Database'),
        (TYPE_OTHER, 'Other'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_REVOKED = 'REVOKED'
    STATUS_FAILED = 'FAILED'
    STATUS_NOT_APPLICABLE = 'NOT_APPLICABLE'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_REVOKED, 'Revoked'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_NOT_APPLICABLE, 'Not Applicable'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(OffboardingCase, on_delete=models.CASCADE, related_name='access_revocations')
    system_name = models.CharField(max_length=255)
    access_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    access_identifier = models.CharField(max_length=255, blank=True)
    scheduled_revocation_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='access_revocations_done'
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offboard_access_revocation'

    def __str__(self):
        return f"{self.system_name} ({self.access_type}) — {self.status}"


class ExitInterview(models.Model):
    FORMAT_IN_PERSON = 'IN_PERSON'
    FORMAT_VIDEO = 'VIDEO'
    FORMAT_WRITTEN = 'WRITTEN'
    FORMAT_PHONE = 'PHONE'

    FORMAT_CHOICES = [
        (FORMAT_IN_PERSON, 'In Person'),
        (FORMAT_VIDEO, 'Video Call'),
        (FORMAT_WRITTEN, 'Written'),
        (FORMAT_PHONE, 'Phone'),
    ]

    EXPERIENCE_EXCELLENT = 'EXCELLENT'
    EXPERIENCE_GOOD = 'GOOD'
    EXPERIENCE_NEUTRAL = 'NEUTRAL'
    EXPERIENCE_POOR = 'POOR'
    EXPERIENCE_VERY_POOR = 'VERY_POOR'

    EXPERIENCE_CHOICES = [
        (EXPERIENCE_EXCELLENT, 'Excellent'),
        (EXPERIENCE_GOOD, 'Good'),
        (EXPERIENCE_NEUTRAL, 'Neutral'),
        (EXPERIENCE_POOR, 'Poor'),
        (EXPERIENCE_VERY_POOR, 'Very Poor'),
    ]

    SENTIMENT_POSITIVE = 'POSITIVE'
    SENTIMENT_NEUTRAL = 'NEUTRAL'
    SENTIMENT_NEGATIVE = 'NEGATIVE'

    SENTIMENT_CHOICES = [
        (SENTIMENT_POSITIVE, 'Positive'),
        (SENTIMENT_NEUTRAL, 'Neutral'),
        (SENTIMENT_NEGATIVE, 'Negative'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(OffboardingCase, on_delete=models.CASCADE, related_name='exit_interviews')
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='exit_interviews_conducted'
    )
    interview_date = models.DateField()
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    reason_for_leaving = models.TextField(blank=True)
    overall_experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, null=True, blank=True)
    would_return = models.BooleanField(null=True, blank=True)
    would_recommend = models.BooleanField(null=True, blank=True)
    responses = models.JSONField(default=dict, blank=True)
    overall_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, null=True, blank=True)
    is_confidential = models.BooleanField(default=True)
    additional_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offboard_exit_interview'

    def __str__(self):
        return f"Exit Interview — {self.case.employee} on {self.interview_date}"


class FinalSettlement(models.Model):
    PAYMENT_BANK_TRANSFER = 'BANK_TRANSFER'
    PAYMENT_CHEQUE = 'CHEQUE'
    PAYMENT_CASH = 'CASH'

    PAYMENT_CHOICES = [
        (PAYMENT_BANK_TRANSFER, 'Bank Transfer'),
        (PAYMENT_CHEQUE, 'Cheque'),
        (PAYMENT_CASH, 'Cash'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_PAID = 'PAID'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PAID, 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(OffboardingCase, on_delete=models.CASCADE, related_name='final_settlements')
    basic_pay_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leave_encashment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gratuity_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notice_pay_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    asset_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_additions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_settlement = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    settlement_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_BANK_TRANSFER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='settlements_approved'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'offboard_final_settlement'

    def __str__(self):
        return f"Settlement for {self.case.employee} — {self.status}"

    def compute_total(self):
        self.total_settlement = (
            self.basic_pay_balance + self.leave_encashment + self.gratuity_amount
            + self.other_additions
            - self.notice_pay_deduction - self.asset_deductions - self.other_deductions
        )
