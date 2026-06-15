from django.contrib import admin
from .models import FaceDescriptor, AttendanceRecord


@admin.register(FaceDescriptor)
class FaceDescriptorAdmin(admin.ModelAdmin):
    list_display = ['employee', 'enrolled_at', 'enrolled_by']
    search_fields = ['employee__employee_number', 'employee__person__legal_name']
    readonly_fields = ['enrolled_at']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'hours_worked', 'method']
    list_filter = ['method', 'date']
    search_fields = ['employee__employee_number', 'employee__person__legal_name']
    date_hierarchy = 'date'
