from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('plans', views.SuccessionPlanViewSet, basename='succession-plan')
router.register('nominees', views.SuccessorNominationViewSet, basename='successor-nomination')
router.register('talent-pools', views.TalentPoolViewSet, basename='talent-pool')
router.register('talent-profiles', views.TalentProfileViewSet, basename='talent-profile')
router.register('development-plans', views.DevelopmentPlanViewSet, basename='development-plan')
router.register('development-activities', views.DevelopmentActivityViewSet, basename='development-activity')

urlpatterns = [
    path('', include(router.urls)),
]
