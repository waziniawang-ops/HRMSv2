import uuid
from django.conf import settings
from django.db import models


class SkillCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'skills_category'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        SkillCategory, on_delete=models.PROTECT, related_name='skills'
    )
    description = models.TextField(blank=True)
    aliases = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skills_skill'
        ordering = ['name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProficiencyScale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    level = models.PositiveIntegerField(unique=True)
    behavioural_indicators = models.TextField(blank=True)

    class Meta:
        db_table = 'skills_proficiency_scale'
        ordering = ['level']

    def __str__(self):
        return f"{self.level} - {self.name}"


class JobSkillRequirement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        'core_hr.Job', on_delete=models.CASCADE, related_name='skill_requirements'
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name='job_requirements'
    )
    required_level = models.ForeignKey(
        ProficiencyScale, on_delete=models.PROTECT, related_name='job_requirements'
    )
    is_mandatory = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'skills_job_requirement'
        unique_together = [['job', 'skill']]

    def __str__(self):
        return f"{self.job.job_title} — {self.skill.name} [{self.required_level.name}]"


class EmployeeSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='skills'
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name='employee_assessments'
    )
    proficiency = models.ForeignKey(
        ProficiencyScale, on_delete=models.PROTECT, related_name='employee_skills'
    )
    is_self_assessed = models.BooleanField(default=True)
    is_endorsed = models.BooleanField(default=False)
    endorsed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='skill_endorsements'
    )
    endorsed_at = models.DateTimeField(null=True, blank=True)
    evidence_description = models.TextField(blank=True)
    assessed_date = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'skills_employee_skill'
        unique_together = [['employee', 'skill']]

    def __str__(self):
        return f"{self.employee} — {self.skill.name} [{self.proficiency.name}]"


class SkillEvidence(models.Model):
    TYPE_CERTIFICATE = 'CERTIFICATE'
    TYPE_PROJECT = 'PROJECT'
    TYPE_TRAINING = 'TRAINING_COMPLETION'
    TYPE_ASSESSMENT = 'ASSESSMENT'
    TYPE_ENDORSEMENT = 'ENDORSEMENT'
    TYPE_PUBLICATION = 'PUBLICATION'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_CERTIFICATE, 'Certificate'),
        (TYPE_PROJECT, 'Project'),
        (TYPE_TRAINING, 'Training Completion'),
        (TYPE_ASSESSMENT, 'Assessment'),
        (TYPE_ENDORSEMENT, 'Endorsement'),
        (TYPE_PUBLICATION, 'Publication'),
        (TYPE_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_skill = models.ForeignKey(
        EmployeeSkill, on_delete=models.CASCADE, related_name='evidence_items'
    )
    title = models.CharField(max_length=255)
    evidence_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    document = models.FileField(upload_to='skills/evidence/', null=True, blank=True)
    url = models.CharField(max_length=500, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='skill_evidence_verified'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skills_evidence'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.evidence_type})"


class SkillGapAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='skill_gap_analyses'
    )
    job = models.ForeignKey(
        'core_hr.Job', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='skill_gap_analyses'
    )
    analysis_date = models.DateField(auto_now_add=True)
    overall_match_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gaps_summary = models.JSONField(default=list, blank=True)
    recommended_training = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skills_gap_analysis'
        ordering = ['-created_at']

    def __str__(self):
        job_name = self.job.job_title if self.job else 'N/A'
        return f"Gap Analysis: {self.employee} vs {job_name} ({self.analysis_date})"


class SkillGap(models.Model):
    STATUS_OPEN = 'OPEN'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_CLOSED, 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='individual_skill_gaps'
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE, related_name='gaps'
    )
    required_level = models.ForeignKey(
        ProficiencyScale, on_delete=models.PROTECT, related_name='required_for_gaps'
    )
    current_level = models.ForeignKey(
        ProficiencyScale, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='current_for_gaps'
    )
    gap_size = models.IntegerField(null=True, blank=True)
    recommended_course = models.ForeignKey(
        'learning.Course', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='skill_gaps_recommended'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    identified_at = models.DateTimeField(auto_now_add=True)
    target_closure_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'skills_gap'
        unique_together = [['employee', 'skill']]

    def __str__(self):
        return f"{self.employee} — {self.skill.name} gap [{self.status}]"

    def save(self, *args, **kwargs):
        if self.required_level and self.current_level:
            self.gap_size = self.required_level.level - self.current_level.level
        elif self.required_level:
            self.gap_size = self.required_level.level
        super().save(*args, **kwargs)
