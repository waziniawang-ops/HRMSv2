from rest_framework import serializers
from .models import (
    PayrollCalendar, PayrollElement, EmployeePayrollProfile,
    PayrollRun, PayslipLine, Payslip, PayrollAdjustment, PayrollGLPosting,
)


class PayrollCalendarSerializer(serializers.ModelSerializer):
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = PayrollCalendar
        fields = [
            'id', 'code', 'name', 'pay_group', 'frequency', 'is_active',
            'created_by', 'created_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_display']

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username


class PayrollElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollElement
        fields = [
            'id', 'code', 'name', 'category', 'is_taxable', 'is_pensionable',
            'formula', 'display_order', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EmployeePayrollProfileSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    calendar_display = serializers.CharField(source='calendar.name', read_only=True)

    class Meta:
        model = EmployeePayrollProfile
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'calendar', 'calendar_display',
            'bank_name', 'bank_account_number', 'bank_code',
            'is_active', 'workflow_request', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'employee_name', 'employee_number', 'calendar_display', 'created_at', 'updated_at']


class PayrollRunSerializer(serializers.ModelSerializer):
    calendar_display = serializers.CharField(source='calendar.name', read_only=True)
    created_by_display = serializers.SerializerMethodField()
    approved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = PayrollRun
        fields = [
            'id', 'calendar', 'calendar_display', 'period_start', 'period_end',
            'status', 'pay_date', 'total_gross', 'total_deductions', 'total_net',
            'employee_count', 'processed_by', 'approved_by', 'approved_by_display',
            'approved_at', 'locked_at', 'workflow_request',
            'created_by', 'created_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'total_gross', 'total_deductions', 'total_net', 'employee_count',
            'approved_at', 'locked_at', 'calendar_display', 'created_by_display',
            'approved_by_display', 'created_at', 'updated_at',
        ]

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username


class PayslipLineSerializer(serializers.ModelSerializer):
    element_display = serializers.CharField(source='element.name', read_only=True)
    element_category = serializers.CharField(source='element.category', read_only=True)
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)

    class Meta:
        model = PayslipLine
        fields = [
            'id', 'payroll_run', 'employee', 'employee_name',
            'element', 'element_display', 'element_category',
            'amount', 'taxable_amount', 'is_deduction',
        ]
        read_only_fields = ['id', 'element_display', 'element_category', 'employee_name']


class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    payroll_period = serializers.SerializerMethodField()

    class Meta:
        model = Payslip
        fields = [
            'id', 'payroll_run', 'payroll_period', 'employee', 'employee_name', 'employee_number',
            'basic_pay', 'total_allowances', 'gross_pay', 'total_deductions',
            'tax_amount', 'pension_amount', 'net_pay', 'payslip_date',
            'is_locked', 'generated_at',
        ]
        read_only_fields = ['id', 'employee_name', 'employee_number', 'payroll_period', 'generated_at']

    def get_payroll_period(self, obj):
        return f"{obj.payroll_run.period_start} to {obj.payroll_run.period_end}"


class PayrollAdjustmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    element_display = serializers.CharField(source='element.name', read_only=True)
    approved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = PayrollAdjustment
        fields = [
            'id', 'payroll_run', 'employee', 'employee_name',
            'element', 'element_display', 'amount', 'reason', 'status',
            'approved_by', 'approved_by_display', 'workflow_request',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'employee_name', 'element_display', 'approved_by_display', 'created_at', 'updated_at']

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username


class PayrollGLPostingSerializer(serializers.ModelSerializer):
    cost_center_display = serializers.CharField(source='cost_center.name', read_only=True, default='')

    class Meta:
        model = PayrollGLPosting
        fields = [
            'id', 'payroll_run', 'gl_account', 'description', 'amount',
            'cost_center', 'cost_center_display', 'posting_date', 'is_posted', 'posted_at',
        ]
        read_only_fields = ['id', 'cost_center_display', 'posted_at']
