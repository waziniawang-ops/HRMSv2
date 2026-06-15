import uuid
from django.conf import settings
from django.db import models


class JobRequisition(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_CHECKED = 'CHECKED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_CHECKED, 'Checked'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    REASON_REPLACEMENT = 'REPLACEMENT'
    REASON_EXPANSION = 'EXPANSION'
    REASON_SUCCESSION_GAP = 'SUCCESSION_GAP'
    REASON_NEW_ROLE = 'NEW_ROLE'

    REASON_CHOICES = [
        (REASON_REPLACEMENT, 'Replacement'),
        (REASON_EXPANSION, 'Expansion'),
        (REASON_SUCCESSION_GAP, 'Succession Gap'),
        (REASON_NEW_ROLE, 'New Role'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requisition_number = models.CharField(max_length=50, unique=True, blank=True)
    position = models.ForeignKey(
        'core_hr.Position', on_delete=models.PROTECT, related_name='requisitions'
    )
    hiring_reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    justification = models.TextField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requisitions_made'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    target_start_date = models.DateField(null=True, blank=True)
    budget_confirmed = models.BooleanField(default=False)
    headcount = models.PositiveIntegerField(default=1)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='requisitions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rec_job_requisition'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['position', 'status']),
        ]

    def __str__(self):
        return f"{self.requisition_number or str(self.id)[:8]} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            from django.utils import timezone
            self.requisition_number = f"REQ-{timezone.now().strftime('%Y')}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)


class JobPosting(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_POSTED = 'POSTED'
    STATUS_SCREENING = 'SCREENING'
    STATUS_INTERVIEW = 'INTERVIEW'
    STATUS_OFFER_DRAFT = 'OFFER_DRAFT'
    STATUS_OFFER_SUBMITTED = 'OFFER_SUBMITTED'
    STATUS_OFFER_APPROVED = 'OFFER_APPROVED'
    STATUS_OFFER_ACCEPTED = 'OFFER_ACCEPTED'
    STATUS_ONBOARDING_STARTED = 'ONBOARDING_STARTED'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_POSTED, 'Posted'),
        (STATUS_SCREENING, 'Screening'),
        (STATUS_INTERVIEW, 'Interview'),
        (STATUS_OFFER_DRAFT, 'Offer Draft'),
        (STATUS_OFFER_SUBMITTED, 'Offer Submitted'),
        (STATUS_OFFER_APPROVED, 'Offer Approved'),
        (STATUS_OFFER_ACCEPTED, 'Offer Accepted'),
        (STATUS_ONBOARDING_STARTED, 'Onboarding Started'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    VISIBILITY_INTERNAL = 'INTERNAL'
    VISIBILITY_EXTERNAL = 'EXTERNAL'
    VISIBILITY_BOTH = 'BOTH'
    VISIBILITY_CONFIDENTIAL = 'CONFIDENTIAL'

    VISIBILITY_CHOICES = [
        (VISIBILITY_INTERNAL, 'Internal Only'),
        (VISIBILITY_EXTERNAL, 'External Only'),
        (VISIBILITY_BOTH, 'Internal & External'),
        (VISIBILITY_CONFIDENTIAL, 'Confidential'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requisition = models.ForeignKey(JobRequisition, on_delete=models.PROTECT, related_name='postings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_BOTH)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    opening_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    screening_questions = models.JSONField(default=list, blank=True)
    eligibility_criteria = models.JSONField(default=dict, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='job_postings'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='job_postings_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rec_job_posting'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'visibility']),
        ]

    def __str__(self):
        return f"{self.title} [{self.status}]"


class Applicant(models.Model):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_LOCKED = 'LOCKED'
    STATUS_WITHDRAWN = 'WITHDRAWN'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_LOCKED, 'Locked'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='applicant'
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    profile_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    consent_version = models.CharField(max_length=50, default='1.0')
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    linkedin_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rec_applicant'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class ApplicantProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='profile')
    summary = models.TextField(blank=True)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rec_applicant_profile'

    def __str__(self):
        return f"Profile of {self.applicant}"


class Application(models.Model):
    STATUS_APPLIED = 'APPLIED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_SHORTLISTED = 'SHORTLISTED'
    STATUS_INTERVIEW_SCHEDULED = 'INTERVIEW_SCHEDULED'
    STATUS_INTERVIEW_COMPLETED = 'INTERVIEW_COMPLETED'
    STATUS_OFFERED = 'OFFERED'
    STATUS_OFFER_ACCEPTED = 'OFFER_ACCEPTED'
    STATUS_ONBOARDING = 'ONBOARDING'
    STATUS_HIRED = 'HIRED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_WITHDRAWN = 'WITHDRAWN'

    STATUS_CHOICES = [
        (STATUS_APPLIED, 'Applied'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_SHORTLISTED, 'Shortlisted'),
        (STATUS_INTERVIEW_SCHEDULED, 'Interview Scheduled'),
        (STATUS_INTERVIEW_COMPLETED, 'Interview Completed'),
        (STATUS_OFFERED, 'Offered'),
        (STATUS_OFFER_ACCEPTED, 'Offer Accepted'),
        (STATUS_ONBOARDING, 'Onboarding'),
        (STATUS_HIRED, 'Hired'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_posting = models.ForeignKey(JobPosting, on_delete=models.PROTECT, related_name='applications')
    applicant = models.ForeignKey(Applicant, on_delete=models.PROTECT, related_name='applications')
    stage = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_APPLIED)
    cover_letter = models.TextField(blank=True)
    screening_answers = models.JSONField(default=dict, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rec_application'
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['applicant', 'job_posting'],
                name='uq_applicant_per_posting'
            )
        ]
        indexes = [
            models.Index(fields=['job_posting', 'stage']),
        ]

    def __str__(self):
        return f"{self.applicant} → {self.job_posting.title} [{self.stage}]"


class Interview(models.Model):
    TYPE_PHONE = 'PHONE'
    TYPE_VIDEO = 'VIDEO'
    TYPE_ONSITE = 'ONSITE'
    TYPE_PANEL = 'PANEL'
    TYPE_TECHNICAL = 'TECHNICAL'

    TYPE_CHOICES = [
        (TYPE_PHONE, 'Phone Screen'),
        (TYPE_VIDEO, 'Video'),
        (TYPE_ONSITE, 'On-Site'),
        (TYPE_PANEL, 'Panel'),
        (TYPE_TECHNICAL, 'Technical'),
    ]

    STATUS_SCHEDULED = 'SCHEDULED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_NO_SHOW = 'NO_SHOW'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW, 'No Show'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    interview_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_VIDEO)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    scheduled_at = models.DateTimeField()
    location_or_link = models.CharField(max_length=500, blank=True)
    panel = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='panel_interviews'
    )
    round_number = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='interviews_created'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rec_interview'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Round {self.round_number} [{self.interview_type}] for {self.application}"


class InterviewFeedback(models.Model):
    RECOMMENDATION_PROCEED = 'PROCEED'
    RECOMMENDATION_HOLD = 'HOLD'
    RECOMMENDATION_REJECT = 'REJECT'

    RECOMMENDATION_CHOICES = [
        (RECOMMENDATION_PROCEED, 'Proceed'),
        (RECOMMENDATION_HOLD, 'Hold'),
        (RECOMMENDATION_REJECT, 'Reject'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='feedbacks')
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='interview_feedbacks'
    )
    overall_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    section_scores = models.JSONField(default=dict, blank=True)
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES)
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        db_table = 'rec_interview_feedback'
        unique_together = [['interview', 'interviewer']]

    def __str__(self):
        return f"Feedback by {self.interviewer} for {self.interview}"


class Offer(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_SENT = 'SENT'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_DECLINED = 'DECLINED'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_REVOKED = 'REVOKED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_SENT, 'Sent'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_REVOKED, 'Revoked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer_number = models.CharField(max_length=50, unique=True, blank=True)
    application = models.ForeignKey(Application, on_delete=models.PROTECT, related_name='offers')
    position = models.ForeignKey('core_hr.Position', on_delete=models.PROTECT)
    grade = models.ForeignKey('core_hr.Grade', on_delete=models.PROTECT)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.JSONField(default=dict, blank=True)
    total_package = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    employment_type = models.CharField(max_length=30, default='FULL_TIME')
    start_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    expiry_date = models.DateField(null=True, blank=True)
    offer_letter = models.FileField(upload_to='offer_letters/', null=True, blank=True)
    negotiation_notes = models.TextField(blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_reason = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='offers'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='offers_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rec_offer'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.offer_number or str(self.id)[:8]} [{self.status}]"

    def save(self, *args, **kwargs):
        if not self.offer_number:
            from django.utils import timezone
            self.offer_number = f"OFF-{timezone.now().strftime('%Y')}-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)


class ApplicantDocument(models.Model):
    DOC_RESUME = 'RESUME'
    DOC_COVER_LETTER = 'COVER_LETTER'
    DOC_ACADEMIC = 'ACADEMIC_CERT'
    DOC_ID = 'IDENTITY'
    DOC_PORTFOLIO = 'PORTFOLIO'
    DOC_OTHER = 'OTHER'

    DOC_TYPE_CHOICES = [
        (DOC_RESUME, 'Resume / CV'),
        (DOC_COVER_LETTER, 'Cover Letter'),
        (DOC_ACADEMIC, 'Academic Certificate'),
        (DOC_ID, 'Identity Document'),
        (DOC_PORTFOLIO, 'Portfolio'),
        (DOC_OTHER, 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES, default=DOC_OTHER)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='applicant_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rec_applicant_document'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.applicant.full_name} — {self.doc_type}"
