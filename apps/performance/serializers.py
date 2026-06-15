from rest_framework import serializers
from .models import (
    PerformanceCycle, CompetencyModel, Competency, GoalPlan, Goal, GoalProgress,
    ReviewForm, ReviewRating, CalibrationSession, CalibratedRating,
    FinalOutcome, ImprovementPlan,
)


class PerformanceCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceCycle
        fields = [
            'id', 'name', 'cycle_year', 'status',
            'goal_setting_start', 'goal_setting_end',
            'mid_year_start', 'mid_year_end',
            'year_end_start', 'year_end_end',
            'calibration_start', 'calibration_end',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = ['id', 'model', 'name', 'description', 'max_level', 'weight', 'created_at']
        read_only_fields = ['id', 'created_at']


class CompetencyModelSerializer(serializers.ModelSerializer):
    competencies = CompetencySerializer(many=True, read_only=True)

    class Meta:
        model = CompetencyModel
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'competencies']
        read_only_fields = ['id', 'created_at']


class GoalProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalProgress
        fields = ['id', 'goal', 'update_date', 'current_value', 'completion_percentage', 'notes', 'recorded_by', 'created_at']
        read_only_fields = ['id', 'recorded_by', 'created_at']

    def create(self, validated_data):
        validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)


class GoalSerializer(serializers.ModelSerializer):
    progress_updates = GoalProgressSerializer(many=True, read_only=True)

    class Meta:
        model = Goal
        fields = [
            'id', 'goal_plan', 'title', 'description', 'category', 'weight',
            'target_value', 'unit_of_measure', 'due_date', 'status',
            'completion_percentage', 'created_at', 'updated_at', 'progress_updates',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GoalPlanSerializer(serializers.ModelSerializer):
    goals = GoalSerializer(many=True, read_only=True)
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    cycle_name = serializers.CharField(source='cycle.name', read_only=True)

    class Meta:
        model = GoalPlan
        fields = [
            'id', 'employee', 'employee_name', 'cycle', 'cycle_name',
            'status', 'overall_weight_total', 'approved_by', 'approved_at',
            'created_at', 'updated_at', 'goals',
        ]
        read_only_fields = ['id', 'overall_weight_total', 'approved_by', 'approved_at', 'created_at', 'updated_at']


class ReviewRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewRating
        fields = ['id', 'review_form', 'competency', 'goal', 'rating', 'comments', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewFormSerializer(serializers.ModelSerializer):
    ratings = ReviewRatingSerializer(many=True, read_only=True)
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = ReviewForm
        fields = [
            'id', 'cycle', 'employee', 'employee_name', 'reviewer', 'reviewer_name', 'review_type',
            'status', 'overall_rating', 'strengths_comments', 'improvement_comments',
            'overall_comments', 'submitted_at', 'acknowledged_at',
            'created_at', 'updated_at', 'ratings',
        ]
        read_only_fields = ['id', 'submitted_at', 'acknowledged_at', 'created_at', 'updated_at']

    def get_reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name() or obj.reviewer.username
        return None


class CalibratedRatingSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = CalibratedRating
        fields = [
            'id', 'session', 'employee', 'employee_name',
            'pre_calibration_rating', 'calibrated_rating', 'calibration_notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CalibrationSessionSerializer(serializers.ModelSerializer):
    calibrated_ratings = CalibratedRatingSerializer(many=True, read_only=True)
    org_unit_name = serializers.CharField(source='org_unit.name', read_only=True)

    class Meta:
        model = CalibrationSession
        fields = [
            'id', 'cycle', 'org_unit', 'org_unit_name', 'session_date',
            'status', 'facilitator', 'notes', 'created_at', 'calibrated_ratings',
        ]
        read_only_fields = ['id', 'created_at']


class FinalOutcomeSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    cycle_name = serializers.CharField(source='cycle.name', read_only=True)

    class Meta:
        model = FinalOutcome
        fields = [
            'id', 'cycle', 'cycle_name', 'employee', 'employee_name', 'final_rating', 'outcome_label',
            'eligible_for_increment', 'eligible_for_bonus',
            'increment_percentage', 'bonus_amount', 'notes',
            'approved_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'approved_by', 'created_at', 'updated_at']


class ImprovementPlanSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = ImprovementPlan
        fields = [
            'id', 'employee', 'employee_name', 'cycle', 'start_date', 'end_date',
            'reason', 'objectives', 'status', 'outcome_notes',
            'initiated_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'initiated_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['initiated_by'] = self.context['request'].user
        return super().create(validated_data)
