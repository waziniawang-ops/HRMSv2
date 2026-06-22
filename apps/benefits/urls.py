from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('benefit-plans', views.BenefitPlanViewSet, basename='benefit-plan')
router.register('eligibility-rules', views.EligibilityRuleViewSet, basename='benefit-eligibility-rule')
router.register('benefit-enrollments', views.BenefitEnrollmentViewSet, basename='benefit-enrollment')
router.register('benefit-dependents', views.BenefitDependentViewSet, basename='benefit-dependent')
router.register('benefit-claims', views.BenefitClaimReferenceViewSet, basename='benefit-claim')
router.register('benefit-costs', views.BenefitCostViewSet, basename='benefit-cost')

urlpatterns = [
    path('', include(router.urls)),
]
