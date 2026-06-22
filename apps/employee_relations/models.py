import uuid
from django.conf import settings
from django.db import models


class ERCaseCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    is_grievance = models.BooleanField(default=False)
    is_disciplinary = models.BooleanField(default=False)
    is_confidential = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'er_case_category'
        ordering = ['name']

    def __str__(self):
        return self.name


class ERCase(models.Model):
    TYPE_GRIEVANCE = 'GRIEVANCE'
    TYPE_DISCIPLINARY = 'DISCIPLINARY'
    TYPE_MISCONDUCT = 'MISCONDUCT'
    TYPE_POOR_PERFORMANCE = 'POOR_PERFORMANCE'
    TYPE_ATTENDANCE = 'ATTENDANCE'
    TYPE_FRAUD = 'FRAUD'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_GRIEVANCE, 'Grievance'),
        (TYPE_DISCIPLINARY, 'Disciplinary'),
        (TYPE_MISCONDUCT, 'Misconduct'),
        (TYPE_POOR_PERFORMANCE, 'Poor Performance'),
        (TYPE_ATTENDANCE, 'Attendance'),
        (TYPE_FRAUD, 'Fraud'),
        (TYPE_OTHER, 'Other'),
    ]

    STATUS_OPEN = 'OPEN'
    STATUS_UNDER_INVESTIGATION = 'UNDER_INVESTIGATION'
    STATUS_HEARING_SCHEDULED = 'HEARING_SCHEDULED'
    STATUS_HEARING_COMPLETED = 'HEARING_COMPLETED'
    STATUS_OUTCOME_ISSUED = 'OUTCOME_ISSUED'
    STATUS_APPEALED = 'APPEALED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_WITHDRAWN = 'WITHDRAWN'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_UNDER_INVESTIGATION, 'Under Investigation'),
        (STATUS_HEARING_SCHEDULED, 'Hearing Scheduled'),
        (STATUS_HEARING_COMPLETED, 'Hearing Completed'),
        (STATUS_OUTCOME_ISSUED, 'Outcome Issued'),
        (STATUS_APPEALED, 'Appealed'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
    ]

    SEVERITY_MINOR = 'MINOR'
    SEVERITY_MODERATE = 'MODERATE'
    SEVERITY_MAJOR = 'MAJOR'
    SEVERITY_GROSS = 'GROSS_MISCONDUCT'

    SEVERITY_CHOICES = [
        (SEVERITY_MINOR, 'Minor'),
        (SEVERITY_MODERATE, 'Moderate'),
        (SEVERITY_MAJOR, 'Major'),
        (SEVERITY_GROSS, 'Gross Misconduct'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=30, unique=True, blank=True)
    category = models.ForeignKey(
        ERCaseCategory, on_delete=models.PROTECT, related_name='cases'
    )
    subject = models.CharField(max_length=255)
    description = models.TextField()
    case_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MINOR)
    subject_employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='er_cases_as_subject'
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='er_cases_opened'
    )
    assigned_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='er_cases_investigating'
    )
    legal_hold = models.BooleanField(default=False)
    confidential = models.BooleanField(default=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'er_case'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['subject_employee']),
        ]

    def __str__(self):
        return f"{self.case_number} — {self.subject} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.case_number:
            from django.utils import timezone
            year = timezone.now().year
            last = ERCase.objects.filter(created_at__year=year).order_by('-case_number').first()
            if last and last.case_number:
                try:
                    seq = int(last.case_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            self.case_number = f"ER-{year}-{seq:05d}"
        super().save(*args, **kwargs)


class CaseParty(models.Model):
    ROLE_COMPLAINANT = 'COMPLAINANT'
    ROLE_RESPONDENT = 'RESPONDENT'
    ROLE_WITNESS = 'WITNESS'
    ROLE_INVESTIGATOR = 'INVESTIGATOR'
    ROLE_PANEL_MEMBER = 'PANEL_MEMBER'
    ROLE_ADVOCATE = 'ADVOCATE'

    ROLE_CHOICES = [
        (ROLE_COMPLAINANT, 'Complainant'),
        (ROLE_RESPONDENT, 'Respondent'),
        (ROLE_WITNESS, 'Witness'),
        (ROLE_INVESTIGATOR, 'Investigator'),
        (ROLE_PANEL_MEMBER, 'Panel Member'),
        (ROLE_ADVOCATE, 'Advocate'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ERCase, on_delete=models.CASCADE, related_name='parties')
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='er_case_roles'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    coi_declared = models.BooleanField(default=False)
    coi_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'er_case_party'
        unique_together = [['case', 'employee', 'role']]

    def __str__(self):
        return f"{self.employee} as {self.role} in {self.case.case_number}"


class CaseEvidence(models.Model):
    TYPE_DOCUMENT = 'DOCUMENT'
    TYPE_WITNESS_STATEMENT = 'WITNESS_STATEMENT'
    TYPE_CCTV = 'CCTV'
    TYPE_EMAIL = 'EMAIL'
    TYPE_SYSTEM_LOG = 'SYSTEM_LOG'
    TYPE_PHOTOGRAPH = 'PHOTOGRAPH'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_DOCUMENT, 'Document'),
        (TYPE_WITNESS_STATEMENT, 'Witness Statement'),
        (TYPE_CCTV, 'CCTV Footage'),
        (TYPE_EMAIL, 'Email'),
        (TYPE_SYSTEM_LOG, 'System Log'),
        (TYPE_PHOTOGRAPH, 'Photograph'),
        (TYPE_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ERCase, on_delete=models.CASCADE, related_name='evidence')
    title = models.CharField(max_length=255)
    description = models.TextField()
    evidence_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    document = models.FileField(null=True, blank=True, upload_to='er/evidence/')
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='er_evidence_added'
    )
    is_confidential = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'er_case_evidence'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.evidence_type} — {self.title}"


