from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('claim-types', views.ClaimTypeViewSet, basename='claim-type')
router.register('expense-policies', views.ExpensePolicyViewSet, basename='expense-policy')
router.register('claims', views.ClaimRequestViewSet, basename='claim-request')
router.register('claim-lines', views.ClaimLineViewSet, basename='claim-line')
router.register('claim-receipts', views.ClaimReceiptViewSet, basename='claim-receipt')
router.register('travel-requests', views.TravelRequestViewSet, basename='travel-request')

urlpatterns = [
    path('', include(router.urls)),
]
