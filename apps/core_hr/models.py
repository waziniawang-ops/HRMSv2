import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class OrgUnit(models.Model):
    TYPE_ORGANIZATION = 'ORGANIZATION'
    TYPE_COMPANY = 'COMPANY'
    TYPE_DIVISION = 'DIVISION'
    TYPE_DEPARTMENT = 'DEPARTMENT'
    TYPE_UNIT = 'UNIT'
    TYPE_BRANCH = 'BRANCH'

    TYPE_CHOICES = [
        (TYPE_ORGANIZATION, 'Organization'),
        (TYPE_COMPANY, 'Company'),
        (TYPE_DIVISION, 'Division'),
        (TYPE_DEPARTMENT, 'Department'),
        (TYPE_UNIT, 'Unit'),
        (TYPE_BRANCH, 'Branch'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_DEPARTMENT)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    head_employee = models.ForeignKey(
        'core_hr.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='headed_units'
    )
    status = models.CharField(max_length=20, default='ACTIVE')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='org_units_created'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_org_unit'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class CostCenter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    org_unit = models.ForeignKey(OrgUnit, on_delete=models.PROTECT, related_name='cost_centers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_cost_center'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class JobFamily(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_job_family'
        ordering = ['name']

    def __str__(self):
        return self.name


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_code = models.CharField(max_length=50, unique=True)
    job_title = models.CharField(max_length=255)
    job_family = models.ForeignKey(
        JobFamily, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs'
    )
    description = models.TextField(blank=True)
    competency_profile = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_job'
        ordering = ['job_title']

    def __str__(self):
        return f"{self.job_code} - {self.job_title}"


class Grade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade_code = models.CharField(max_length=20, unique=True)
    grade_name = models.CharField(max_length=100)
    pay_band_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pay_band_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    level = models.PositiveIntegerField(default=1, help_text="Numeric seniority level")
    is_active = models.BooleanField(default=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_grade'
        ordering = ['level']

    def __str__(self):
        return f"{self.grade_code} - {self.grade_name}"


class Position(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_APPROVED = 'APPROVED'
    STATUS_VACANT = 'VACANT'
    STATUS_OCCUPIED = 'OCCUPIED'
    STATUS_FROZEN = 'FROZEN'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_VACANT, 'Vacant'),
        (STATUS_OCCUPIED, 'Occupied'),
        (STATUS_FROZEN, 'Frozen'),
        (STATUS_CLOSED, 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    position_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name='positions')
    org_unit = models.ForeignKey(OrgUnit, on_delete=models.PROTECT, related_name='positions')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, related_name='positions')
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name='positions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    incumbent_employee = models.ForeignKey(
        'core_hr.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='occupied_positions'
    )
    is_critical = models.BooleanField(default=False, help_text="Critical role for succession planning")
    headcount_budget = models.PositiveIntegerField(default=1)
    reporting_to = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='direct_reports'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='positions'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='positions_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_position'
        ordering = ['position_code']
        indexes = [
            models.Index(fields=['status', 'org_unit']),
        ]

    def __str__(self):
        return f"{self.position_code} - {self.title} [{self.status}]"


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='person'
    )
    legal_name = models.CharField(max_length=255)
    preferred_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id_hash = models.CharField(max_length=255, blank=True, help_text="Hashed national ID")
    email = models.EmailField(unique=True)
    personal_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_person'
        ordering = ['legal_name']

    def __str__(self):
        return self.legal_name or self.email


class Employee(models.Model):
    STATUS_PROBATION = 'PROBATION'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_TERMINATED = 'TERMINATED'
    STATUS_RESIGNED = 'RESIGNED'
    STATUS_RETIRED = 'RETIRED'

    STATUS_CHOICES = [
        (STATUS_PROBATION, 'Probation'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_TERMINATED, 'Terminated'),
        (STATUS_RESIGNED, 'Resigned'),
        (STATUS_RETIRED, 'Retired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.OneToOneField(Person, on_delete=models.PROTECT, related_name='employee')
    employee_number = models.CharField(max_length=50, unique=True)
    hire_date = models.DateField()
    employment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROBATION)
    manager = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='direct_reports'
    )
    position = models.ForeignKey(
        Position, null=True, blank=True, on_delete=models.SET_NULL, related_name='employees'
    )
    org_unit = models.ForeignKey(
        OrgUnit, null=True, blank=True, on_delete=models.SET_NULL, related_name='employees'
    )
    grade = models.ForeignKey(
        Grade, null=True, blank=True, on_delete=models.SET_NULL, related_name='employees'
    )
    source_onboarding = models.ForeignKey(
        'onboarding.OnboardingCase', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='converted_employees'
    )
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_employee'
        ordering = ['employee_number']
        indexes = [
            models.Index(fields=['employment_status']),
            models.Index(fields=['manager']),
        ]

    def __str__(self):
        return f"{self.employee_number} - {self.person.legal_name}"

    @property
    def full_name(self):
        return self.person.legal_name

    @property
    def is_active_employee(self):
        return self.employment_status in [self.STATUS_PROBATION, self.STATUS_ACTIVE]


class EmployeeAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assignments')
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    org_unit = models.ForeignKey(OrgUnit, on_delete=models.PROTECT)
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT)
    manager = models.ForeignKey(
        Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name='managed_assignments'
    )
    is_primary = models.BooleanField(default=True)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_employee_assignment'
        ordering = ['-valid_from']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'is_primary'],
                condition=models.Q(is_primary=True, valid_to=None),
                name='uq_primary_assignment_per_employee'
            )
        ]

    def __str__(self):
        return f"{self.employee} → {self.position} from {self.valid_from}"


class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        db_table = 'core_system_setting'
        ordering = ['key']

    def __str__(self):
        return f"{self.key} = {self.value}"
