import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class HSEIncidentType(models.Model):
    SEVERITY_MINOR = 'MINOR'
    SEVERITY_MODERATE = 'MODERATE'
    SEVERITY_MAJOR = 'MAJOR'
    SEVERITY_CRITICAL = 'CRITICAL'
    SEVERITY_FATALITY = 'FATALITY'

    SEVERITY_CHOICES = [
        (SEVERITY_MINOR, 'Minor'),
        (SEVERITY_MODERATE, 'Moderate'),
        (SEVERITY_MAJOR, 'Major'),
        (SEVERITY_CRITICAL, 'Critical'),
        (SEVERITY_FATALITY, 'Fatality'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    default_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MINOR)
    requires_investigation = models.BooleanField(default=True)
    notification_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'hse_incident_type'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class HSEIncident(models.Model):
    SEVERITY_MINOR = 'MINOR'
    SEVERITY_MODERATE = 'MODERATE'
    SEVERITY_MAJOR = 'MAJOR'
    SEVERITY_CRITICAL = 'CRITICAL'
    SEVERITY_FATALITY = 'FATALITY'

    SEVERITY_CHOICES = [
        (SEVERITY_MINOR, 'Minor'),
        (SEVERITY_MODERATE, 'Moderate'),
        (SEVERITY_MAJOR, 'Major'),
        (SEVERITY_CRITICAL, 'Critical'),
        (SEVERITY_FATALITY, 'Fatality'),
    ]

    STATUS_REPORTED = 'REPORTED'
    STATUS_UNDER_INVESTIGATION = 'UNDER_INVESTIGATION'
    STATUS_ACTION_REQUIRED = 'ACTION_REQUIRED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_DISMISSED = 'DISMISSED'

    STATUS_CHOICES = [
        (STATUS_REPORTED, 'Reported'),
        (STATUS_UNDER_INVESTIGATION, 'Under Investigation'),
        (STATUS_ACTION_REQUIRED, 'Action Required'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_DISMISSED, 'Dismissed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_number = models.CharField(max_length=30, unique=True, blank=True)
    incident_type = models.ForeignKey(
        HSEIncidentType, on_delete=models.PROTECT, related_name='incidents'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    incident_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_REPORTED)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='hse_incidents_reported'
    )
    employees_involved = models.JSONField(default=list, blank=True)
    witness_names = models.JSONField(default=list, blank=True)
    immediate_action_taken = models.TextField(blank=True)
    is_work_related = models.BooleanField(default=True)
    is_notifiable = models.BooleanField(default=False)
    notification_authority = models.CharField(max_length=255, blank=True)
    root_cause_identified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hse_incident'
        ordering = ['-incident_date']
        indexes = [
            models.Index(fields=['status', 'severity']),
        ]

    def __str__(self):
        return f"{self.incident_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.incident_number:
            year = timezone.now().year
            last = HSEIncident.objects.filter(created_at__year=year).order_by('-incident_number').first()
            try:
                seq = int(last.incident_number.split('-')[-1]) + 1 if last and last.incident_number else 1
            except (ValueError, IndexError, AttributeError):
                seq = 1
            self.incident_number = f"INC-{year}-{seq:05d}"
        super().save(*args, **kwargs)


class IncidentInvestigation(models.Model):
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident = models.ForeignKey(
        HSEIncident, on_delete=models.CASCADE, related_name='investigations'
    )
    lead_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='hse_investigations_led'
    )
    team_members = models.JSONField(default=list, blank=True)
    investigation_start = models.DateField()
    target_close_date = models.DateField(null=True, blank=True)
    root_cause = models.TextField(blank=True)
    contributing_factors = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    completed_at = models.DateTimeField(null=True, blank=True)
    report_file = models.FileField(upload_to='hse/investigation_reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hse_investigation'
        ordering = ['-investigation_start']

    def __str__(self):
        return f"Investigation: {self.incident.incident_number} [{self.status}]"


class CorrectiveAction(models.Model):
    ACTION_TYPE_CORRECTIVE = 'CORRECTIVE'
    ACTION_TYPE_PREVENTIVE = 'PREVENTIVE'
    ACTION_TYPE_BOTH = 'BOTH'

    ACTION_TYPE_CHOICES = [
        (ACTION_TYPE_CORRECTIVE, 'Corrective'),
        (ACTION_TYPE_PREVENTIVE, 'Preventive'),
        (ACTION_TYPE_BOTH, 'Both'),
    ]

    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_CRITICAL = 'CRITICAL'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]

    STATUS_OPEN = 'OPEN'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_OVERDUE = 'OVERDUE'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investigation = models.ForeignKey(
        IncidentInvestigation, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='corrective_actions'
    )
    incident = models.ForeignKey(
        HSEIncident, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='direct_corrective_actions'
    )
    action_description = models.TextField()
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES, default=ACTION_TYPE_CORRECTIVE)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='hse_actions_assigned'
    )
    due_date = models.DateField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    completion_evidence = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='hse_actions_verified'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hse_corrective_action'
        ordering = ['due_date']

    def __str__(self):
        return f"Action [{self.priority}]: {self.action_description[:60]}"


