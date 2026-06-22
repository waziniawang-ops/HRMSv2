from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('incident-types', views.HSEIncidentTypeViewSet, basename='hse-incident-type')
router.register('incidents', views.HSEIncidentViewSet, basename='hse-incident')
router.register('investigations', views.IncidentInvestigationViewSet, basename='hse-investigation')
router.register('corrective-actions', views.CorrectiveActionViewSet, basename='hse-corrective-action')
router.register('wellbeing-programs', views.WellbeingProgramViewSet, basename='wellbeing-program')
router.register('wellbeing-enrollments', views.WellbeingEnrollmentViewSet, basename='wellbeing-enrollment')
router.register('medical-fitness', views.MedicalFitnessRecordViewSet, basename='medical-fitness')

urlpatterns = [
    path('', include(router.urls)),
]
