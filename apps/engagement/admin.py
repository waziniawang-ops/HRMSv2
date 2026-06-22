from django.contrib import admin
from .models import (
    SurveyTemplate, EngagementSurvey, SurveyResponse,
    ActionPlan, RecognitionType, RecognitionAward,
    RecognitionNomination, EmployeePoints,
)

admin.site.register(SurveyTemplate)
admin.site.register(EngagementSurvey)
admin.site.register(SurveyResponse)
admin.site.register(ActionPlan)
admin.site.register(RecognitionType)
admin.site.register(RecognitionAward)
admin.site.register(RecognitionNomination)
admin.site.register(EmployeePoints)
