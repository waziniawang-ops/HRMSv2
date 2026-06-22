import uuid
from django.conf import settings
from django.db import models


class PerformanceCycle(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_GOAL_SETTING = 'GOAL_SETTING'
    STATUS_MID_YEAR = 'MID_YEAR'
    STATUS_YEAR_END = 'YEAR_END'
    STATUS_CALIBRATION = 'CALIBRATION'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_GOAL_SETTING, 'Goal Setting'),
        (STATUS_MID_YEAR, 'Mid-Year Review'),
        (STATUS_YEAR_END, 'Year-End Review'),
        (STATUS_CALIBRATION, 'Calibration'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CLOSED, 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    cycle_year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    goal_setting_start = models.DateField()
    goal_setting_end = models.DateField()
    mid_year_start = models.DateField(null=True, blank=True)
    mid_year_end = models.DateField(null=True, blank=True)
    year_end_start = models.DateField()
    year_end_end = models.DateField()
    calibration_start = models.DateField(null=True, blank=True)
    calibration_end = models.DateField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perf_cycle'
        ordering = ['-cycle_year']

    def __str__(self):
        return f"{self.name} ({self.cycle_year})"


class CompetencyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_competency_model'
        ordering = ['name']

    def __str__(self):
        return self.name


class Competency(models.Model):
    LEVEL_CHOICES = [(i, f'Level {i}') for i in range(1, 6)]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(CompetencyModel, on_delete=models.CASCADE, related_name='competencies')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    max_level = models.PositiveSmallIntegerField(default=5)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_competency'
        ordering = ['name']

    def __str__(self):
        return f"{self.model.name} — {self.name}"


class GoalPlan(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_MANAGER_APPROVED = 'MANAGER_APPROVED'
    STATUS_HR_APPROVED = 'HR_APPROVED'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted for Approval'),
        (STATUS_MANAGER_APPROVED, 'Manager Approved'),
        (STATUS_HR_APPROVED, 'HR Approved'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='goal_plans'
    )
    cycle = models.ForeignKey(
        PerformanceCycle, on_delete=models.PROTECT, related_name='goal_plans'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    overall_weight_total = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='goal_plans_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perf_goal_plan'
        unique_together = ['employee', 'cycle']
        ordering = ['-created_at']

    def __str__(self):
        return f"Goal Plan: {self.employee} — {self.cycle}"


class Goal(models.Model):
    CATEGORY_KPI = 'KPI'
    CATEGORY_PROJECT = 'PROJECT'
    CATEGORY_DEVELOPMENT = 'DEVELOPMENT'
    CATEGORY_BEHAVIORAL = 'BEHAVIORAL'

    CATEGORY_CHOICES = [
        (CATEGORY_KPI, 'KPI / Quantitative'),
        (CATEGORY_PROJECT, 'Project'),
        (CATEGORY_DEVELOPMENT, 'Development'),
        (CATEGORY_BEHAVIORAL, 'Behavioral'),
    ]

    STATUS_NOT_STARTED = 'NOT_STARTED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, 'Not Started'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal_plan = models.ForeignKey(GoalPlan, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_KPI)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    target_value = models.CharField(max_length=255, blank=True)
    unit_of_measure = models.CharField(max_length=100, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_STARTED)
    completion_percentage = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perf_goal'
        ordering = ['-weight', 'title']

    def __str__(self):
        return self.title


class GoalProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='progress_updates')
    update_date = models.DateField()
    current_value = models.CharField(max_length=255, blank=True)
    completion_percentage = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='goal_progress_recorded'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_goal_progress'
        ordering = ['-update_date']

    def __str__(self):
        return f"{self.goal} — {self.update_date} ({self.completion_percentage}%)"


class ReviewForm(models.Model):
    TYPE_SELF = 'SELF'
    TYPE_MANAGER = 'MANAGER'
    TYPE_PEER = 'PEER'
    TYPE_360 = '360'

    TYPE_CHOICES = [
        (TYPE_SELF, 'Self Assessment'),
        (TYPE_MANAGER, 'Manager Review'),
        (TYPE_PEER, 'Peer Review'),
        (TYPE_360, '360 Degree Review'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_ACKNOWLEDGED = 'ACKNOWLEDGED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_ACKNOWLEDGED, 'Acknowledged'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle = models.ForeignKey(PerformanceCycle, on_delete=models.PROTECT, related_name='review_forms')
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='review_forms'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='review_forms_as_reviewer'
    )
    review_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    overall_rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    strengths_comments = models.TextField(blank=True)
    improvement_comments = models.TextField(blank=True)
    overall_comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perf_review_form'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.review_type} Review: {self.employee} ({self.cycle})"


class ReviewRating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review_form = models.ForeignKey(ReviewForm, on_delete=models.CASCADE, related_name='ratings')
    competency = models.ForeignKey(
        Competency, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='review_ratings'
    )
    goal = models.ForeignKey(
        Goal, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='review_ratings'
    )
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_review_rating'

    def __str__(self):
        return f"Rating {self.rating} on {self.review_form}"


class CalibrationSession(models.Model):
    STATUS_SCHEDULED = 'SCHEDULED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle = models.ForeignKey(PerformanceCycle, on_delete=models.PROTECT, related_name='calibration_sessions')
    org_unit = models.ForeignKey(
        'core_hr.OrgUnit', on_delete=models.PROTECT, related_name='calibration_sessions'
    )
    session_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='calibration_sessions_facilitated'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_calibration_session'
        ordering = ['-session_date']

    def __str__(self):
        return f"Calibration: {self.org_unit} — {self.session_date}"


class CalibratedRating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CalibrationSession, on_delete=models.CASCADE, related_name='calibrated_ratings')
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='calibrated_ratings'
    )
    pre_calibration_rating = models.DecimalField(max_digits=4, decimal_places=2)
    calibrated_rating = models.DecimalField(max_digits=4, decimal_places=2)
    calibration_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_calibrated_rating'
        unique_together = ['session', 'employee']

    def __str__(self):
        return f"Calibrated: {self.employee} — {self.calibrated_rating}"


class FinalOutcome(models.Model):
    OUTCOME_EXCEEDS = 'EXCEEDS'
    OUTCOME_MEETS = 'MEETS'
    OUTCOME_PARTIALLY = 'PARTIALLY'
    OUTCOME_BELOW = 'BELOW'

    OUTCOME_CHOICES = [
        (OUTCOME_EXCEEDS, 'Exceeds Expectations'),
        (OUTCOME_MEETS, 'Meets Expectations'),
        (OUTCOME_PARTIALLY, 'Partially Meets'),
        (OUTCOME_BELOW, 'Below Expectations'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle = models.ForeignKey(PerformanceCycle, on_delete=models.PROTECT, related_name='final_outcomes')
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='performance_outcomes'
    )
    final_rating = models.DecimalField(max_digits=4, decimal_places=2)
    outcome_label = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    eligible_for_increment = models.BooleanField(default=False)
    eligible_for_bonus = models.BooleanField(default=False)
    increment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='final_outcomes_approved'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perf_final_outcome'
        unique_together = ['cycle', 'employee']
        ordering = ['-created_at']

    def __str__(self):
        return f"Final Outcome: {self.employee} — {self.outcome_label} ({self.final_rating})"


class ImprovementPlan(models.Model):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_FAILED, 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='improvement_plans'
    )
    cycle = models.ForeignKey(
        PerformanceCycle, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='improvement_plans'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    objectives = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    outcome_notes = models.TextField(blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='improvement_plans_initiated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perf_improvement_plan'
        ordering = ['-created_at']

    def __str__(self):
        return f"PIP: {self.employee} ({self.start_date} to {self.end_date})"


class CheckIn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='check_ins'
    )
    manager = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='check_ins_as_manager'
    )
    cycle = models.ForeignKey(
        PerformanceCycle, null=True, blank=True, on_delete=models.SET_NULL, related_name='check_ins'
    )
    check_in_date = models.DateField()
    goals_discussed = models.JSONField(default=list, help_text='List of goal IDs discussed')
    achievements = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    next_steps = models.TextField(blank=True)
    overall_rating = models.CharField(
        max_length=20, blank=True,
        choices=[('ON_TRACK', 'On Track'), ('AT_RISK', 'At Risk'), ('OFF_TRACK', 'Off Track')]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_check_in'
        ordering = ['-check_in_date']

    def __str__(self):
        return f"Check-in: {self.employee} with {self.manager} on {self.check_in_date}"


class CyclePopulation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cycle = models.ForeignKey(
        PerformanceCycle, on_delete=models.CASCADE, related_name='population'
    )
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='performance_cycle_memberships'
    )
    is_eligible = models.BooleanField(default=True)
    inclusion_reason = models.CharField(max_length=255, blank=True)
    exclusion_reason = models.CharField(max_length=255, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'perf_cycle_population'
        unique_together = [['cycle', 'employee']]

    def __str__(self):
        return f"{self.employee} in {self.cycle}"
