from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('plans', views.WorkforcePlanViewSet, basename='workforce-plan')
router.register('attendance-policies', views.AttendancePolicyViewSet, basename='attendance-policy')
router.register('attendance', views.AttendanceLogViewSet, basename='attendance-log')
router.register('leave-types', views.LeaveTypeViewSet, basename='leave-type')
router.register('leave-balances', views.LeaveBalanceViewSet, basename='leave-balance')
router.register('leave-requests', views.LeaveRequestViewSet, basename='leave-request')
router.register('overtime', views.OvertimeRequestViewSet, basename='overtime-request')
router.register('rosters', views.RosterViewSet, basename='roster')
router.register('transfers', views.TransferViewSet, basename='transfer')
router.register('separations', views.SeparationViewSet, basename='separation')

urlpatterns = [
    path('', include(router.urls)),
]
