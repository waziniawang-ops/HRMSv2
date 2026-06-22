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
router.register('shift-templates', views.ShiftTemplateViewSet, basename='shift-template')
router.register('attendance-exceptions', views.AttendanceExceptionViewSet, basename='attendance-exception')
router.register('holiday-calendars', views.HolidayCalendarViewSet, basename='holiday-calendar')
router.register('holiday-entries', views.HolidayCalendarEntryViewSet, basename='holiday-entry')
router.register('leave-policies', views.LeavePolicyViewSet, basename='leave-policy')
router.register('leave-documents', views.LeaveDocumentViewSet, basename='leave-document')

urlpatterns = [
    path('', include(router.urls)),
]
