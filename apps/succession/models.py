import uuid
from django.conf import settings
from django.db import models


class SuccessionPlan(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    position = models.ForeignKey(
        'core_hr.Position', on_delete=models.PROTECT, related_name='succession_plans'
    )
    incumbent = models.ForeignKey(
        'core_hr.Employee', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='succession_plans_as_incumbent'
    )
    plan_year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    risk_level = models.CharField(
        max_length=10,
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')],
        default='MEDIUM'
    )
    notes = models.TextField(blank=True)
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='succession_plans_prepared'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='succession_plans_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suc_plan'
        unique_together = ['position', 'plan_year']
        ordering = ['-plan_year']

    def __str__(self):
        return f"Succession Plan: {self.position} ({self.plan_year})"


class SuccessorNomination(models.Model):
    READINESS_IMMEDIATE = 'IMMEDIATE'
    READINESS_1_2_YEARS = '1_2_YEARS'
    READINESS_3_5_YEARS = '3_5_YEARS'
    READINESS_LONG_TERM = 'LONG_TERM'

    READINESS_CHOICES = [
        (READINESS_IMMEDIATE, 'Ready Now'),
        (READINESS_1_2_YEARS, 'Ready in 1-2 Years'),
        (READINESS_3_5_YEARS, 'Ready in 3-5 Years'),
        (READINESS_LONG_TERM, 'Long Term (5+ Years)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    succession_plan = models.ForeignKey(
        SuccessionPlan, on_delete=models.CASCADE, related_name='nominees'
    )
    candidate = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='successor_nominations'
    )
    readiness_level = models.CharField(max_length=20, choices=READINESS_CHOICES)
    priority_rank = models.PositiveIntegerField(default=1)
    strengths = models.TextField(blank=True)
    development_needs = models.TextField(blank=True)
    is_willing = models.BooleanField(default=True)
    nominated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='successor_nominations_made'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suc_nominee'
        unique_together = ['succession_plan', 'candidate']
        ordering = ['priority_rank']

    def __str__(self):
        return f"{self.candidate} → {self.succession_plan.position} (Rank {self.priority_rank})"


class TalentPool(models.Model):
    TIER_HIGH_POTENTIAL = 'HI_POT'
    TIER_HIGH_PERFORMER = 'HI_PERF'
    TIER_CORE = 'CORE'
    TIER_WATCH = 'WATCH'

    TIER_CHOICES = [
        (TIER_HIGH_POTENTIAL, 'High Potential'),
        (TIER_HIGH_PERFORMER, 'High Performer'),
        (TIER_CORE, 'Core Contributor'),
        (TIER_WATCH, 'Watch List'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suc_talent_pool'
        ordering = ['tier', 'name']

    def __str__(self):
        return f"{self.name} ({self.tier})"


class TalentProfile(models.Model):
    NINE_BOX_CHOICES = [
        (1, 'Low Performance / Low Potential'),
        (2, 'Low Performance / Moderate Potential'),
        (3, 'Low Performance / High Potential'),
        (4, 'Moderate Performance / Low Potential'),
        (5, 'Moderate Performance / Moderate Potential'),
        (6, 'Moderate Performance / High Potential'),
        (7, 'High Performance / Low Potential'),
        (8, 'High Performance / Moderate Potential'),
        (9, 'High Performance / High Potential'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='talent_profile'
    )
    talent_pool = models.ForeignKey(
        TalentPool, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='members'
    )
    nine_box_score = models.PositiveSmallIntegerField(
        choices=NINE_BOX_CHOICES, null=True, blank=True
    )
    flight_risk = models.CharField(
        max_length=10,
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')],
        default='LOW'
    )
    career_aspirations = models.TextField(blank=True)
    key_strengths = models.TextField(blank=True)
    development_areas = models.TextField(blank=True)
    mobility_preference = models.CharField(
        max_length=20,
        choices=[
            ('LOCAL', 'Local Only'),
            ('DOMESTIC', 'Domestic'),
            ('INTERNATIONAL', 'International'),
            ('ANY', 'Any Location'),
        ],
        default='LOCAL'
    )
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='talent_assessments'
    )
    last_assessed_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suc_talent_profile'

    def __str__(self):
        return f"Talent Profile: {self.employee}"


class DevelopmentPlan(models.Model):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='development_plans'
    )
    succession_nominee = models.ForeignKey(
        SuccessorNomination, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='development_plans'
    )
    title = models.CharField(max_length=255)
    objective = models.TextField()
    target_completion_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    progress_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='development_plans_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suc_dev_plan'
        ordering = ['-created_at']

    def __str__(self):
        return f"Dev Plan: {self.employee} — {self.title}"


class DevelopmentActivity(models.Model):
    TYPE_TRAINING = 'TRAINING'
    TYPE_MENTORING = 'MENTORING'
    TYPE_STRETCH_ASSIGNMENT = 'STRETCH_ASSIGNMENT'
    TYPE_COACHING = 'COACHING'
    TYPE_CERTIFICATION = 'CERTIFICATION'
    TYPE_JOB_ROTATION = 'JOB_ROTATION'

    TYPE_CHOICES = [
        (TYPE_TRAINING, 'Training'),
        (TYPE_MENTORING, 'Mentoring'),
        (TYPE_STRETCH_ASSIGNMENT, 'Stretch Assignment'),
        (TYPE_COACHING, 'Coaching'),
        (TYPE_CERTIFICATION, 'Certification'),
        (TYPE_JOB_ROTATION, 'Job Rotation'),
    ]

    STATUS_PLANNED = 'PLANNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PLANNED, 'Planned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    development_plan = models.ForeignKey(
        DevelopmentPlan, on_delete=models.CASCADE, related_name='activities'
    )
    activity_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED)
    completed_at = models.DateField(null=True, blank=True)
    outcome_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suc_dev_activity'
        ordering = ['target_date']

    def __str__(self):
        return f"{self.activity_type}: {self.title}"


class CriticalRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    position = models.OneToOneField(
        'core_hr.Position', on_delete=models.CASCADE, related_name='critical_role'
    )
    rationale = models.TextField(blank=True)
    risk_level = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')
    ], default='MEDIUM')
    time_to_fill_days = models.PositiveIntegerField(default=90)
    has_identified_successor = models.BooleanField(default=False)
    minimum_successors_required = models.PositiveIntegerField(default=2)
    review_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suc_critical_role'
        ordering = ['position__title']

    def __str__(self):
        return f"Critical: {self.position}"
