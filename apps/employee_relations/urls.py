from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.ERCaseCategoryViewSet, basename='er-case-category')
router.register('cases', views.ERCaseViewSet, basename='er-case')
router.register('parties', views.CasePartyViewSet, basename='case-party')
router.register('evidence', views.CaseEvidenceViewSet, basename='case-evidence')
router.register('hearings', views.CaseHearingViewSet, basename='case-hearing')
router.register('outcomes', views.CaseOutcomeViewSet, basename='case-outcome')
router.register('appeals', views.ERAppealViewSet, basename='er-appeal')

urlpatterns = [
    path('', include(router.urls)),
]
