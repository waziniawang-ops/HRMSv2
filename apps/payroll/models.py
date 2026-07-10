import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class PayrollCalendar(models.Model):
    PAY_GROUP_MONTHLY = 'MONTHLY'
    PAY_GROUP_BIWEEKLY = 'BIWEEKLY'
    PAY_GROUP_WEEKLY = 'WEEKLY'
    PAY_GROUP_FORTNIGHTLY = 'FORTNIGHTLY'

    PAY_GROUP_CHOICES = [
        (PAY_GROUP_MONTHLY, 'Monthly'),
        (PAY_GROUP_BIWEEKLY, 'Bi-Weekly'),
        (PAY_GROUP_WEEKLY, 'Weekly'),
        (PAY_GROUP_FORTNIGHTLY, 'Fortnightly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    pay_group = models.CharField(max_length=20, choices=PAY_GROUP_CHOICES, default=PAY_GROUP_MONTHLY)
    frequency = models.CharField(max_length=255, blank=True, help_text='Description of pay frequency')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_calendars_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payroll_calendar'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class PayrollElement(models.Model):
    CATEGORY_BASIC = 'BASIC'
    CATEGORY_ALLOWANCE = 'ALLOWANCE'
    CATEGORY_DEDUCTION = 'DEDUCTION'
    CATEGORY_CONTRIBUTION = 'CONTRIBUTION'
    CATEGORY_TAX = 'TAX'

    CATEGORY_CHOICES = [
        (CATEGORY_BASIC, 'Basic Pay'),
        (CATEGORY_ALLOWANCE, 'Allowance'),
        (CATEGORY_DEDUCTION, 'Deduction'),
        (CATEGORY_CONTRIBUTION, 'Employer Contribution'),
        (CATEGORY_TAX, 'Tax'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    is_taxable = models.BooleanField(default=True)
    is_pensionable = models.BooleanField(default=False)
    formula = models.JSONField(default=dict, help_text='{"type": "fixed", "value": 0}')
    gl_account = models.CharField(
        max_length=50, blank=True, default='',
        help_text='GL account code this element posts to (expense account for earnings, liability account for deductions/tax).'
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payroll_element'
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.category})"


class EmployeePayrollProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='payroll_profile'
    )
    calendar = models.ForeignKey(
        PayrollCalendar, on_delete=models.PROTECT, related_name='employee_profiles'
    )
    bank_name = models.CharField(max_length=255)
    bank_account_number = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_profiles_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payroll_employee_profile'
        ordering = ['employee__employee_number']

    def __str__(self):
        return f"Payroll Profile: {self.employee}"


class PayrollRun(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_LOCKED = 'LOCKED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_PAID = 'PAID'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_LOCKED, 'Locked'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PAID, 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    calendar = models.ForeignKey(
        PayrollCalendar, on_delete=models.PROTECT, related_name='runs'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    pay_date = models.DateField(null=True, blank=True)
    total_gross = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    total_deductions = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    total_net = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    employee_count = models.PositiveIntegerField(default=0)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_runs_processed'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_runs_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_runs_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payroll_run'
        ordering = ['-period_start']
        unique_together = [['calendar', 'period_start', 'period_end']]

    def __str__(self):
        return f"{self.calendar} | {self.period_start} - {self.period_end} [{self.status}]"


class PayslipLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='lines')
    employee = models.ForeignKey('core_hr.Employee', on_delete=models.PROTECT, related_name='payslip_lines')
    element = models.ForeignKey(PayrollElement, on_delete=models.PROTECT, related_name='payslip_lines')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_deduction = models.BooleanField(default=False)

    class Meta:
        db_table = 'payroll_payslip_line'
        ordering = ['element__display_order']

    def __str__(self):
        return f"{self.employee} | {self.element} = {self.amount}"


class Payslip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey('core_hr.Employee', on_delete=models.PROTECT, related_name='payslips')
    basic_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pension_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2)
    payslip_date = models.DateField()
    is_locked = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payroll_payslip'
        unique_together = [['payroll_run', 'employee']]
        ordering = ['-payslip_date']

    def __str__(self):
        return f"Payslip: {self.employee} | {self.payslip_date}"


class PayrollAdjustment(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='adjustments')
    employee = models.ForeignKey('core_hr.Employee', on_delete=models.PROTECT, related_name='payroll_adjustments')
    element = models.ForeignKey(PayrollElement, on_delete=models.PROTECT, related_name='adjustments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_adjustments_approved'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_adjustments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payroll_adjustment'
        ordering = ['-created_at']

    def __str__(self):
        return f"Adjustment: {self.employee} | {self.element} | {self.amount}"


class PayrollGLPosting(models.Model):
    ENTRY_DEBIT = 'DEBIT'
    ENTRY_CREDIT = 'CREDIT'

    ENTRY_TYPE_CHOICES = [
        (ENTRY_DEBIT, 'Debit'),
        (ENTRY_CREDIT, 'Credit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='gl_postings')
    gl_account = models.CharField(max_length=50)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES, default=ENTRY_DEBIT)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_center = models.ForeignKey(
        'core_hr.CostCenter', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='payroll_gl_postings'
    )
    posting_date = models.DateField()
    is_posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    sent_to_accounting_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payroll_gl_posting'
        ordering = ['posting_date', 'gl_account']

    def __str__(self):
        return f"GL: {self.gl_account} | {self.entry_type} | {self.amount} | {self.posting_date}"


class AccountingIntegration(models.Model):
    """
    Singleton configuration for pushing GL postings to an external accounting
    system via a generic configurable API/webhook. Always accessed through
    `get_settings()` so exactly one row ever exists.
    """
    name = models.CharField(max_length=100, default='Accounting System')
    api_url = models.URLField(max_length=500, blank=True)
    api_key = models.CharField(max_length=500, blank=True)
    auth_header_name = models.CharField(max_length=100, blank=True, default='Authorization')
    auth_header_prefix = models.CharField(max_length=50, blank=True, default='Bearer')
    last_test_at = models.DateTimeField(null=True, blank=True)
    last_test_success = models.BooleanField(null=True, blank=True)
    last_test_detail = models.CharField(max_length=500, blank=True, default='')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payroll_accounting_integration'

    def __str__(self):
        return self.name

    @property
    def is_configured(self):
        return bool(self.api_url and self.api_key)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
