from django.contrib import admin
from .models import OrgUnit, CostCenter, JobFamily, Job, Grade, Position, Person, Employee, EmployeeAssignment


@admin.register(OrgUnit)
class OrgUnitAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'type', 'parent', 'status']
    list_filter = ['type', 'status']
    search_fields = ['code', 'name']
    raw_id_fields = ['parent', 'head_employee']


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'org_unit', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']
    raw_id_fields = ['org_unit']


@admin.register(JobFamily)
class JobFamilyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['job_code', 'job_title', 'job_family', 'is_active']
    list_filter = ['is_active', 'job_family']
    search_fields = ['job_code', 'job_title']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['grade_code', 'grade_name', 'level', 'pay_band_min', 'pay_band_max', 'is_active']
    list_filter = ['is_active']
    ordering = ['level']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['position_code', 'title', 'org_unit', 'grade', 'status', 'is_critical']
    list_filter = ['status', 'is_critical', 'org_unit']
    search_fields = ['position_code', 'title']
    raw_id_fields = ['job', 'org_unit', 'cost_center', 'grade', 'incumbent_employee', 'reporting_to']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['legal_name', 'email', 'phone', 'nationality']
    search_fields = ['legal_name', 'email']
    raw_id_fields = ['user']


class EmployeeAssignmentInline(admin.TabularInline):
    model = EmployeeAssignment
    fk_name = 'employee'
    extra = 0
    raw_id_fields = ['position', 'org_unit', 'grade', 'manager']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_number', 'full_name', 'employment_status', 'hire_date', 'org_unit', 'grade']
    list_filter = ['employment_status', 'org_unit', 'grade']
    search_fields = ['employee_number', 'person__legal_name', 'person__email']
    raw_id_fields = ['person', 'manager', 'position', 'org_unit', 'grade']
    inlines = [EmployeeAssignmentInline]
