from rest_framework import serializers
from .models import ERCaseCategory, ERCase, CaseParty, CaseEvidence, CaseHearing, CaseOutcome, ERAppeal


class ERCaseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ERCaseCategory
        fields = ['id', 'code', 'name', 'is_grievance', 'is_disciplinary', 'is_confidential', 'is_active']
        read_only_fields = ['id']


class CasePartySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True, default='')
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True, default='')

    class Meta:
        model = CaseParty
        fields = [
            'id', 'case', 'employee', 'employee_name', 'employee_number',
            'role', 'coi_declared', 'coi_notes', 'notes', 'added_at',
        ]
        read_only_fields = ['id', 'employee_name', 'employee_number', 'added_at']


class CaseEvidenceSerializer(serializers.ModelSerializer):
    added_by_display = serializers.SerializerMethodField()

    class Meta:
        model = CaseEvidence
        fields = [
            'id', 'case', 'title', 'description', 'evidence_type',
            'document', 'added_by', 'added_by_display', 'is_confidential', 'created_at',
        ]
        read_only_fields = ['id', 'added_by', 'added_by_display', 'created_at']

    def get_added_by_display(self, obj):
        return obj.added_by.get_full_name() or obj.added_by.username

    def create(self, validated_data):
        validated_data['added_by'] = self.context['request'].user
        return super().create(validated_data)


class CaseHearingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseHearing
        fields = [
            'id', 'case', 'hearing_date', 'location', 'hearing_type',
            'panel_members', 'status', 'outcome_summary', 'minutes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CaseOutcomeSerializer(serializers.ModelSerializer):
    decided_by_display = serializers.SerializerMethodField()

    class Meta:
        model = CaseOutcome
        fields = [
            'id', 'case', 'outcome_type', 'effective_date', 'duration_days',
            'outcome_details', 'letter_issued', 'letter_issued_at',
            'decided_by', 'decided_by_display', 'created_at',
        ]
        read_only_fields = ['id', 'decided_by', 'decided_by_display', 'created_at']

    def get_decided_by_display(self, obj):
        return obj.decided_by.get_full_name() or obj.decided_by.username

    def create(self, validated_data):
        validated_data['decided_by'] = self.context['request'].user
        return super().create(validated_data)


class ERAppealSerializer(serializers.ModelSerializer):
    appellant_name = serializers.CharField(source='appellant.person.legal_name', read_only=True, default='')
    appellant_number = serializers.CharField(source='appellant.employee_number', read_only=True, default='')
    reviewed_by_display = serializers.SerializerMethodField()
    case_number = serializers.CharField(source='case.case_number', read_only=True, default='')

    class Meta:
        model = ERAppeal
        fields = [
            'id', 'case', 'case_number', 'appellant', 'appellant_name', 'appellant_number',
            'appeal_date', 'appeal_reason', 'grounds_of_appeal', 'status',
            'reviewed_by', 'reviewed_by_display', 'review_notes',
            'workflow_request', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'appellant_name', 'appellant_number', 'reviewed_by_display',
            'case_number', 'workflow_request', 'created_at', 'updated_at',
        ]

    def get_reviewed_by_display(self, obj):
        if not obj.reviewed_by:
            return None
        return obj.reviewed_by.get_full_name() or obj.reviewed_by.username


class ERCaseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    subject_employee_name = serializers.CharField(
        source='subject_employee.person.legal_name', read_only=True, default=''
    )
    subject_employee_number = serializers.CharField(
        source='subject_employee.employee_number', read_only=True, default=''
    )
    opened_by_display = serializers.SerializerMethodField()
    assigned_investigator_display = serializers.SerializerMethodField()
    parties = CasePartySerializer(many=True, read_only=True)

    class Meta:
        model = ERCase
        fields = [
            'id', 'case_number', 'category', 'category_name',
            'subject', 'description', 'case_type', 'status', 'severity',
            'subject_employee', 'subject_employee_name', 'subject_employee_number',
            'opened_by', 'opened_by_display',
            'assigned_investigator', 'assigned_investigator_display',
            'legal_hold', 'confidential', 'workflow_request',
            'closed_at', 'parties', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'case_number', 'category_name', 'subject_employee_name', 'subject_employee_number',
            'opened_by', 'opened_by_display', 'assigned_investigator_display',
            'workflow_request', 'parties', 'created_at', 'updated_at',
        ]

    def get_opened_by_display(self, obj):
        return obj.opened_by.get_full_name() or obj.opened_by.username

    def get_assigned_investigator_display(self, obj):
        if not obj.assigned_investigator:
            return None
        return obj.assigned_investigator.get_full_name() or obj.assigned_investigator.username

    def create(self, validated_data):
        validated_data['opened_by'] = self.context['request'].user
        return super().create(validated_data)
