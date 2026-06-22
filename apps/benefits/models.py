import uuid
from django.conf import settings
from django.db import models


class BenefitPlan(models.Model):
    CATEGORY_MEDICAL = 'MEDICAL'
    CATEGORY_DENTAL = 'DENTAL'
    CATEGORY_VISION = 'VISION'
    CATEGORY_LIFE = 'LIFE'
    CATEGORY_PENSION = 'PENSION'
    CATEGORY_EDUCATION = 'EDUCATION'
    CATEGORY_RECREATION = 'RECREATION'
    CATEGORY_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CATEGORY_MEDICAL, 'Medical'),
        (CATEGORY_DENTAL, 'Dental'),
        (CATEGORY_VISION, 'Vision'),
        (CATEGORY_LIFE, 'Life Insurance'),
        (CATEGORY_PENSION, 'Pension / Retirement'),
        (CATEGORY_EDUCATION, 'Education'),
        (CATEGORY_RECREATION, 'Recreation'),
        (CATEGORY_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    provider = models.CharField(max_length=255, blank=True)
    coverage_details = models.JSONField(default=dict)
    employee_contribution_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0,
        help_text='Employee contribution as a fraction (0-1)'
    )
    employer_contribution_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0,
        help_text='Employer contribution as a fraction (0-1)'
    )
    max_dependents = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'benefits_plan'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class EligibilityRule(models.Model):
    EMPLOYMENT_FULL_TIME = 'FULL_TIME'
    EMPLOYMENT_PART_TIME = 'PART_TIME'
    EMPLOYMENT_CONTRACT = 'CONTRACT'
    EMPLOYMENT_INTERN = 'INTERN'

    EMPLOYMENT_CHOICES = [
        (EMPLOYMENT_FULL_TIME, 'Full Time'),
        (EMPLOYMENT_PART_TIME, 'Part Time'),
        (EMPLOYMENT_CONTRACT, 'Contract'),
        (EMPLOYMENT_INTERN, 'Intern'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(BenefitPlan, on_delete=models.CASCADE, related_name='eligibility_rules')
    grade = models.ForeignKey(
        'core_hr.Grade', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='benefit_eligibility_rules'
    )
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, blank=True)
    min_service_months = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'benefits_eligibility_rule'
        ordering = ['plan', 'grade']

    def __str__(self):
        return f"{self.plan} | Grade: {self.grade or 'All'} | Type: {self.employment_type or 'All'}"


class BenefitEnrollment(models.Model):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_ENDED = 'ENDED'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_ENDED, 'Ended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='benefit_enrollments'
    )
    plan = models.ForeignKey(BenefitPlan, on_delete=models.PROTECT, related_name='enrollments')
    enrollment_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    employee_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employer_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='benefit_enrollments_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'benefits_enrollment'
        unique_together = [['employee', 'plan']]
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.employee} | {self.plan} [{self.status}]"


class BenefitDependent(models.Model):
    RELATIONSHIP_SPOUSE = 'SPOUSE'
    RELATIONSHIP_CHILD = 'CHILD'
    RELATIONSHIP_PARENT = 'PARENT'
    RELATIONSHIP_SIBLING = 'SIBLING'
    RELATIONSHIP_OTHER = 'OTHER'

    RELATIONSHIP_CHOICES = [
        (RELATIONSHIP_SPOUSE, 'Spouse'),
        (RELATIONSHIP_CHILD, 'Child'),
        (RELATIONSHIP_PARENT, 'Parent'),
        (RELATIONSHIP_SIBLING, 'Sibling'),
        (RELATIONSHIP_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(BenefitEnrollment, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'benefits_dependent'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.relationship}) — {self.enrollment}"


class BenefitClaimReference(models.Model):
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_REIMBURSED = 'REIMBURSED'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_REIMBURSED, 'Reimbursed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(BenefitEnrollment, on_delete=models.PROTECT, related_name='claims')
    claim_reference = models.CharField(max_length=100, blank=True)
    claim_date = models.DateField()
    amount_claimed = models.DecimalField(max_digits=12, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    description = models.TextField(blank=True)
    document = models.FileField(null=True, blank=True, upload_to='benefits/claims/')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='benefit_claims_approved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'benefits_claim_reference'
        ordering = ['-claim_date']

    def __str__(self):
        return f"Claim: {self.enrollment} | {self.claim_date} | {self.amount_claimed}"


class BenefitCost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(BenefitEnrollment, on_delete=models.PROTECT, related_name='costs')
    period_start = models.DateField()
    period_end = models.DateField()
    employee_amount = models.DecimalField(max_digits=12, decimal_places=2)
    employer_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payroll_run = models.ForeignKey(
        'payroll.PayrollRun', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='benefit_costs'
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'benefits_cost'
        ordering = ['-period_start']

    def __str__(self):
        return f"Cost: {self.enrollment} | {self.period_start} - {self.period_end}"
