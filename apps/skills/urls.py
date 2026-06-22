from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.SkillCategoryViewSet, basename='skill-category')
router.register('skills', views.SkillViewSet, basename='skill')
router.register('proficiency-scales', views.ProficiencyScaleViewSet, basename='proficiency-scale')
router.register('job-requirements', views.JobSkillRequirementViewSet, basename='job-skill-requirement')
router.register('employee-skills', views.EmployeeSkillViewSet, basename='employee-skill')
router.register('evidence', views.SkillEvidenceViewSet, basename='skill-evidence')
router.register('gap-analyses', views.SkillGapAnalysisViewSet, basename='skill-gap-analysis')
router.register('gaps', views.SkillGapViewSet, basename='skill-gap')

urlpatterns = [
    path('', include(router.urls)),
]