class WellbeingProgram(models.Model):
    TYPE_MENTAL_HEALTH = 'MENTAL_HEALTH'
    TYPE_PHYSICAL_FITNESS = 'PHYSICAL_FITNESS'
    TYPE_FINANCIAL_WELLNESS = 'FINANCIAL_WELLNESS'
    TYPE_SOCIAL = 'SOCIAL'
    TYPE_ERGONOMICS = 'ERGONOMICS'
    TYPE_NUTRITION = 'NUTRITION'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_MENTAL_HEALTH, 'Mental Health'),
        (TYPE_PHYSICAL_FITNESS, 'Physical Fitness'),
        (TYPE_FINANCIAL_WELLNESS, 'Financial Wellness'),
        (TYPE_SOCIAL, 'Social'),
        (TYPE_ERGONOMICS, 'Ergonomics'),
        (TYPE_NUTRITION, 'Nutrition'),
        (TYPE_OTHER, 'Other'),
    ]

    STATUS_PLANNED = 'PLANNED'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PLANNED, 'Planned'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    program_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED)
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='wellbeing_programs_facilitated'
    )
    target_audience = models.CharField(max_length=255, blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    current_enrollment = models.PositiveIntegerField(default=0)
    is_mandatory = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='wellbeing_programs_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hse_wellbeing_program'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} [{self.status}]"


class WellbeingEnrollment(models.Model):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_WITHDRAWN = 'WITHDRAWN'
    STATUS_NO_SHOW = 'NO_SHOW'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
        (STATUS_NO_SHOW, 'No Show'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(
        WellbeingProgram, on_delete=models.PROTECT, related_name='enrollments'
    )
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='wellbeing_enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    completion_date = models.DateField(null=True, blank=True)
    attendance_percentage = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'hse_wellbeing_enrollment'
        unique_together = [['program', 'employee']]

    def __str__(self):
        return f"{self.employee} — {self.program.name}"


class MedicalFitnessRecord(models.Model):
    FITNESS_FIT = 'FIT'
    FITNESS_FIT_WITH_RESTRICTIONS = 'FIT_WITH_RESTRICTIONS'
    FITNESS_TEMPORARILY_UNFIT = 'TEMPORARILY_UNFIT'
    FITNESS_PERMANENTLY_UNFIT = 'PERMANENTLY_UNFIT'

    FITNESS_CHOICES = [
        (FITNESS_FIT, 'Fit'),
        (FITNESS_FIT_WITH_RESTRICTIONS, 'Fit with Restrictions'),
        (FITNESS_TEMPORARILY_UNFIT, 'Temporarily Unfit'),
        (FITNESS_PERMANENTLY_UNFIT, 'Permanently Unfit'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='medical_fitness_records'
    )
    assessment_date = models.DateField()
    fitness_status = models.CharField(max_length=30, choices=FITNESS_CHOICES)
    restrictions = models.TextField(blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    assessed_by = models.CharField(max_length=255, blank=True)
    medical_facility = models.CharField(max_length=255, blank=True)
    certificate_file = models.FileField(upload_to='hse/medical/', null=True, blank=True)
    is_confidential = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hse_medical_fitness'
        ordering = ['-assessment_date']

    def __str__(self):
        return f"{self.employee} — {self.fitness_status} ({self.assessment_date})"
