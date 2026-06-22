from rest_framework import serializers
from .models import (
    HSEIncidentType, HSEIncident, IncidentInvestigation,
    CorrectiveAction, WellbeingProgram, WellbeingEnrollment, MedicalFitnessRecord,
)


class HSEIncidentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HSEIncidentType
        fields = ['id', 'code', 'name', 'default_severity', 'requires_investigation',
                  'notification_required', 'is_active']
        read_only_fields = ['id']


class HSEIncidentSerializer(serializers.ModelSerializer):
    incident_type_name = serializers.CharField(source='incident_type.name', read_only=True)
    reported_by_display = serializers.SerializerMethodField()
    corrective_actions_count = serializers.SerializerMethodField()

    class Meta:
        model = HSEIncident
        fields = [
            'id', 'incident_number', 'incident_type', 'incident_type_name',
            'title', 'description', 'incident_date', 'location', 'severity',
            'status', 'reported_by', 'reported_by_display',
            'employees_involved', 'witness_names', 'immediate_action_taken',
            'is_work_related', 'is_notifiable', 'notification_authority',
            'root_cause_identified', 'corrective_actions_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'incident_number', 'reported_by', 'created_at', 'updated_at']

    def get_reported_by_display(self, obj):
        return obj.reported_by.get_full_name() or obj.reported_by.username

    def get_corrective_actions_count(self, obj):
        return obj.direct_corrective_actions.count()

    def create(self, validated_data):
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)


class IncidentInvestigationSerializer(serializers.ModelSerializer):
    incident_number = serializers.CharField(source='incident.incident_number', read_only=True)
    lead_investigator_display = serializers.SerializerMethodField()

    class Meta:
        model = IncidentInvestigation
        fields = [
            'id', 'incident', 'incident_number', 'lead_investigator', 'lead_investigator_display',
            'team_members', 'investigation_start', 'target_close_date',
            'root_cause', 'contributing_factors', 'findings', 'recommendations',
            'status', 'completed_at', 'report_file', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_lead_investigator_display(self, obj):
        return obj.lead_investigator.get_full_name() or obj.lead_investigator.username


class CorrectiveActionSerializer(serializers.ModelSerializer):
    assigned_to_display = serializers.SerializerMethodField()
    verified_by_display = serializers.SerializerMethodField()

    class Meta:
        model = CorrectiveAction
        fields = [
            'id', 'investigation', 'incident', 'action_description', 'action_type',
            'assigned_to', 'assigned_to_display', 'due_date', 'priority', 'status',
            'completion_evidence', 'completed_at', 'verified_by', 'verified_by_display',
            'verified_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_assigned_to_display(self, obj):
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def get_verified_by_display(self, obj):
        if not obj.verified_by:
            return None
        return obj.verified_by.get_full_name() or obj.verified_by.username


class WellbeingProgramSerializer(serializers.ModelSerializer):
    created_by_display = serializers.SerializerMethodField()
    program_type_display = serializers.CharField(source='get_program_type_display', read_only=True)
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = WellbeingProgram
        fields = [
            'id', 'name', 'description', 'program_type', 'program_type_display',
            'start_date', 'end_date', 'status', 'facilitator', 'target_audience',
            'max_participants', 'current_enrollment', 'enrollment_count',
            'is_mandatory', 'created_by', 'created_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'current_enrollment', 'created_at', 'updated_at']

    def get_created_by_display(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_enrollment_count(self, obj):
        return obj.enrollments.filter(status='ACTIVE').count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class WellbeingEnrollmentSerializer(serializers.ModelSerializer):
    program_name = serializers.CharField(source='program.name', read_only=True)
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)

    class Meta:
        model = WellbeingEnrollment
        fields = [
            'id', 'program', 'program_name', 'employee', 'employee_name', 'employee_number',
            'enrolled_at', 'status', 'completion_date', 'attendance_percentage',
        ]
        read_only_fields = ['id', 'enrolled_at']


class MedicalFitnessRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    fitness_status_display = serializers.CharField(source='get_fitness_status_display', read_only=True)

    class Meta:
        model = MedicalFitnessRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'assessment_date', 'fitness_status', 'fitness_status_display',
            'restrictions', 'next_review_date', 'assessed_by', 'medical_facility',
            'certificate_file', 'is_confidential', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
