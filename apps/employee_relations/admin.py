from django.contrib import admin
from .models import ERCaseCategory, ERCase, CaseParty, CaseEvidence, CaseHearing, CaseOutcome, ERAppeal

admin.site.register(ERCaseCategory)
admin.site.register(ERCase)
admin.site.register(CaseParty)
admin.site.register(CaseEvidence)
admin.site.register(CaseHearing)
admin.site.register(CaseOutcome)
admin.site.register(ERAppeal)
