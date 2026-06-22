import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class ClaimType(models.Model):
    CATEGORY_MEDICAL = 'MEDICAL'
    CATEGORY_TRANSPORT = 'TRANSPORT'
    CATEGORY_MEALS = 'MEALS'
    CATEGORY_ACCOMMODATION = 'ACCOMMODATION'
    CATEGORY_TRAINING = 'TRAINING'
    CATEGORY_PROFESSIONAL_DEV = 'PROFESSIONAL_DEV'
    CATEGORY_MISCELLANEOUS = 'MISCELLANEOUS'

    CATEGORY_CHOICES = [
        (CATEGORY_MEDICAL, 'Medical'),
        (CATEGORY_TRANSPORT, 'Transport'),
        (CATEGORY_MEALS, 'Meals'),
        (CATEGORY_ACCOMMODATION, 'Accommodation'),
        (CATEGORY_TRAINING, 'Training'),
        (CATEGORY_PROFESSIONAL_DEV, 'Professional Development'),
        (CATEGORY_MISCELLANEOUS, 'Miscellaneous'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    max_amount_per_claim = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_amount_per_year = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requires_receipt = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'claims_claim_type'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ExpensePolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)
    mileage_rate_per_km = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    per_diem_domestic = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    per_diem_international = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    meal_allowance_breakfast = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    meal_allowance_lunch = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    meal_allowance_dinner = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rules = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='expense_policies_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'claims_expense_policy'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.name} (from {self.effective_date})"


class ClaimRequest(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_IN_REVIEW = 'IN_REVIEW'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_PAID = 'PAID'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_IN_REVIEW, 'In Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim_number = models.CharField(max_length=30, unique=True, blank=True)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='claim_requests'
    )
    claim_title = models.CharField(max_length=255)
    period_start = models.DateField()
    period_end = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='BND')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='claims_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='claims_paid'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'claims_claim_request'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
        ]

    def __str__(self):
        return f"{self.claim_number} - {self.claim_title}"

    def save(self, *args, **kwargs):
        if not self.claim_number:
            year = timezone.now().year
            last = ClaimRequest.objects.filter(created_at__year=year).order_by('-claim_number').first()
            try:
                seq = int(last.claim_number.split('-')[-1]) + 1 if last and last.claim_number else 1
            except (ValueError, IndexError, AttributeError):
                seq = 1
            self.claim_number = f"CLM-{year}-{seq:05d}"
        super().save(*args, **kwargs)


class ClaimLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(
        ClaimRequest, on_delete=models.CASCADE, related_name='lines'
    )
    claim_type = models.ForeignKey(
        ClaimType, on_delete=models.PROTECT, related_name='claim_lines'
    )
    description = models.CharField(max_length=500)
    expense_date = models.DateField()
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='BND')
    is_approved = models.BooleanField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = 'claims_claim_line'
        ordering = ['expense_date']

    def __str__(self):
        return f"{self.claim.claim_number} - {self.description}"


class ClaimReceipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(
        ClaimRequest, on_delete=models.CASCADE, related_name='receipts'
    )
    line = models.ForeignKey(
        ClaimLine, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='receipts'
    )
    file = models.FileField(upload_to='claims/receipts/')
    receipt_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'claims_claim_receipt'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Receipt for {self.claim.claim_number} ({self.receipt_date})"


class TravelRequest(models.Model):
    TRAVEL_DOMESTIC = 'DOMESTIC'
    TRAVEL_INTERNATIONAL = 'INTERNATIONAL'

    TRAVEL_TYPE_CHOICES = [
        (TRAVEL_DOMESTIC, 'Domestic'),
        (TRAVEL_INTERNATIONAL, 'International'),
    ]

    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_number = models.CharField(max_length=30, unique=True, blank=True)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.PROTECT, related_name='travel_requests'
    )
    title = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    country_of_travel = models.CharField(max_length=100, blank=True)
    purpose = models.TextField()
    departure_date = models.DateField()
    return_date = models.DateField()
    travel_type = models.CharField(max_length=20, choices=TRAVEL_TYPE_CHOICES, default=TRAVEL_DOMESTIC)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='BND')
    advance_requested = models.BooleanField(default=False)
    advance_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    advance_settled = models.BooleanField(default=False)
    itinerary = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='travel_requests_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'claims_travel_request'
        ordering = ['-departure_date']

    def __str__(self):
        return f"{self.request_number} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            year = timezone.now().year
            last = TravelRequest.objects.filter(created_at__year=year).order_by('-request_number').first()
            try:
                seq = int(last.request_number.split('-')[-1]) + 1 if last and last.request_number else 1
            except (ValueError, IndexError, AttributeError):
                seq = 1
            self.request_number = f"TRV-{year}-{seq:05d}"
        super().save(*args, **kwargs)
