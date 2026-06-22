from django.contrib import admin
from .models import (
    PayrollCalendar, PayrollElement, EmployeePayrollProfile,
    PayrollRun, PayslipLine, Payslip, PayrollAdjustment, PayrollGLPosting,
)

admin.site.register(PayrollCalendar)
admin.site.register(PayrollElement)
admin.site.register(EmployeePayrollProfile)
admin.site.register(PayrollRun)
admin.site.register(PayslipLine)
admin.site.register(Payslip)
admin.site.register(PayrollAdjustment)
admin.site.register(PayrollGLPosting)
