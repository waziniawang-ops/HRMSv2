from rest_framework import serializers
from .models import (
    Course, LearningPath, LearningPathCourse, AssignmentRule, LearningAssignment,
    CourseSession, Enrollment, Assessment, CourseCompletion, Certificate,
    TrainingRequest, SkillGap,
)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description', 'course_type', 'duration_hours',
            'passing_score', 'max_participants', 'is_mandatory', 'status',
            'content_url', 'created_by', 'approved_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'approved_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class LearningPathCourseSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = LearningPathCourse
        fields = ['id', 'course', 'course_title', 'sequence_order', 'is_required']
        read_only_fields = ['id']


class LearningPathSerializer(serializers.ModelSerializer):
    path_courses = LearningPathCourseSerializer(
        source='learningpathcourse_set', many=True, read_only=True
    )

    class Meta:
        model = LearningPath
        fields = ['id', 'name', 'description', 'status', 'created_by', 'created_at', 'updated_at', 'path_courses']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AssignmentRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentRule
        fields = [
            'id', 'name', 'trigger', 'course', 'learning_path',
            'target_job_family', 'target_grade', 'due_days', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class LearningAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    path_name = serializers.CharField(source='learning_path.name', read_only=True)
    assigned_by_display = serializers.SerializerMethodField()
    trigger = serializers.CharField(source='assignment_rule.trigger', read_only=True, default='MANUAL')

    class Meta:
        model = LearningAssignment
        fields = [
            'id', 'employee', 'employee_name', 'course', 'course_title',
            'learning_path', 'path_name', 'assignment_rule', 'trigger', 'due_date',
            'status', 'assigned_by', 'assigned_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'assigned_by', 'created_at', 'updated_at']

    def get_assigned_by_display(self, obj):
        if obj.assigned_by:
            return obj.assigned_by.get_full_name() or obj.assigned_by.username
        return None

    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)


class CourseSessionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseSession
        fields = [
            'id', 'course', 'course_title', 'session_code', 'start_datetime', 'end_datetime',
            'venue', 'facilitator_name', 'status', 'max_participants',
            'enrolled_count', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status=Enrollment.STATUS_ENROLLED).count()


class EnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'employee', 'employee_name', 'course_session', 'status', 'enrolled_at', 'attended_at']
        read_only_fields = ['id', 'enrolled_at']


class AssessmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = Assessment
        fields = [
            'id', 'course', 'employee', 'employee_name', 'attempt_number',
            'score', 'is_passed', 'attempted_at',
        ]
        read_only_fields = ['id', 'is_passed', 'attempted_at']


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['id', 'completion', 'certificate_number', 'issued_at', 'expiry_date', 'file']
        read_only_fields = ['id', 'issued_at']


class CourseCompletionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    certificate = CertificateSerializer(read_only=True)

    class Meta:
        model = CourseCompletion
        fields = [
            'id', 'employee', 'employee_name', 'course', 'course_title',
            'completed_at', 'score', 'hours_completed', 'is_valid', 'expiry_date',
            'created_at', 'certificate',
        ]
        read_only_fields = ['id', 'created_at']


class TrainingRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = TrainingRequest
        fields = [
            'id', 'employee', 'employee_name', 'training_title', 'provider',
            'reason', 'estimated_cost', 'requested_dates', 'status',
            'reviewed_by', 'review_notes', 'reviewed_at', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'reviewed_by', 'reviewed_at', 'created_at']


class SkillGapSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    recommended_course_title = serializers.CharField(source='recommended_course.title', read_only=True)

    class Meta:
        model = SkillGap
        fields = [
            'id', 'employee', 'employee_name', 'skill_name', 'required_level',
            'current_level', 'gap', 'recommended_course', 'recommended_course_title',
            'is_closed', 'assessed_at', 'closed_at',
        ]
        read_only_fields = ['id', 'gap', 'assessed_at']
