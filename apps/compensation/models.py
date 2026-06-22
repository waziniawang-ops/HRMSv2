import uuid
from django.conf import settings
from django.db import models


class SalaryComponent(models.Model):
    CATEGORY_BASIC = 'BASIC'
    CATEGORY_HOUSING = 'HOUSING'
    CATEGORY_TRANSPORT = 'TRANSPORT'
    CATEGORY_UTILITY = 'UTILITY'
    CATEGORY_ALLOWANCE = 'ALLOWANCE'
    CATEGORY_OVERTIME = 'OVERTIME'
    CATEGORY_BONUS = 'BONUS'

    CATEGORY_CHOICES = [
        (CATEGORY_BASIC, 'Basic Pay'),
        (CATEGORY_HOUSING, 'Housing Allowance'),
        (CATEGORY_TRANSPORT, 'Transport Allowance'),
        (CATEGORY_UTILITY, 'Utility Allowance'),
        (CATEGORY_ALLOWANCE, 'General Allowance'),
        (CATEGORY_OVERTIME, 'Overtime Pay'),
        (CATEGORY_BONUS, 'Bonus'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    default_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_pensionable = models.BooleanField(default=False)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comp_salary_component'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class GradeBand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade = models.ForeignKey(
        'core_hr.Grade', on_delete=models.PROTECT, related_name='grade_bands'
    )
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.PROTECT, related_name='grade_bands'
    )
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    mid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='BND')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comp_grade_band'
        unique_together = [['grade', 'component']]
        ordering = ['grade', 'component']

    def __str__(self):
        return f"{self.grade} | {self.component}"


class EmployeePackage(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUPERSEDED = 'SUPERSEDED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUPERSEDED, 'Superseded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='packages'
    )
    effective_date = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    total_ctc = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default='BND')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    components = models.JSONField(
        default=list,
        help_text='[{"component_id": "...", "component_name": "...", "amount": 0, "currency": "BND"}]'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='packages_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='packages_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comp_employee_package'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.employee} | Package from {self.effective_date} [{self.status}]"


class CompensationChange(models.Model):
    TYPE_INCREMENT = 'INCREMENT'
    TYPE_BONUS = 'BONUS'
    TYPE_ADJUSTMENT = 'ADJUSTMENT'
    TYPE_PROMOTION = 'PROMOTION'
    TYPE_DEMOTION = 'DEMOTION'
    TYPE_REVISION = 'REVISION'

    TYPE_CHOICES = [
        (TYPE_INCREMENT, 'Increment'),
        (TYPE_BONUS, 'Bonus'),
        (TYPE_ADJUSTMENT, 'Adjustment'),
        (TYPE_PROMOTION, 'Promotion'),
        (TYPE_DEMOTION, 'Demotion'),
        (TYPE_REVISION, 'Revision'),
    ]

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
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='comp_changes'
    )
    change_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    previous_package = models.ForeignKey(
        EmployeePackage, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    new_package = models.ForeignKey(
        EmployeePackage, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    effective_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='comp_changes_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comp_change'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} | {self.change_type} on {self.effective_date}"


class BonusCycle(models.Model):
    TYPE_PERFORMANCE = 'PERFORMANCE'
    TYPE_DISCRETIONARY = 'DISCRETIONARY'
    TYPE_ANNUAL = 'ANNUAL'
    TYPE_FESTIVE = 'FESTIVE'
    TYPE_SPECIAL = 'SPECIAL'

    TYPE_CHOICES = [
        (TYPE_PERFORMANCE, 'Performance Bonus'),
        (TYPE_DISCRETIONARY, 'Discretionary Bonus'),
        (TYPE_ANNUAL, 'Annual Bonus'),
        (TYPE_FESTIVE, 'Festive Bonus'),
        (TYPE_SPECIAL, 'Special Bonus'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_OPEN = 'OPEN'
    STATUS_CLOSED = 'CLOSED'
    STATUS_PAID = 'PAID'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_PAID, 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    year = models.PositiveIntegerField()
    bonus_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    budget_pool = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=10, default='BND')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='bonus_cycles_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='bonus_cycles_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comp_bonus_cycle'
        unique_together = [['name', 'year']]
        ordering = ['-year', 'name']

    def __str__(self):
        return f"{self.name} {self.year} [{self.status}]"


class BonusAllocation(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_PAID = 'PAID'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_PAID, 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle = models.ForeignKey(BonusCycle, on_delete=models.PROTECT, related_name='allocations')
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='bonus_allocations'
    )
    recommended_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    performance_rating = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    recommended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='bonus_recommendations'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='bonus_approvals'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comp_bonus_allocation'
        unique_together = [['cycle', 'employee']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} | {self.cycle} | {self.recommended_amount}"
