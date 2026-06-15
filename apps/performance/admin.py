from django.contrib import admin
from .models import (
    PerformanceCycle, CompetencyModel, Competency, GoalPlan, Goal, GoalProgress,
    ReviewForm, ReviewRating, CalibrationSession, CalibratedRating,
    FinalOutcome, ImprovementPlan,
)


@admin.register(PerformanceCycle)
class PerformanceCycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'cycle_year', 'status', 'goal_setting_start', 'year_end_end']
    list_filter = ['status', 'cycle_year']


class CompetencyInline(admin.TabularInline):
    model = Competency
    extra = 0
    fields = ['name', 'max_level', 'weight']


@admin.register(CompetencyModel)
class CompetencyModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    inlines = [CompetencyInline]


class GoalInline(admin.TabularInline):
    model = Goal
    extra = 0
    fields = ['title', 'category', 'weight', 'status', 'completion_percentage']


@admin.register(GoalPlan)
class GoalPlanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cycle', 'status', 'overall_weight_total']
    list_filter = ['status', 'cycle']
    raw_id_fields = ['employee', 'cycle', 'approved_by']
    inlines = [GoalInline]


@admin.register(ReviewForm)
class ReviewFormAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cycle', 'review_type', 'status', 'overall_rating']
    list_filter = ['review_type', 'status', 'cycle']
    raw_id_fields = ['employee', 'cycle', 'reviewer']


class CalibratedRatingInline(admin.TabularInline):
    model = CalibratedRating
    extra = 0
    fields = ['employee', 'pre_calibration_rating', 'calibrated_rating']
    raw_id_fields = ['employee']


@admin.register(CalibrationSession)
class CalibrationSessionAdmin(admin.ModelAdmin):
    list_display = ['org_unit', 'cycle', 'session_date', 'status', 'facilitator']
    list_filter = ['status', 'cycle']
    raw_id_fields = ['org_unit', 'cycle', 'facilitator']
    inlines = [CalibratedRatingInline]


@admin.register(FinalOutcome)
class FinalOutcomeAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cycle', 'final_rating', 'outcome_label', 'eligible_for_increment', 'eligible_for_bonus']
    list_filter = ['outcome_label', 'cycle', 'eligible_for_increment']
    raw_id_fields = ['employee', 'cycle', 'approved_by']


@admin.register(ImprovementPlan)
class ImprovementPlanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'start_date', 'end_date', 'status']
    list_filter = ['status']
    raw_id_fields = ['employee', 'cycle', 'initiated_by']
