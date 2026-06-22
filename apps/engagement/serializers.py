from rest_framework import serializers
from .models import (
    SurveyTemplate, EngagementSurvey, SurveyResponse,
    ActionPlan, RecognitionType, RecognitionAward,
    RecognitionNomination, EmployeePoints,
)


class SurveyTemplateSerializer(serializers.ModelSerializer):
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = SurveyTemplate
        fields = [
            'id', 'code', 'name', 'description', 'survey_type',
            'questions', 'is_active', 'created_by', 'created_by_display', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_created_by_display(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EngagementSurveySerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    survey_type = serializers.CharField(source='template.survey_type', read_only=True)
    launched_by_display = serializers.SerializerMethodField()
    response_completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = EngagementSurvey
        fields = [
            'id', 'template', 'template_name', 'survey_type', 'title', 'description',
            'target_audience', 'target_ids', 'open_date', 'close_date',
            'is_anonymous', 'anonymity_threshold', 'status', 'response_count',
            'launched_by', 'launched_by_display', 'response_completion_rate',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'launched_by', 'response_count', 'created_at', 'updated_at']

    def get_launched_by_display(self, obj):
        return obj.launched_by.get_full_name() or obj.launched_by.username

    def get_response_completion_rate(self, obj):
        total = obj.responses.count()
        complete = obj.responses.filter(is_complete=True).count()
        if total == 0:
            return 0
        return round((complete / total) * 100, 1)

    def create(self, validated_data):
        validated_data['launched_by'] = self.context['request'].user
        return super().create(validated_data)


class SurveyResponseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(
        source='employee.person.legal_name', read_only=True, default=None, allow_null=True
    )

    class Meta:
        model = SurveyResponse
        fields = [
            'id', 'survey', 'employee', 'employee_name', 'response_token',
            'responses', 'enps_score', 'submitted_at', 'is_complete',
        ]
        read_only_fields = ['id', 'response_token', 'submitted_at']


class ActionPlanSerializer(serializers.ModelSerializer):
    assigned_to_display = serializers.SerializerMethodField()
    created_by_display = serializers.SerializerMethodField()
    survey_title = serializers.CharField(source='survey.title', read_only=True)

    class Meta:
        model = ActionPlan
        fields = [
            'id', 'survey', 'survey_title', 'title', 'description', 'focus_area',
            'assigned_to', 'assigned_to_display', 'target_date', 'status',
            'progress_notes', 'completion_percentage',
            'created_by', 'created_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_assigned_to_display(self, obj):
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def get_created_by_display(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class RecognitionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecognitionType
        fields = [
            'id', 'code', 'name', 'recognition_category', 'points_value',
            'badge_icon', 'requires_approval', 'is_active',
        ]
        read_only_fields = ['id']


class RecognitionAwardSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.person.legal_name', read_only=True)
    nominated_by_name = serializers.CharField(source='nominated_by.person.legal_name', read_only=True)
    recognition_type_name = serializers.CharField(source='recognition_type.name', read_only=True)
    reviewed_by_display = serializers.SerializerMethodField()

    class Meta:
        model = RecognitionAward
        fields = [
            'id', 'nominated_by', 'nominated_by_name', 'recipient', 'recipient_name',
            'recognition_type', 'recognition_type_name', 'message', 'is_public',
            'points_awarded', 'status', 'reviewed_by', 'reviewed_by_display',
            'reviewed_at', 'created_at',
        ]
        read_only_fields = ['id', 'reviewed_by', 'reviewed_at', 'created_at']

    def get_reviewed_by_display(self, obj):
        if not obj.reviewed_by:
            return None
        return obj.reviewed_by.get_full_name() or obj.reviewed_by.username


class RecognitionNominationSerializer(serializers.ModelSerializer):
    nominator_name = serializers.CharField(source='nominator.person.legal_name', read_only=True)
    nominee_name = serializers.CharField(source='nominee.person.legal_name', read_only=True)
    recognition_type_name = serializers.CharField(source='recognition_type.name', read_only=True)

    class Meta:
        model = RecognitionNomination
        fields = [
            'id', 'nominator', 'nominator_name', 'nominee', 'nominee_name',
            'recognition_type', 'recognition_type_name', 'justification',
            'supporting_evidence', 'status', 'workflow_request',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'workflow_request', 'created_at', 'updated_at']


class EmployeePointsSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    available_points = serializers.IntegerField(read_only=True)

    class Meta:
        model = EmployeePoints
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'total_earned', 'total_redeemed', 'available_points', 'updated_at',
        ]
        read_only_fields = ['id', 'total_earned', 'total_redeemed', 'updated_at']
