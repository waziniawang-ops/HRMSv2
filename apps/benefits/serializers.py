from rest_framework import serializers
from .models import BenefitPlan, EligibilityRule, BenefitEnrollment, BenefitDependent, BenefitClaimReference, BenefitCost


class BenefitPlanSerializer(serializers.ModelSerializer):
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = BenefitPlan
        fields = [
            'id', 'code', 'name', 'category', 'provider', 'coverage_details',
            'employee_contribution_rate', 'employer_contribution_rate',
            'max_dependents', 'is_active', 'enrollment_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'enrollment_count', 'created_at', 'updated_at']

    def get_enrollment_count(self, obj):
        return obj.enrollments.filter(status='ACTIVE').count()


class EligibilityRuleSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    grade_display = serializers.CharField(source='grade.grade_name', read_only=True, default='')

    class Meta:
        model = EligibilityRule
        fields = [
            'id', 'plan', 'plan_name', 'grade', 'grade_display',
            'employment_type', 'min_service_months', 'is_active',
        ]
        read_only_fields = ['id', 'plan_name', 'grade_display']


class BenefitDependentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenefitDependent
        fields = [
            'id', 'enrollment', 'name', 'relationship',
            'date_of_birth', 'id_number', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class BenefitEnrollmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_category = serializers.CharField(source='plan.category', read_only=True)
    approved_by_display = serializers.SerializerMethodField()
    dependents = BenefitDependentSerializer(many=True, read_only=True)

    class Meta:
        model = BenefitEnrollment
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'plan', 'plan_name', 'plan_category',
            'enrollment_date', 'end_date', 'status',
            'employee_contribution', 'employer_contribution',
            'workflow_request', 'approved_by', 'approved_by_display', 'approved_at',
            'dependents', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_number', 'plan_name', 'plan_category',
            'approved_by_display', 'approved_at', 'dependents', 'created_at', 'updated_at',
        ]

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username


class BenefitClaimReferenceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='enrollment.employee.person.legal_name', read_only=True)
    plan_name = serializers.CharField(source='enrollment.plan.name', read_only=True)
    approved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = BenefitClaimReference
        fields = [
            'id', 'enrollment', 'employee_name', 'plan_name',
            'claim_reference', 'claim_date', 'amount_claimed', 'amount_approved',
            'status', 'description', 'document',
            'approved_by', 'approved_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'plan_name', 'approved_by_display', 'created_at', 'updated_at',
        ]

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username


class BenefitCostSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='enrollment.employee.person.legal_name', read_only=True)
    plan_name = serializers.CharField(source='enrollment.plan.name', read_only=True)

    class Meta:
        model = BenefitCost
        fields = [
            'id', 'enrollment', 'employee_name', 'plan_name',
            'period_start', 'period_end',
            'employee_amount', 'employer_amount',
            'is_paid', 'payroll_run', 'recorded_at',
        ]
        read_only_fields = ['id', 'employee_name', 'plan_name', 'recorded_at']
