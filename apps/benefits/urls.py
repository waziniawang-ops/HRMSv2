from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('plans', views.BenefitPlanViewSet, basename='benefit-plan')
router.register('eligibility-rules', views.EligibilityRuleViewSet, basename='benefit-eligibility-rule')
router.register('enrollments', views.BenefitEnrollmentViewSet, basename='benefit-enrollment')
router.register('dependents', views.BenefitDependentViewSet, basename='benefit-dependent')
router.register('claims', views.BenefitClaimReferenceViewSet, basename='benefit-claim')
router.register('costs', views.BenefitCostViewSet, basename='benefit-cost')

urlpatterns = [
    path('', include(router.urls)),
]
