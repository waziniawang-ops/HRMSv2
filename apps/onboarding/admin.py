from django.contrib import admin
from .models import OnboardingTemplate, OnboardingCase, OnboardingTask, OnboardingDocument


@admin.register(OnboardingTemplate)
class OnboardingTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


class OnboardingTaskInline(admin.TabularInline):
    model = OnboardingTask
    extra = 0
    fields = ['task_code', 'title', 'is_required', 'order', 'status', 'completed_at', 'hr_verified']
    readonly_fields = ['completed_at']


@admin.register(OnboardingCase)
class OnboardingCaseAdmin(admin.ModelAdmin):
    list_display = ['offer', 'status', 'target_start_date', 'assigned_hr', 'completion_percentage']
    list_filter = ['status']
    search_fields = ['offer__application__applicant__full_name']
    raw_id_fields = ['offer', 'candidate_person', 'template', 'assigned_hr']
    inlines = [OnboardingTaskInline]


@admin.register(OnboardingDocument)
class OnboardingDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type', 'onboarding_case', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified']
    raw_id_fields = ['onboarding_case', 'task', 'uploaded_by', 'verified_by']
