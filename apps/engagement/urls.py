from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('survey-templates', views.SurveyTemplateViewSet, basename='survey-template')
router.register('surveys', views.EngagementSurveyViewSet, basename='engagement-survey')
router.register('survey-responses', views.SurveyResponseViewSet, basename='survey-response')
router.register('action-plans', views.ActionPlanViewSet, basename='action-plan')
router.register('recognition-types', views.RecognitionTypeViewSet, basename='recognition-type')
router.register('awards', views.RecognitionAwardViewSet, basename='recognition-award')
router.register('nominations', views.RecognitionNominationViewSet, basename='recognition-nomination')
router.register('points', views.EmployeePointsViewSet, basename='employee-points')

urlpatterns = [
    path('', include(router.urls)),
]
