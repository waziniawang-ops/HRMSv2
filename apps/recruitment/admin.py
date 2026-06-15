from django.contrib import admin
from .models import (
    JobRequisition, JobPosting, Applicant, ApplicantProfile,
    Application, Interview, InterviewFeedback, Offer,
)


@admin.register(JobRequisition)
class JobRequisitionAdmin(admin.ModelAdmin):
    list_display = ['requisition_number', 'position', 'hiring_reason', 'status', 'requested_by', 'created_at']
    list_filter = ['status', 'hiring_reason']
    search_fields = ['requisition_number', 'justification']
    raw_id_fields = ['position', 'requested_by']


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'requisition', 'visibility', 'status', 'opening_date', 'closing_date']
    list_filter = ['status', 'visibility']
    search_fields = ['title']
    raw_id_fields = ['requisition', 'created_by']


class ApplicantProfileInline(admin.StackedInline):
    model = ApplicantProfile
    extra = 0


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'profile_status', 'created_at']
    list_filter = ['profile_status']
    search_fields = ['full_name', 'email']
    inlines = [ApplicantProfileInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job_posting', 'stage', 'score', 'applied_at']
    list_filter = ['stage']
    search_fields = ['applicant__full_name', 'job_posting__title']
    raw_id_fields = ['applicant', 'job_posting']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['application', 'interview_type', 'status', 'scheduled_at', 'round_number']
    list_filter = ['interview_type', 'status']
    raw_id_fields = ['application', 'created_by']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['offer_number', 'application', 'status', 'basic_salary', 'start_date', 'created_at']
    list_filter = ['status']
    search_fields = ['offer_number']
    raw_id_fields = ['application', 'position', 'grade', 'created_by']
