from django.contrib import admin
from .models import SalaryComponent, GradeBand, EmployeePackage, CompensationChange, BonusCycle, BonusAllocation

admin.site.register(SalaryComponent)
admin.site.register(GradeBand)
admin.site.register(EmployeePackage)
admin.site.register(CompensationChange)
admin.site.register(BonusCycle)
admin.site.register(BonusAllocation)
