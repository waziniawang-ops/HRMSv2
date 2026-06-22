from rest_framework import serializers
from .models import OrgUnit, CostCenter, JobFamily, Job, Grade, Position, Person, Employee, EmployeeAssignment, SystemSetting, Location, EmploymentContract


class OrgUnitSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True, default=None)
    head_employee_display = serializers.CharField(source='head_employee.person.legal_name', read_only=True, allow_null=True, default=None)
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = OrgUnit
        fields = ['id', 'code', 'name', 'type', 'parent', 'parent_name', 'head_employee', 'head_employee_display', 'status', 'created_by', 'created_by_display', 'created_at']
        read_only_fields = ['id', 'created_at', 'created_by', 'parent_name', 'head_employee_display', 'created_by_display']

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = ['id', 'code', 'name', 'org_unit', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class JobFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobFamily
        fields = ['id', 'code', 'name', 'description']
        read_only_fields = ['id']


class JobSerializer(serializers.ModelSerializer):
    job_family_display = serializers.CharField(source='job_family.name', read_only=True)

    class Meta:
        model = Job
        fields = ['id', 'job_code', 'job_title', 'job_family', 'job_family_display', 'description', 'is_active']
        read_only_fields = ['id']


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'grade_code', 'grade_name', 'pay_band_min', 'pay_band_max', 'level', 'is_active']
        read_only_fields = ['id']


class PositionSerializer(serializers.ModelSerializer):
    job_display = serializers.CharField(source='job.job_title', read_only=True)
    org_unit_display = serializers.CharField(source='org_unit.name', read_only=True)
    grade_display = serializers.CharField(source='grade.grade_name', read_only=True)
    reporting_to_display = serializers.CharField(source='reporting_to.title', read_only=True, allow_null=True, default=None)
    location_display = serializers.CharField(source='location.name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = Position
        fields = [
            'id', 'position_code', 'title', 'job', 'job_display',
            'org_unit', 'org_unit_display', 'cost_center', 'grade', 'grade_display',
            'location', 'location_display',
            'status', 'is_critical', 'headcount_budget', 'incumbent_employee',
            'reporting_to', 'reporting_to_display', 'workflow_request', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'workflow_request', 'reporting_to_display', 'location_display', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = [
            'id', 'legal_name', 'preferred_name', 'date_of_birth',
            'email', 'personal_email', 'phone', 'address',
            'nationality', 'gender', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    person_detail = PersonSerializer(source='person', read_only=True)
    position_display = serializers.CharField(source='position.title', read_only=True, default='')
    org_unit_display = serializers.CharField(source='org_unit.name', read_only=True, default='')
    grade_display = serializers.CharField(source='grade.grade_name', read_only=True, default='')
    manager_display = serializers.CharField(source='manager.person.legal_name', read_only=True, default='')

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_number', 'full_name', 'person', 'person_detail',
            'hire_date', 'employment_status', 'employment_type', 'manager', 'manager_display',
            'position', 'position_display', 'org_unit', 'org_unit_display',
            'grade', 'grade_display', 'termination_date', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EmployeeAssignmentSerializer(serializers.ModelSerializer):
    employee_display = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    position_display = serializers.CharField(source='position.title', read_only=True)
    org_unit_display = serializers.CharField(source='org_unit.name', read_only=True)
    grade_display = serializers.CharField(source='grade.grade_name', read_only=True)
    manager_display = serializers.CharField(source='manager.person.legal_name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = EmployeeAssignment
        fields = [
            'id', 'employee', 'employee_display', 'employee_number',
            'position', 'position_display', 'org_unit', 'org_unit_display',
            'grade', 'grade_display', 'manager', 'manager_display',
            'is_primary', 'valid_from', 'valid_to', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'employee_display', 'employee_number', 'position_display', 'org_unit_display', 'grade_display', 'manager_display']


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['key', 'value', 'description', 'updated_at']
        read_only_fields = ['key', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'code', 'name', 'address', 'city', 'country', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmploymentContractSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = EmploymentContract
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'contract_type', 'start_date', 'end_date',
            'notice_period_days', 'probation_period_days',
            'status', 'contract_document', 'is_signed', 'signed_at',
            'notes', 'workflow_request', 'created_by', 'created_by_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'workflow_request', 'created_at', 'updated_at']

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
