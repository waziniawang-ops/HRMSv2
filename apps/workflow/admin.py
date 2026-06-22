from django.contrib import admin
from .models import WorkflowRule, WorkflowRequest, WorkflowStep, WorkflowComment, WorkflowHistory, WorkflowAttachment, WorkflowActor


@admin.register(WorkflowRule)
class WorkflowRuleAdmin(admin.ModelAdmin):
    list_display = ['workflow_code', 'module_code', 'applies_to', 'is_active', 'version']
    list_filter = ['module_code', 'is_active']
    search_fields = ['workflow_code', 'description']


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0
    readonly_fields = ['acted_at', 'approver_user', 'status', 'action']


class WorkflowHistoryInline(admin.TabularInline):
    model = WorkflowHistory
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'actor', 'comment', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WorkflowRequest)
class WorkflowRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'module_code', 'object_type', 'object_id', 'status', 'maker_user', 'created_at']
    list_filter = ['status', 'module_code']
    search_fields = ['object_id', 'maker_user__username']
    raw_id_fields = ['maker_user', 'workflow_rule']
    inlines = [WorkflowStepInline, WorkflowHistoryInline]
    readonly_fields = ['submitted_at', 'completed_at', 'created_at', 'updated_at']


@admin.register(WorkflowAttachment)
class WorkflowAttachmentAdmin(admin.ModelAdmin):
    list_display = ['workflow_request', 'original_filename', 'uploaded_by', 'uploaded_at']
    raw_id_fields = ['workflow_request', 'uploaded_by']
    readonly_fields = ['uploaded_at']


@admin.register(WorkflowActor)
class WorkflowActorAdmin(admin.ModelAdmin):
    list_display = ['workflow_request', 'user', 'role', 'assigned_at']
    list_filter = ['role']
    raw_id_fields = ['workflow_request', 'user']
    readonly_fields = ['assigned_at']
