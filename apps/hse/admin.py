from django.contrib import admin
from .models import (
    HSEIncidentType, HSEIncident, IncidentInvestigation,
    CorrectiveAction, WellbeingProgram, WellbeingEnrollment, MedicalFitnessRecord,
)

admin.site.register(HSEIncidentType)
admin.site.register(HSEIncident)
admin.site.register(IncidentInvestigation)
admin.site.register(CorrectiveAction)
admin.site.register(WellbeingProgram)
admin.site.register(WellbeingEnrollment)
admin.site.register(MedicalFitnessRecord)
