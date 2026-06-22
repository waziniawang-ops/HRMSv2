from rest_framework import serializers
from .models import (
    OffboardingCase, ClearanceTask, AssetClearance,
    AccessRevocation, ExitInterview, FinalSettlement,
)


class ClearanceTaskSerializer(serializers.ModelSerializer):
    assigned_to_display = serializers.SerializerMethodField()
    completed_by_display = serializers.SerializerMethodField()

    class Meta:
        model = ClearanceTask
        fields = [
            'id', 'case', 'task_name', 'department', 'task_type',
            'assigned_to', 'assigned_to_display', 'due_date', 'status',
            'completion_notes', 'completed_by', 'completed_by_display', 'completed_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_assigned_to_display(self, obj):
        if not obj.assigned_to:
            return None
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def get_completed_by_display(self, obj):
        if not obj.completed_by:
            return None
        return obj.completed_by.get_full_name() or obj.completed_by.username


class AssetClearanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetClearance
        fields = [
            'id', 'case', 'asset_name', 'asset_code', 'asset_type',
            'issued_date', 'return_status', 'return_date',
            'condition_on_return', 'condition_notes', 'deduction_amount',
            'cleared_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AccessRevocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRevocation
        fields = [
            'id', 'case', 'system_name', 'access_type', 'access_identifier',
            'scheduled_revocation_date', 'status', 'revoked_by', 'revoked_at',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ExitInterviewSerializer(serializers.ModelSerializer):
    conducted_by_display = serializers.SerializerMethodField()

    class Meta:
        model = ExitInterview
        fields = [
            'id', 'case', 'conducted_by', 'conducted_by_display', 'interview_date',
            'format', 'reason_for_leaving', 'overall_experience',
            'would_return', 'would_recommend', 'responses', 'overall_sentiment',
            'is_confidential', 'additional_comments', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_conducted_by_display(self, obj):
        return obj.conducted_by.get_full_name() or obj.conducted_by.username


class FinalSettlementSerializer(serializers.ModelSerializer):
    approved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = FinalSettlement
        fields = [
            'id', 'case', 'basic_pay_balance', 'leave_encashment', 'gratuity_amount',
            'notice_pay_deduction', 'asset_deductions', 'other_deductions', 'other_additions',
            'total_settlement', 'settlement_date', 'payment_method', 'status',
            'approved_by', 'approved_by_display', 'workflow_request',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'approved_by', 'workflow_request', 'created_at', 'updated_at']

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username


class OffboardingCaseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    initiated_by_display = serializers.SerializerMethodField()
    hr_owner_display = serializers.SerializerMethodField()
    clearance_summary = serializers.SerializerMethodField()

    class Meta:
        model = OffboardingCase
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'separation', 'status', 'notice_period_days', 'last_working_date',
            'exit_interview_scheduled_date', 'knowledge_handover_due',
            'rehire_eligible', 'rehire_notes', 'legal_hold',
            'final_settlement_amount', 'settlement_status', 'settlement_paid_at',
            'initiated_by', 'initiated_by_display', 'hr_owner', 'hr_owner_display',
            'workflow_request', 'completed_at', 'clearance_summary',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'initiated_by', 'workflow_request', 'completed_at', 'created_at', 'updated_at']

    def get_initiated_by_display(self, obj):
        return obj.initiated_by.get_full_name() or obj.initiated_by.username

    def get_hr_owner_display(self, obj):
        if not obj.hr_owner:
            return None
        return obj.hr_owner.get_full_name() or obj.hr_owner.username

    def get_clearance_summary(self, obj):
        tasks = obj.clearance_tasks.all()
        total = tasks.count()
        completed = tasks.filter(status__in=['COMPLETED', 'WAIVED']).count()
        return {'total': total, 'completed': completed, 'pending': total - completed}

    def create(self, validated_data):
        validated_data['initiated_by'] = self.context['request'].user
        return super().create(validated_data)
