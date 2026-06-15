import uuid
from django.conf import settings
from django.db import models


class WorkforcePlan(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_year = models.PositiveIntegerField()
    org_unit = models.ForeignKey(
        'core_hr.OrgUnit', on_delete=models.PROTECT, related_name='workforce_plans'
    )
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='workforce_plans_prepared'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    headcount_current = models.PositiveIntegerField(default=0)
    headcount_target = models.PositiveIntegerField(default=0)
    attrition_forecast = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workforce_plans_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wf_plan'
        unique_together = ['plan_year', 'org_unit']
        ordering = ['-plan_year']

    def __str__(self):
        return f"Workforce Plan {self.plan_year} — {self.org_unit}"


class AttendancePolicy(models.Model):
    POLICY_FIXED = 'FIXED'
    POLICY_FLEXIBLE = 'FLEXIBLE'
    POLICY_SHIFT = 'SHIFT'

    POLICY_CHOICES = [
        (POLICY_FIXED, 'Fixed Hours'),
        (POLICY_FLEXIBLE, 'Flexible Hours'),
        (POLICY_SHIFT, 'Shift Based'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    policy_type = models.CharField(max_length=20, choices=POLICY_CHOICES, default=POLICY_FIXED)
    standard_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8)
    grace_minutes = models.PositiveIntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wf_attendance_policy'
        ordering = ['name']

    def __str__(self):
        return self.name


class AttendanceLog(models.Model):
    SOURCE_BIOMETRIC = 'BIOMETRIC'
    SOURCE_MANUAL = 'MANUAL'
    SOURCE_MOBILE = 'MOBILE'
    SOURCE_SYSTEM = 'SYSTEM'

    SOURCE_CHOICES = [
        (SOURCE_BIOMETRIC, 'Biometric'),
        (SOURCE_MANUAL, 'Manual Entry'),
        (SOURCE_MOBILE, 'Mobile App'),
        (SOURCE_SYSTEM, 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='attendance_logs'
    )
    date = models.DateField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_present = models.BooleanField(default=True)
    is_late = models.BooleanField(default=False)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_BIOMETRIC)
    remarks = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wf_attendance_log'
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} — {self.date}"

    def compute_hours(self):
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            self.hours_worked = round(delta.total_seconds() / 3600, 2)


class LeaveType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    days_per_year = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    carry_forward = models.BooleanField(default=False)
    max_carry_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wf_leave_type'
        ordering = ['name']

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='leave_balances'
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT, related_name='balances'
    )
    year = models.PositiveIntegerField()
    entitled_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pending_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    carried_forward = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wf_leave_balance'
        unique_together = ['employee', 'leave_type', 'year']

    @property
    def available_days(self):
        return self.entitled_days + self.carried_forward - self.used_days - self.pending_days


class LeaveRequest(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING, 'Pending Approval'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='leave_requests'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='requests')
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='leave_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wf_leave_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.start_date} to {self.end_date})"


class OvertimeRequest(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='overtime_requests'
    )
    date = models.DateField()
    hours_requested = models.DecimalField(max_digits=5, decimal_places=2)
    hours_approved = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='overtime_approvals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wf_overtime_request'
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} — OT {self.date} ({self.hours_requested}h)"


class Roster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='rosters'
    )
    shift_name = models.CharField(max_length=100)
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    effective_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='rosters_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wf_roster'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.employee} — {self.shift_name} from {self.effective_date}"


class Transfer(models.Model):
    TYPE_TRANSFER = 'TRANSFER'
    TYPE_PROMOTION = 'PROMOTION'
    TYPE_DEMOTION = 'DEMOTION'
    TYPE_LATERAL = 'LATERAL'
    TYPE_SECONDMENT = 'SECONDMENT'

    TYPE_CHOICES = [
        (TYPE_TRANSFER, 'Transfer'),
        (TYPE_PROMOTION, 'Promotion'),
        (TYPE_DEMOTION, 'Demotion'),
        (TYPE_LATERAL, 'Lateral Move'),
        (TYPE_SECONDMENT, 'Secondment'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='transfers'
    )
    movement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    from_position = models.ForeignKey(
        'core_hr.Position', on_delete=models.PROTECT, related_name='transfers_from'
    )
    to_position = models.ForeignKey(
        'core_hr.Position', on_delete=models.PROTECT, related_name='transfers_to'
    )
    from_grade = models.ForeignKey(
        'core_hr.Grade', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='transfers_from_grade'
    )
    to_grade = models.ForeignKey(
        'core_hr.Grade', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='transfers_to_grade'
    )
    effective_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='transfers_initiated'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='transfers_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='transfers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wf_transfer'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} — {self.movement_type} on {self.effective_date}"


class Separation(models.Model):
    TYPE_RESIGNATION = 'RESIGNATION'
    TYPE_TERMINATION = 'TERMINATION'
    TYPE_RETIREMENT = 'RETIREMENT'
    TYPE_END_OF_CONTRACT = 'END_OF_CONTRACT'
    TYPE_REDUNDANCY = 'REDUNDANCY'
    TYPE_DEATH = 'DEATH'

    TYPE_CHOICES = [
        (TYPE_RESIGNATION, 'Resignation'),
        (TYPE_TERMINATION, 'Termination'),
        (TYPE_RETIREMENT, 'Retirement'),
        (TYPE_END_OF_CONTRACT, 'End of Contract'),
        (TYPE_REDUNDANCY, 'Redundancy'),
        (TYPE_DEATH, 'Death'),
    ]

    STATUS_INITIATED = 'INITIATED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_INITIATED, 'Initiated'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='separation'
    )
    separation_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    notice_date = models.DateField()
    last_working_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INITIATED)
    clearance_completed = models.BooleanField(default=False)
    exit_interview_done = models.BooleanField(default=False)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='separations_initiated'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='separations_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wf_separation'
        ordering = ['-notice_date']

    def __str__(self):
        return f"{self.employee} — {self.separation_type}"
