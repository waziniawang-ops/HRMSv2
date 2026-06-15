from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('templates', views.OnboardingTemplateViewSet, basename='onboarding-template')
router.register('cases', views.OnboardingCaseViewSet, basename='onboarding-case')
router.register('tasks', views.OnboardingTaskViewSet, basename='onboarding-task')
router.register('documents', views.OnboardingDocumentViewSet, basename='onboarding-document')

urlpatterns = [
    path('', include(router.urls)),
]
