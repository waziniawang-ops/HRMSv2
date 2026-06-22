import uuid
from django.conf import settings
from django.db import models


class Course(models.Model):
    TYPE_ELEARNING = 'ELEARNING'
    TYPE_CLASSROOM = 'CLASSROOM'
    TYPE_BLENDED = 'BLENDED'
    TYPE_VIRTUAL = 'VIRTUAL'
    TYPE_ON_THE_JOB = 'ON_THE_JOB'

    TYPE_CHOICES = [
        (TYPE_ELEARNING, 'E-Learning'),
        (TYPE_CLASSROOM, 'Classroom'),
        (TYPE_BLENDED, 'Blended'),
        (TYPE_VIRTUAL, 'Virtual Instructor-Led'),
        (TYPE_ON_THE_JOB, 'On-the-Job Training'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_PUBLISHED = 'PUBLISHED'
    STATUS_ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    course_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    duration_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    passing_score = models.PositiveSmallIntegerField(default=70)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    is_mandatory = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    content_url = models.URLField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='courses_created'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='courses_approved'
    )
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lms_course'
        ordering = ['title']

    def __str__(self):
        return f"[{self.code}] {self.title}"


class LearningPath(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    courses = models.ManyToManyField(Course, through='LearningPathCourse', related_name='learning_paths')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='learning_paths_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lms_learning_path'
        ordering = ['name']

    def __str__(self):
        return self.name


class LearningPathCourse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learning_path = models.ForeignKey(LearningPath, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    sequence_order = models.PositiveIntegerField(default=1)
    is_required = models.BooleanField(default=True)

    class Meta:
        db_table = 'lms_path_course'
        unique_together = ['learning_path', 'course']
        ordering = ['sequence_order']


class AssignmentRule(models.Model):
    TRIGGER_NEW_HIRE = 'NEW_HIRE'
    TRIGGER_PROMOTION = 'PROMOTION'
    TRIGGER_ROLE_CHANGE = 'ROLE_CHANGE'
    TRIGGER_ANNUAL = 'ANNUAL'
    TRIGGER_MANUAL = 'MANUAL'

    TRIGGER_CHOICES = [
        (TRIGGER_NEW_HIRE, 'New Hire'),
        (TRIGGER_PROMOTION, 'Promotion'),
        (TRIGGER_ROLE_CHANGE, 'Role Change'),
        (TRIGGER_ANNUAL, 'Annual Renewal'),
        (TRIGGER_MANUAL, 'Manual Assignment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    trigger = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignment_rules'
    )
    learning_path = models.ForeignKey(
        LearningPath, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignment_rules'
    )
    target_job_family = models.ForeignKey(
        'core_hr.JobFamily', null=True, blank=True, on_delete=models.SET_NULL, related_name='assignment_rules'
    )
    target_grade = models.ForeignKey(
        'core_hr.Grade', null=True, blank=True, on_delete=models.SET_NULL, related_name='assignment_rules'
    )
    due_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lms_assignment_rule'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.trigger})"


class LearningAssignment(models.Model):
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_OVERDUE = 'OVERDUE'
    STATUS_WAIVED = 'WAIVED'

    STATUS_CHOICES = [
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_WAIVED, 'Waived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='learning_assignments'
    )
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments'
    )
    learning_path = models.ForeignKey(
        LearningPath, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments'
    )
    assignment_rule = models.ForeignKey(
        AssignmentRule, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments'
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ASSIGNED)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='learning_assignments_made'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lms_assignment'
        ordering = ['-created_at']

    def __str__(self):
        target = self.course or self.learning_path
        return f"{self.employee} assigned to {target}"


class CourseSession(models.Model):
    STATUS_SCHEDULED = 'SCHEDULED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='sessions')
    session_code = models.CharField(max_length=50, unique=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    venue = models.CharField(max_length=255, blank=True)
    facilitator_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lms_session'
        ordering = ['-start_datetime']

    def __str__(self):
        return f"{self.course.code} — {self.session_code}"


class Enrollment(models.Model):
    STATUS_ENROLLED = 'ENROLLED'
    STATUS_ATTENDED = 'ATTENDED'
    STATUS_ABSENT = 'ABSENT'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_ENROLLED, 'Enrolled'),
        (STATUS_ATTENDED, 'Attended'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='enrollments'
    )
    course_session = models.ForeignKey(
        CourseSession, on_delete=models.PROTECT, related_name='enrollments'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ENROLLED)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    attended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'lms_enrollment'
        unique_together = ['employee', 'course_session']

    def __str__(self):
        return f"{self.employee} enrolled in {self.course_session}"


class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='assessments'
    )
    attempt_number = models.PositiveSmallIntegerField(default=1)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    is_passed = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)
    answers_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'lms_assessment'
        ordering = ['-attempted_at']

    def save(self, *args, **kwargs):
        self.is_passed = self.score >= self.course.passing_score
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — {self.course.code} Attempt {self.attempt_number} ({self.score}%)"


class CourseCompletion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='course_completions'
    )
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='completions')
    completed_at = models.DateTimeField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hours_completed = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_valid = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lms_completion'
        unique_together = ['employee', 'course']

    def __str__(self):
        return f"{self.employee} completed {self.course.code}"


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    completion = models.OneToOneField(CourseCompletion, on_delete=models.CASCADE, related_name='certificate')
    certificate_number = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    file = models.FileField(upload_to='learning/certificates/', null=True, blank=True)

    class Meta:
        db_table = 'lms_certificate'

    def __str__(self):
        return f"Certificate {self.certificate_number}"


class TrainingRequest(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='training_requests'
    )
    training_title = models.CharField(max_length=500)
    provider = models.CharField(max_length=255, blank=True)
    reason = models.TextField()
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requested_dates = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='training_requests_reviewed'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lms_training_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} — {self.training_title}"


class SkillGap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='skill_gaps'
    )
    skill_name = models.CharField(max_length=255)
    required_level = models.PositiveSmallIntegerField(default=3)
    current_level = models.PositiveSmallIntegerField(default=1)
    gap = models.PositiveSmallIntegerField(default=0)
    recommended_course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='skill_gaps'
    )
    is_closed = models.BooleanField(default=False)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    assessed_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'lms_skill_gap'
        ordering = ['-gap']

    def save(self, *args, **kwargs):
        self.gap = max(0, self.required_level - self.current_level)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} — {self.skill_name} gap: {self.gap}"


class LearningTranscript(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='learning_transcript'
    )
    total_hours_completed = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_certificates_earned = models.PositiveIntegerField(default=0)
    mandatory_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_completion_date = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lms_transcript'

    def __str__(self):
        return f"Transcript: {self.employee} ({self.total_courses_completed} courses)"
