from rest_framework import serializers
from .models import (
    SkillCategory, Skill, ProficiencyScale, JobSkillRequirement,
    EmployeeSkill, SkillEvidence, SkillGapAnalysis, SkillGap,
)


class SkillCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = SkillCategory
        fields = ['id', 'code', 'name', 'parent', 'parent_name', 'description', 'is_active']
        read_only_fields = ['id']


class SkillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Skill
        fields = ['id', 'code', 'name', 'category', 'category_name', 'description', 'aliases', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProficiencyScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProficiencyScale
        fields = ['id', 'code', 'name', 'description', 'level', 'behavioural_indicators']
        read_only_fields = ['id']


class JobSkillRequirementSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_code = serializers.CharField(source='skill.code', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    required_level_name = serializers.CharField(source='required_level.name', read_only=True)
    required_level_num = serializers.IntegerField(source='required_level.level', read_only=True)

    class Meta:
        model = JobSkillRequirement
        fields = [
            'id', 'job', 'job_title', 'skill', 'skill_name', 'skill_code',
            'required_level', 'required_level_name', 'required_level_num',
            'is_mandatory', 'notes',
        ]
        read_only_fields = ['id']


class SkillEvidenceSerializer(serializers.ModelSerializer):
    evidence_type_display = serializers.CharField(source='get_evidence_type_display', read_only=True)
    verified_by_display = serializers.SerializerMethodField()

    class Meta:
        model = SkillEvidence
        fields = [
            'id', 'employee_skill', 'title', 'evidence_type', 'evidence_type_display',
            'description', 'document', 'url', 'verified', 'verified_by',
            'verified_by_display', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_verified_by_display(self, obj):
        if not obj.verified_by:
            return None
        return obj.verified_by.get_full_name() or obj.verified_by.username


class EmployeeSkillSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_code = serializers.CharField(source='skill.code', read_only=True)
    category_name = serializers.CharField(source='skill.category.name', read_only=True)
    proficiency_name = serializers.CharField(source='proficiency.name', read_only=True)
    proficiency_level = serializers.IntegerField(source='proficiency.level', read_only=True)
    endorsed_by_display = serializers.SerializerMethodField()
    evidence_items = SkillEvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = EmployeeSkill
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'skill', 'skill_name', 'skill_code', 'category_name',
            'proficiency', 'proficiency_name', 'proficiency_level',
            'is_self_assessed', 'is_endorsed', 'endorsed_by', 'endorsed_by_display',
            'endorsed_at', 'evidence_description', 'assessed_date',
            'last_updated', 'evidence_items',
        ]
        read_only_fields = ['id', 'last_updated', 'endorsed_by', 'endorsed_at']

    def get_endorsed_by_display(self, obj):
        if not obj.endorsed_by:
            return None
        return obj.endorsed_by.get_full_name() or obj.endorsed_by.username


class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True, allow_null=True, default=None)

    class Meta:
        model = SkillGapAnalysis
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'job', 'job_title', 'analysis_date', 'overall_match_percentage',
            'gaps_summary', 'recommended_training', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'analysis_date', 'created_at']


class SkillGapSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    required_level_name = serializers.CharField(source='required_level.name', read_only=True)
    current_level_name = serializers.CharField(
        source='current_level.name', read_only=True, allow_null=True, default=None
    )
    recommended_course_name = serializers.CharField(
        source='recommended_course.title', read_only=True, allow_null=True, default=None
    )

    class Meta:
        model = SkillGap
        fields = [
            'id', 'employee', 'employee_name', 'skill', 'skill_name',
            'required_level', 'required_level_name', 'current_level', 'current_level_name',
            'gap_size', 'recommended_course', 'recommended_course_name',
            'status', 'identified_at', 'target_closure_date',
        ]
        read_only_fields = ['id', 'gap_size', 'identified_at']
