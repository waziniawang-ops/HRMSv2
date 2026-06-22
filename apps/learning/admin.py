from django.contrib import admin
from .models import (
    Course, LearningPath, LearningPathCourse, AssignmentRule, LearningAssignment,
    CourseSession, Enrollment, Assessment, CourseCompletion, Certificate,
    TrainingRequest, SkillGap, LearningTranscript,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'course_type', 'duration_hours', 'is_mandatory', 'status']
    list_filter = ['course_type', 'status', 'is_mandatory']
    search_fields = ['code', 'title']
    raw_id_fields = ['created_by', 'approved_by']


class LearningPathCourseInline(admin.TabularInline):
    model = LearningPathCourse
    extra = 0
    fields = ['course', 'sequence_order', 'is_required']
    raw_id_fields = ['course']


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ['name', 'status']
    list_filter = ['status']
    raw_id_fields = ['created_by']
    inlines = [LearningPathCourseInline]


@admin.register(AssignmentRule)
class AssignmentRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger', 'course', 'learning_path', 'due_days', 'is_active']
    list_filter = ['trigger', 'is_active']
    raw_id_fields = ['course', 'learning_path', 'target_job_family', 'target_grade']


@admin.register(LearningAssignment)
class LearningAssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'course', 'learning_path', 'due_date', 'status']
    list_filter = ['status']
    raw_id_fields = ['employee', 'course', 'learning_path', 'assignment_rule', 'assigned_by']


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ['employee', 'status', 'enrolled_at']
    readonly_fields = ['enrolled_at']
    raw_id_fields = ['employee']


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ['session_code', 'course', 'start_datetime', 'end_datetime', 'status']
    list_filter = ['status', 'course']
    inlines = [EnrollmentInline]


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'course', 'attempt_number', 'score', 'is_passed', 'attempted_at']
    list_filter = ['is_passed', 'course']
    raw_id_fields = ['employee', 'course']


@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ['employee', 'course', 'completed_at', 'score', 'is_valid', 'expiry_date']
    list_filter = ['is_valid', 'course']
    raw_id_fields = ['employee', 'course']


@admin.register(TrainingRequest)
class TrainingRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'training_title', 'provider', 'estimated_cost', 'status']
    list_filter = ['status']
    raw_id_fields = ['employee', 'reviewed_by']


@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    list_display = ['employee', 'skill_name', 'required_level', 'current_level', 'gap', 'is_closed']
    list_filter = ['is_closed']
    raw_id_fields = ['employee', 'recommended_course']


@admin.register(LearningTranscript)
class LearningTranscriptAdmin(admin.ModelAdmin):
    list_display = ['employee', 'total_courses_completed', 'total_hours_completed', 'total_certificates_earned', 'mandatory_completion_rate', 'last_updated']
    raw_id_fields = ['employee']
