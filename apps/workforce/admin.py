from django.contrib import admin
from .models import (
    WorkforcePlan, AttendancePolicy, AttendanceLog, LeaveType, LeaveBalance,
    LeaveRequest, OvertimeRequest, Roster, Transfer, Separation,
)


@admin.register(WorkforcePlan)
class WorkforcePlanAdmin(admin.ModelAdmin):
    list_display = ['plan_year', 'org_unit', 'status', 'headcount_current', 'headcount_target', 'prepared_by']
    list_filter = ['status', 'plan_year']
    search_fields = ['org_unit__name']
    raw_id_fields = ['org_unit', 'prepared_by', 'approved_by']


@admin.register(AttendancePolicy)
class AttendancePolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'policy_type', 'standard_hours_per_day', 'grace_minutes', 'is_active']
    list_filter = ['policy_type', 'is_active']


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'clock_in', 'clock_out', 'hours_worked', 'is_present', 'is_late', 'source']
    list_filter = ['is_present', 'is_late', 'source', 'date']
    search_fields = ['employee__person__legal_name']
    raw_id_fields = ['employee']


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'days_per_year', 'is_paid', 'carry_forward', 'is_active']
    list_filter = ['is_paid', 'carry_forward', 'is_active']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'entitled_days', 'used_days', 'pending_days']
    list_filter = ['year', 'leave_type']
    raw_id_fields = ['employee', 'leave_type']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status']
    list_filter = ['status', 'leave_type']
    raw_id_fields = ['employee', 'leave_type', 'reviewed_by']


@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'hours_requested', 'hours_approved', 'status']
    list_filter = ['status']
    raw_id_fields = ['employee', 'approved_by']


@admin.register(Roster)
class RosterAdmin(admin.ModelAdmin):
    list_display = ['employee', 'shift_name', 'shift_start', 'shift_end', 'effective_date', 'end_date']
    raw_id_fields = ['employee', 'created_by']


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['employee', 'movement_type', 'from_position', 'to_position', 'effective_date', 'status']
    list_filter = ['status', 'movement_type']
    raw_id_fields = ['employee', 'from_position', 'to_position', 'from_grade', 'to_grade', 'initiated_by', 'approved_by', 'workflow_request']


@admin.register(Separation)
class SeparationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'separation_type', 'notice_date', 'last_working_date', 'status']
    list_filter = ['status', 'separation_type']
    raw_id_fields = ['employee', 'initiated_by', 'approved_by']
