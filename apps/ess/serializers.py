from rest_framework import serializers
from .models import ESSRequestType, ESSRequest, ProfileChangeRequest, ManagerDelegation
from apps.documents.models import DocAcknowledgement as PolicyAcknowledgement


class ESSRequestTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ESSRequestType
        fields = [
            'id', 'code', 'name', 'category', 'requires_approval',
            'workflow_code', 'description', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ESSRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source='employee.person.legal_name', read_only=True, default=''
    )
    employee_number = serializers.CharField(
        source='employee.employee_number', read_only=True, default=''
    )
    request_type_display = serializers.CharField(
        source='request_type.name', read_only=True, default=''
    )
    resolved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = ESSRequest
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'request_type', 'request_type_display',
            'subject', 'description', 'payload', 'attachments',
            'status', 'workflow_request',
            'resolved_by', 'resolved_by_display', 'resolved_at', 'resolution_notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_number', 'request_type_display',
            'resolved_by_display', 'workflow_request', 'created_at', 'updated_at',
        ]

    def get_resolved_by_display(self, obj):
        if not obj.resolved_by:
            return None
        return obj.resolved_by.get_full_name() or obj.resolved_by.username


class ProfileChangeRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source='employee.person.legal_name', read_only=True, default=''
    )
    employee_number = serializers.CharField(
        source='employee.employee_number', read_only=True, default=''
    )
    reviewed_by_display = serializers.SerializerMethodField()

    class Meta:
        model = ProfileChangeRequest
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'field_name', 'field_label', 'old_value', 'new_value', 'reason',
            'evidence_document', 'status',
            'reviewed_by', 'reviewed_by_display', 'review_notes',
            'workflow_request', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_number', 'reviewed_by_display',
            'workflow_request', 'created_at', 'updated_at',
        ]

    def get_reviewed_by_display(self, obj):
        if not obj.reviewed_by:
            return None
        return obj.reviewed_by.get_full_name() or obj.reviewed_by.username


class PolicyAcknowledgementSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source='employee.person.legal_name', read_only=True, default=''
    )
    policy_display = serializers.CharField(
        source='policy.name', read_only=True, default=''
    )

    class Meta:
        model = PolicyAcknowledgement
        fields = [
            'id', 'employee', 'employee_name',
            'policy', 'policy_display',
            'version_acknowledged', 'acknowledged_at', 'ip_address',
        ]
        read_only_fields = ['id', 'employee_name', 'policy_display', 'acknowledged_at']


class ManagerDelegationSerializer(serializers.ModelSerializer):
    delegator_name = serializers.CharField(
        source='delegator.person.legal_name', read_only=True, default=''
    )
    delegate_name = serializers.CharField(
        source='delegate.person.legal_name', read_only=True, default=''
    )
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = ManagerDelegation
        fields = [
            'id', 'delegator', 'delegator_name', 'delegate', 'delegate_name',
            'delegation_type', 'workflow_code',
            'valid_from', 'valid_to', 'is_active', 'reason',
            'created_by', 'created_by_display', 'created_at',
        ]
        read_only_fields = ['id', 'delegator_name', 'delegate_name', 'created_by_display', 'created_at']

    def get_created_by_display(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
