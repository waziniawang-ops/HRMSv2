from rest_framework import serializers
from .models import (
    SuccessionPlan, SuccessorNomination, TalentPool, TalentProfile,
    DevelopmentPlan, DevelopmentActivity, CriticalRole,
)


class DevelopmentActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DevelopmentActivity
        fields = [
            'id', 'activity_type', 'title', 'description', 'target_date',
            'status', 'completed_at', 'outcome_notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DevelopmentPlanSerializer(serializers.ModelSerializer):
    activities = DevelopmentActivitySerializer(many=True, read_only=True)
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = DevelopmentPlan
        fields = [
            'id', 'employee', 'employee_name', 'succession_nominee', 'title',
            'objective', 'target_completion_date', 'status', 'progress_notes',
            'created_by', 'created_at', 'updated_at', 'activities',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class SuccessorNominationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.person.legal_name', read_only=True)

    class Meta:
        model = SuccessorNomination
        fields = [
            'id', 'succession_plan', 'candidate', 'candidate_name',
            'readiness_level', 'priority_rank', 'strengths', 'development_needs',
            'is_willing', 'nominated_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'nominated_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['nominated_by'] = self.context['request'].user
        return super().create(validated_data)


class SuccessionPlanSerializer(serializers.ModelSerializer):
    nominees = SuccessorNominationSerializer(many=True, read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    incumbent_name = serializers.CharField(source='incumbent.person.legal_name', read_only=True)

    class Meta:
        model = SuccessionPlan
        fields = [
            'id', 'position', 'position_title', 'incumbent', 'incumbent_name',
            'plan_year', 'status', 'risk_level', 'notes',
            'prepared_by', 'approved_by', 'approved_at',
            'created_at', 'updated_at', 'nominees',
        ]
        read_only_fields = ['id', 'prepared_by', 'approved_by', 'approved_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['prepared_by'] = self.context['request'].user
        return super().create(validated_data)


class TalentPoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentPool
        fields = ['id', 'name', 'tier', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class TalentProfileSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    talent_pool_name = serializers.CharField(source='talent_pool.name', read_only=True, allow_null=True, default=None)
    nine_box_label = serializers.CharField(source='get_nine_box_score_display', read_only=True)
    assessed_by_display = serializers.CharField(source='assessed_by.get_full_name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = TalentProfile
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'talent_pool', 'talent_pool_name',
            'nine_box_score', 'nine_box_label', 'flight_risk',
            'career_aspirations', 'key_strengths', 'development_areas',
            'mobility_preference', 'assessed_by', 'assessed_by_display',
            'last_assessed_at', 'workflow_request',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'assessed_by', 'assessed_by_display', 'last_assessed_at', 'workflow_request', 'created_at', 'updated_at']


class CriticalRoleSerializer(serializers.ModelSerializer):
    position_title = serializers.CharField(source='position.title', read_only=True, default='')
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)

    class Meta:
        model = CriticalRole
        fields = [
            'id', 'position', 'position_title', 'rationale',
            'risk_level', 'risk_level_display', 'time_to_fill_days',
            'has_identified_successor', 'minimum_successors_required',
            'review_date', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'position_title', 'risk_level_display', 'created_at', 'updated_at']
