from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('cases', views.OffboardingCaseViewSet, basename='offboarding-case')
router.register('clearance-tasks', views.ClearanceTaskViewSet, basename='clearance-task')
router.register('asset-clearances', views.AssetClearanceViewSet, basename='asset-clearance')
router.register('access-revocations', views.AccessRevocationViewSet, basename='access-revocation')
router.register('exit-interviews', views.ExitInterviewViewSet, basename='exit-interview')
router.register('settlements', views.FinalSettlementViewSet, basename='final-settlement')

urlpatterns = [
    path('', include(router.urls)),
]
