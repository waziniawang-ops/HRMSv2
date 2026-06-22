from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('calendars', views.PayrollCalendarViewSet, basename='payroll-calendar')
router.register('elements', views.PayrollElementViewSet, basename='payroll-element')
router.register('employee-profiles', views.EmployeePayrollProfileViewSet, basename='payroll-employee-profile')
router.register('runs', views.PayrollRunViewSet, basename='payroll-run')
router.register('payslip-lines', views.PayslipLineViewSet, basename='payslip-line')
router.register('payslips', views.PayslipViewSet, basename='payslip')
router.register('adjustments', views.PayrollAdjustmentViewSet, basename='payroll-adjustment')
router.register('gl-postings', views.PayrollGLPostingViewSet, basename='payroll-gl-posting')

urlpatterns = [
    path('', include(router.urls)),
]