class CaseHearing(models.Model):
    TYPE_PRELIMINARY = 'PRELIMINARY'
    TYPE_INVESTIGATIVE = 'INVESTIGATIVE'
    TYPE_DISCIPLINARY = 'DISCIPLINARY'
    TYPE_APPEAL = 'APPEAL'

    TYPE_CHOICES = [
        (TYPE_PRELIMINARY, 'Preliminary'),
        (TYPE_INVESTIGATIVE, 'Investigative'),
        (TYPE_DISCIPLINARY, 'Disciplinary'),
        (TYPE_APPEAL, 'Appeal'),
    ]

    STATUS_SCHEDULED = 'SCHEDULED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_POSTPONED = 'POSTPONED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_POSTPONED, 'Postponed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ERCase, on_delete=models.CASCADE, related_name='hearings')
    hearing_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    hearing_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_DISCIPLINARY)
    panel_members = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    outcome_summary = models.TextField(blank=True)
    minutes = models.FileField(null=True, blank=True, upload_to='er/hearings/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'er_case_hearing'
        ordering = ['hearing_date']

    def __str__(self):
        return f"Hearing for {self.case.case_number} on {self.hearing_date}"


class CaseOutcome(models.Model):
    TYPE_VERBAL_WARNING = 'VERBAL_WARNING'
    TYPE_WRITTEN_WARNING = 'WRITTEN_WARNING'
    TYPE_FINAL_WARNING = 'FINAL_WARNING'
    TYPE_SUSPENSION = 'SUSPENSION'
    TYPE_DEMOTION = 'DEMOTION'
    TYPE_TERMINATION = 'TERMINATION'
    TYPE_DISMISSED = 'DISMISSED'
    TYPE_REINSTATEMENT = 'REINSTATEMENT'
    TYPE_NO_ACTION = 'NO_ACTION'

    TYPE_CHOICES = [
        (TYPE_VERBAL_WARNING, 'Verbal Warning'),
        (TYPE_WRITTEN_WARNING, 'Written Warning'),
        (TYPE_FINAL_WARNING, 'Final Warning'),
        (TYPE_SUSPENSION, 'Suspension'),
        (TYPE_DEMOTION, 'Demotion'),
        (TYPE_TERMINATION, 'Termination'),
        (TYPE_DISMISSED, 'Dismissed'),
        (TYPE_REINSTATEMENT, 'Reinstatement'),
        (TYPE_NO_ACTION, 'No Action'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ERCase, on_delete=models.CASCADE, related_name='outcomes')
    outcome_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    effective_date = models.DateField()
    duration_days = models.IntegerField(null=True, blank=True)
    outcome_details = models.TextField(blank=True)
    letter_issued = models.BooleanField(default=False)
    letter_issued_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='er_outcomes_decided'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'er_case_outcome'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.outcome_type} for {self.case.case_number}"


class ERAppeal(models.Model):
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_UPHELD = 'UPHELD'
    STATUS_PARTIALLY_UPHELD = 'PARTIALLY_UPHELD'
    STATUS_DISMISSED = 'DISMISSED'
    STATUS_WITHDRAWN = 'WITHDRAWN'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_UPHELD, 'Upheld'),
        (STATUS_PARTIALLY_UPHELD, 'Partially Upheld'),
        (STATUS_DISMISSED, 'Dismissed'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ERCase, on_delete=models.PROTECT, related_name='appeals')
    appellant = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='er_appeals'
    )
    appeal_date = models.DateField()
    appeal_reason = models.TextField()
    grounds_of_appeal = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='er_appeals_reviewed'
    )
    review_notes = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'er_appeal'
        ordering = ['-appeal_date']

    def __str__(self):
        return f"Appeal by {self.appellant} for {self.case.case_number} [{self.status}]"
