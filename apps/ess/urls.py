from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('request-types', views.ESSRequestTypeViewSet, basename='ess-request-type')
router.register('requests', views.ESSRequestViewSet, basename='ess-request')
router.register('profile-changes', views.ProfileChangeRequestViewSet, basename='profile-change')
router.register('policy-acknowledgements', views.PolicyAcknowledgementViewSet, basename='policy-ack')
router.register('delegations', views.ManagerDelegationViewSet, basename='delegation')

urlpatterns = [
    path('', include(router.urls)),
]
