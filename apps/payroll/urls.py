from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('payroll-calendars', views.PayrollCalendarViewSet, basename='payroll-calendar')
router.register('payroll-elements', views.PayrollElementViewSet, basename='payroll-element')
router.register('payroll-employee-profiles', views.EmployeePayrollProfileViewSet, basename='payroll-employee-profile')
router.register('payroll-runs', views.PayrollRunViewSet, basename='payroll-run')
router.register('payslip-lines', views.PayslipLineViewSet, basename='payslip-line')
router.register('payslips', views.PayslipViewSet, basename='payslip')
router.register('payroll-adjustments', views.PayrollAdjustmentViewSet, basename='payroll-adjustment')
router.register('payroll-gl-postings', views.PayrollGLPostingViewSet, basename='payroll-gl-posting')

urlpatterns = [
    path('', include(router.urls)),
]
