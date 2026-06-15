from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('cycles', views.PerformanceCycleViewSet, basename='performance-cycle')
router.register('competency-models', views.CompetencyModelViewSet, basename='competency-model')
router.register('competencies', views.CompetencyViewSet, basename='competency')
router.register('goal-plans', views.GoalPlanViewSet, basename='goal-plan')
router.register('goals', views.GoalViewSet, basename='goal')
router.register('goal-progress', views.GoalProgressViewSet, basename='goal-progress')
router.register('review-forms', views.ReviewFormViewSet, basename='review-form')
router.register('review-ratings', views.ReviewRatingViewSet, basename='review-rating')
router.register('calibration-sessions', views.CalibrationSessionViewSet, basename='calibration-session')
router.register('calibrated-ratings', views.CalibratedRatingViewSet, basename='calibrated-rating')
router.register('final-outcomes', views.FinalOutcomeViewSet, basename='final-outcome')
router.register('improvement-plans', views.ImprovementPlanViewSet, basename='improvement-plan')

urlpatterns = [
    path('', include(router.urls)),
]
