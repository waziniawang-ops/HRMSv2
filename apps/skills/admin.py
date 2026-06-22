from django.contrib import admin
from .models import (
    SkillCategory, Skill, ProficiencyScale, JobSkillRequirement,
    EmployeeSkill, SkillEvidence, SkillGapAnalysis, SkillGap,
)

admin.site.register(SkillCategory)
admin.site.register(Skill)
admin.site.register(ProficiencyScale)
admin.site.register(JobSkillRequirement)
admin.site.register(EmployeeSkill)
admin.site.register(SkillEvidence)
admin.site.register(SkillGapAnalysis)
admin.site.register(SkillGap)
