from rest_framework import serializers
from .models import (
    WorkforcePlan, AttendancePolicy, AttendanceLog, LeaveType, LeaveBalance,
    LeaveRequest, OvertimeRequest, Roster, Transfer, Separation,
    ShiftTemplate, AttendanceException, HolidayCalendar, HolidayCalendarEntry,
    LeavePolicy, LeaveDocument,
)


class WorkforcePlanSerializer(serializers.ModelSerializer):
    org_unit_name = serializers.CharField(source='org_unit.name', read_only=True)
    prepared_by_display = serializers.CharField(source='prepared_by.get_full_name', read_only=True)

    class Meta:
        model = WorkforcePlan
        fields = [
            'id', 'plan_year', 'org_unit', 'org_unit_name', 'prepared_by', 'prepared_by_display',
            'status', 'headcount_current', 'headcount_target', 'attrition_forecast',
            'notes', 'approved_by', 'approved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'prepared_by', 'approved_by', 'approved_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['prepared_by'] = self.context['request'].user
        return super().create(validated_data)


class AttendancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendancePolicy
        fields = ['id', 'name', 'policy_type', 'standard_hours_per_day', 'grace_minutes', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AttendanceLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = AttendanceLog
        fields = [
            'id', 'employee', 'employee_name', 'date', 'clock_in', 'clock_out',
            'hours_worked', 'is_present', 'is_late', 'source', 'remarks', 'created_at',
        ]
        read_only_fields = ['id', 'hours_worked', 'created_at']


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = [
            'id', 'code', 'name', 'days_per_year', 'is_paid', 'requires_approval',
            'carry_forward', 'max_carry_days', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    available_days = serializers.ReadOnlyField()

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'leave_type', 'leave_type_name', 'year',
            'entitled_days', 'used_days', 'pending_days', 'carried_forward',
            'available_days', 'updated_at',
        ]
        read_only_fields = ['id', 'used_days', 'pending_days', 'updated_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'days_requested', 'reason', 'status',
            'reviewed_by', 'reviewed_at', 'review_notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class OvertimeRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = OvertimeRequest
        fields = [
            'id', 'employee', 'employee_name', 'date', 'hours_requested', 'hours_approved',
            'reason', 'status', 'approved_by', 'approved_at', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'hours_approved', 'approved_by', 'approved_at', 'created_at']


class RosterSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = Roster
        fields = [
            'id', 'employee', 'employee_name', 'shift_name', 'shift_start', 'shift_end',
            'effective_date', 'end_date', 'notes', 'created_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TransferSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    from_position_title = serializers.CharField(source='from_position.title', read_only=True)
    to_position_title = serializers.CharField(source='to_position.title', read_only=True)

    class Meta:
        model = Transfer
        fields = [
            'id', 'employee', 'employee_name', 'movement_type',
            'from_position', 'from_position_title', 'to_position', 'to_position_title',
            'from_grade', 'to_grade', 'effective_date', 'reason', 'status',
            'initiated_by', 'approved_by', 'approved_at', 'workflow_request',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'initiated_by', 'status', 'approved_by', 'approved_at',
            'workflow_request', 'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        validated_data['initiated_by'] = self.context['request'].user
        return super().create(validated_data)


class ShiftTemplateSerializer(serializers.ModelSerializer):
    policy_name = serializers.CharField(source='policy.name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = ShiftTemplate
        fields = ['id', 'name', 'shift_start', 'shift_end', 'days_of_week', 'policy', 'policy_name', 'is_active', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AttendanceExceptionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='log.employee.person.legal_name', read_only=True)
    log_date = serializers.DateField(source='log.date', read_only=True)

    class Meta:
        model = AttendanceException
        fields = ['id', 'log', 'employee_name', 'log_date', 'exception_type', 'detected_at', 'is_resolved', 'resolution_notes', 'resolved_by', 'resolved_at']
        read_only_fields = ['id', 'detected_at']


class HolidayCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = HolidayCalendar
        fields = ['id', 'name', 'year', 'country', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class HolidayCalendarEntrySerializer(serializers.ModelSerializer):
    calendar_name = serializers.CharField(source='calendar.name', read_only=True)

    class Meta:
        model = HolidayCalendarEntry
        fields = ['id', 'calendar', 'calendar_name', 'date', 'name', 'holiday_type', 'is_paid']
        read_only_fields = ['id']


class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    grade_display = serializers.CharField(source='grade.grade_name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = LeavePolicy
        fields = ['id', 'leave_type', 'leave_type_name', 'grade', 'grade_display', 'employment_type', 'gender', 'days_entitled', 'accrual_method', 'max_carry_forward', 'requires_medical_cert', 'min_service_months', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class LeaveDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveDocument
        fields = ['id', 'leave_request', 'document', 'document_type', 'description', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class SeparationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = Separation
        fields = [
            'id', 'employee', 'employee_name', 'separation_type',
            'notice_date', 'last_working_date', 'reason', 'status',
            'clearance_completed', 'exit_interview_done',
            'initiated_by', 'approved_by', 'approved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'initiated_by', 'status', 'approved_by', 'approved_at',
            'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        validated_data['initiated_by'] = self.context['request'].user
        return super().create(validated_data)
