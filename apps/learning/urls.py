from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('courses', views.CourseViewSet, basename='course')
router.register('learning-paths', views.LearningPathViewSet, basename='learning-path')
router.register('assignment-rules', views.AssignmentRuleViewSet, basename='assignment-rule')
router.register('assignments', views.LearningAssignmentViewSet, basename='learning-assignment')
router.register('sessions', views.CourseSessionViewSet, basename='course-session')
router.register('enrollments', views.EnrollmentViewSet, basename='enrollment')
router.register('assessments', views.AssessmentViewSet, basename='assessment')
router.register('completions', views.CourseCompletionViewSet, basename='course-completion')
router.register('training-requests', views.TrainingRequestViewSet, basename='training-request')
router.register('skill-gaps', views.SkillGapViewSet, basename='skill-gap')

urlpatterns = [
    path('', include(router.urls)),
]
