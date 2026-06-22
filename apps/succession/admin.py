from django.contrib import admin
from .models import (
    SuccessionPlan, SuccessorNomination, TalentPool, TalentProfile,
    DevelopmentPlan, DevelopmentActivity, CriticalRole,
)


class SuccessorNominationInline(admin.TabularInline):
    model = SuccessorNomination
    extra = 0
    fields = ['candidate', 'readiness_level', 'priority_rank', 'is_willing']
    raw_id_fields = ['candidate']


@admin.register(SuccessionPlan)
class SuccessionPlanAdmin(admin.ModelAdmin):
    list_display = ['position', 'incumbent', 'plan_year', 'status', 'risk_level', 'prepared_by']
    list_filter = ['status', 'risk_level', 'plan_year']
    raw_id_fields = ['position', 'incumbent', 'prepared_by', 'approved_by']
    inlines = [SuccessorNominationInline]


@admin.register(TalentPool)
class TalentPoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'is_active']
    list_filter = ['tier', 'is_active']


@admin.register(TalentProfile)
class TalentProfileAdmin(admin.ModelAdmin):
    list_display = ['employee', 'talent_pool', 'nine_box_score', 'flight_risk', 'mobility_preference']
    list_filter = ['flight_risk', 'talent_pool', 'mobility_preference']
    raw_id_fields = ['employee', 'talent_pool', 'assessed_by']


class DevelopmentActivityInline(admin.TabularInline):
    model = DevelopmentActivity
    extra = 0
    fields = ['activity_type', 'title', 'target_date', 'status']


@admin.register(DevelopmentPlan)
class DevelopmentPlanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'title', 'target_completion_date', 'status']
    list_filter = ['status']
    raw_id_fields = ['employee', 'succession_nominee', 'created_by']
    inlines = [DevelopmentActivityInline]


@admin.register(CriticalRole)
class CriticalRoleAdmin(admin.ModelAdmin):
    list_display = ['position', 'risk_level', 'has_identified_successor', 'minimum_successors_required', 'time_to_fill_days', 'is_active']
    list_filter = ['risk_level', 'has_identified_successor', 'is_active']
    raw_id_fields = ['position']
