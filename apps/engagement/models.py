import uuid
from django.conf import settings
from django.db import models


class SurveyTemplate(models.Model):
    TYPE_PULSE = 'PULSE'
    TYPE_ENGAGEMENT = 'ENGAGEMENT'
    TYPE_ENPS = 'ENPS'
    TYPE_EXIT = 'EXIT'
    TYPE_ONBOARDING = 'ONBOARDING'
    TYPE_360 = '360_FEEDBACK'
    TYPE_CUSTOM = 'CUSTOM'

    TYPE_CHOICES = [
        (TYPE_PULSE, 'Pulse Survey'),
        (TYPE_ENGAGEMENT, 'Engagement Survey'),
        (TYPE_ENPS, 'eNPS Survey'),
        (TYPE_EXIT, 'Exit Survey'),
        (TYPE_ONBOARDING, 'Onboarding Survey'),
        (TYPE_360, '360 Feedback'),
        (TYPE_CUSTOM, 'Custom Survey'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    survey_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CUSTOM)
    questions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='survey_templates_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'engagement_survey_template'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class EngagementSurvey(models.Model):
    AUDIENCE_ALL = 'ALL'
    AUDIENCE_ORG_UNIT = 'ORG_UNIT'
    AUDIENCE_GRADE = 'GRADE'
    AUDIENCE_DEPARTMENT = 'DEPARTMENT'
    AUDIENCE_CUSTOM = 'CUSTOM'

    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL, 'All Employees'),
        (AUDIENCE_ORG_UNIT, 'Org Unit'),
        (AUDIENCE_GRADE, 'Grade'),
        (AUDIENCE_DEPARTMENT, 'Department'),
        (AUDIENCE_CUSTOM, 'Custom List'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_CLOSED = 'CLOSED'
    STATUS_ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(SurveyTemplate, on_delete=models.PROTECT, related_name='surveys')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL)
    target_ids = models.JSONField(default=list, blank=True)
    open_date = models.DateTimeField()
    close_date = models.DateTimeField()
    is_anonymous = models.BooleanField(default=True)
    anonymity_threshold = models.PositiveIntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    response_count = models.PositiveIntegerField(default=0)
    launched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='surveys_launched'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'engagement_survey'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.status}]"


class SurveyResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(EngagementSurvey, on_delete=models.CASCADE, related_name='responses')
    employee = models.ForeignKey(
        'core_hr.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='survey_responses'
    )
    response_token = models.CharField(max_length=64, unique=True)
    responses = models.JSONField(default=dict, blank=True)
    enps_score = models.SmallIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        db_table = 'engagement_survey_response'
        unique_together = [['survey', 'employee']]

    def __str__(self):
        return f"Response to {self.survey.title}"


class ActionPlan(models.Model):
    STATUS_PLANNED = 'PLANNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_ON_HOLD = 'ON_HOLD'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PLANNED, 'Planned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_ON_HOLD, 'On Hold'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(EngagementSurvey, on_delete=models.PROTECT, related_name='action_plans')
    title = models.CharField(max_length=255)
    description = models.TextField()
    focus_area = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='action_plans_assigned'
    )
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED)
    progress_notes = models.TextField(blank=True)
    completion_percentage = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='action_plans_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'engagement_action_plan'
        ordering = ['target_date']

    def __str__(self):
        return f"{self.title} [{self.status}]"


class RecognitionType(models.Model):
    CATEGORY_PEER = 'PEER'
    CATEGORY_MANAGER = 'MANAGER'
    CATEGORY_COMPANY = 'COMPANY'
    CATEGORY_MILESTONE = 'MILESTONE'
    CATEGORY_ANNIVERSARY = 'ANNIVERSARY'

    CATEGORY_CHOICES = [
        (CATEGORY_PEER, 'Peer Recognition'),
        (CATEGORY_MANAGER, 'Manager Recognition'),
        (CATEGORY_COMPANY, 'Company Award'),
        (CATEGORY_MILESTONE, 'Milestone Award'),
        (CATEGORY_ANNIVERSARY, 'Service Anniversary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    recognition_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    points_value = models.PositiveIntegerField(default=0)
    badge_icon = models.CharField(max_length=100, blank=True)
    requires_approval = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'engagement_recognition_type'
        ordering = ['name']

    def __str__(self):
        return self.name


class RecognitionAward(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nominated_by = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='awards_given'
    )
    recipient = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='awards_received'
    )
    recognition_type = models.ForeignKey(RecognitionType, on_delete=models.PROTECT)
    message = models.TextField()
    is_public = models.BooleanField(default=True)
    points_awarded = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_APPROVED)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='awards_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'engagement_recognition_award'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nominated_by} → {self.recipient}: {self.recognition_type.name}"


class RecognitionNomination(models.Model):
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nominator = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='nominations_made'
    )
    nominee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='nominations_received'
    )
    recognition_type = models.ForeignKey(RecognitionType, on_delete=models.PROTECT)
    justification = models.TextField()
    supporting_evidence = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'engagement_recognition_nomination'
        ordering = ['-created_at']

    def __str__(self):
        return f"Nomination: {self.nominator} → {self.nominee}"


class EmployeePoints(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='recognition_points'
    )
    total_earned = models.PositiveIntegerField(default=0)
    total_redeemed = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'engagement_employee_points'

    def __str__(self):
        return f"{self.employee} — {self.available_points} pts available"

    @property
    def available_points(self):
        return self.total_earned - self.total_redeemed
