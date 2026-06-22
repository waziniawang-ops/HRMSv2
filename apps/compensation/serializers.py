from rest_framework import serializers
from .models import SalaryComponent, GradeBand, EmployeePackage, CompensationChange, BonusCycle, BonusAllocation


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = [
            'id', 'code', 'name', 'category', 'default_amount',
            'is_pensionable', 'is_taxable', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class GradeBandSerializer(serializers.ModelSerializer):
    grade_display = serializers.CharField(source='grade.grade_name', read_only=True)
    component_display = serializers.CharField(source='component.name', read_only=True)

    class Meta:
        model = GradeBand
        fields = [
            'id', 'grade', 'grade_display', 'component', 'component_display',
            'min_amount', 'mid_amount', 'max_amount', 'currency', 'is_active', 'updated_at',
        ]
        read_only_fields = ['id', 'grade_display', 'component_display', 'updated_at']


class EmployeePackageSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    approved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = EmployeePackage
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'effective_date', 'valid_to', 'total_ctc', 'currency', 'status',
            'components', 'workflow_request', 'approved_by', 'approved_by_display',
            'approved_at', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_number', 'approved_by_display',
            'approved_at', 'created_at', 'updated_at',
        ]

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username


class CompensationChangeSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = CompensationChange
        fields = [
            'id', 'employee', 'employee_name', 'change_type',
            'previous_package', 'new_package', 'effective_date', 'reason',
            'status', 'workflow_request', 'created_by', 'created_by_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'employee_name', 'created_by_display', 'created_at', 'updated_at']

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username


class BonusCycleSerializer(serializers.ModelSerializer):
    created_by_display = serializers.SerializerMethodField()
    allocation_count = serializers.SerializerMethodField()

    class Meta:
        model = BonusCycle
        fields = [
            'id', 'name', 'year', 'bonus_type', 'budget_pool', 'currency',
            'status', 'approved_by', 'approved_at', 'created_by', 'created_by_display',
            'allocation_count', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'approved_at', 'created_by_display', 'allocation_count', 'created_at', 'updated_at',
        ]

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_allocation_count(self, obj):
        return obj.allocations.count()


class BonusAllocationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    cycle_name = serializers.CharField(source='cycle.name', read_only=True)
    approved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = BonusAllocation
        fields = [
            'id', 'cycle', 'cycle_name', 'employee', 'employee_name', 'employee_number',
            'recommended_amount', 'approved_amount', 'performance_rating', 'status',
            'notes', 'recommended_by', 'approved_by', 'approved_by_display', 'created_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_number', 'cycle_name', 'approved_by_display', 'created_at',
        ]

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username
