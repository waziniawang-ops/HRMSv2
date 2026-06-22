import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    code = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_role'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.display_name}"


class CustomUser(AbstractUser):
    USER_TYPE_INTERNAL = 'INTERNAL'
    USER_TYPE_EXTERNAL = 'EXTERNAL'
    USER_TYPE_SYSTEM = 'SYSTEM'
    USER_TYPE_CHOICES = [
        (USER_TYPE_INTERNAL, 'Internal'),
        (USER_TYPE_EXTERNAL, 'External'),
        (USER_TYPE_SYSTEM, 'System'),
    ]

    ROLE_SYSTEM_ADMIN = 'SYSTEM_ADMIN'
    ROLE_HR_ADMIN = 'HR_ADMIN'
    ROLE_HR_MAKER = 'HR_MAKER'
    ROLE_HR_CHECKER = 'HR_CHECKER'
    ROLE_HIRING_MANAGER = 'HIRING_MANAGER'
    ROLE_INTERVIEWER = 'INTERVIEWER'
    ROLE_RECRUITER = 'RECRUITER'
    ROLE_FINANCE_CHECKER = 'FINANCE_CHECKER'
    ROLE_TALENT_COMMITTEE = 'TALENT_COMMITTEE'
    ROLE_HR_PERFORMANCE = 'HR_PERFORMANCE'
    ROLE_LD_OFFICER = 'LD_OFFICER'
    ROLE_LD_CHECKER = 'LD_CHECKER'
    ROLE_MANAGER = 'MANAGER'
    ROLE_EMPLOYEE = 'EMPLOYEE'
    ROLE_APPLICANT = 'APPLICANT'
    ROLE_PAYROLL_OFFICER = 'PAYROLL_OFFICER'
    ROLE_HSE_OFFICER = 'HSE_OFFICER'
    ROLE_SERVICE_DESK_AGENT = 'SERVICE_DESK_AGENT'
    ROLE_ER_OFFICER = 'ER_OFFICER'
    ROLE_BENEFITS_ADMIN = 'BENEFITS_ADMIN'

    ROLE_CHOICES = [
        (ROLE_SYSTEM_ADMIN, 'System Admin'),
        (ROLE_HR_ADMIN, 'HR Admin'),
        (ROLE_HR_MAKER, 'HR Maker'),
        (ROLE_HR_CHECKER, 'HR Checker'),
        (ROLE_HIRING_MANAGER, 'Hiring Manager'),
        (ROLE_INTERVIEWER, 'Interviewer'),
        (ROLE_RECRUITER, 'Recruiter'),
        (ROLE_FINANCE_CHECKER, 'Finance Checker'),
        (ROLE_TALENT_COMMITTEE, 'Talent Committee'),
        (ROLE_HR_PERFORMANCE, 'HR Performance Officer'),
        (ROLE_LD_OFFICER, 'L&D Officer'),
        (ROLE_LD_CHECKER, 'L&D Checker'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_EMPLOYEE, 'Employee'),
        (ROLE_APPLICANT, 'Applicant'),
        (ROLE_PAYROLL_OFFICER, 'Payroll Officer'),
        (ROLE_HSE_OFFICER, 'HSE Officer'),
        (ROLE_SERVICE_DESK_AGENT, 'Service Desk Agent'),
        (ROLE_ER_OFFICER, 'Employee Relations Officer'),
        (ROLE_BENEFITS_ADMIN, 'Benefits Administrator'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default=USER_TYPE_INTERNAL)
    # primary_role kept for display / sidebar label / backward-compat
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    # dynamic M2M — one user may carry many roles simultaneously
    roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name='users',
        db_table='auth_user_roles',
        help_text='All system roles assigned to this user',
    )
    is_email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def role_codes(self) -> set:
        """Union of M2M roles + primary role (always effective)."""
        codes = set(r.code for r in self.roles.all())
        if self.role:
            codes.add(self.role)
        return codes

    def has_role(self, *roles) -> bool:
        return bool(self.role_codes.intersection(roles))

    @property
    def is_hr_staff(self):
        return self.has_role(
            self.ROLE_HR_MAKER, self.ROLE_HR_CHECKER,
            self.ROLE_HR_ADMIN, self.ROLE_SYSTEM_ADMIN,
        )

    @property
    def is_internal(self):
        return self.user_type == self.USER_TYPE_INTERNAL

    @property
    def is_applicant_user(self):
        return self.user_type == self.USER_TYPE_EXTERNAL


class EmailVerificationToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_email_verification_token'

    def __str__(self):
        return f"Token for {self.user.username}"
