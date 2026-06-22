from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('org-units', views.OrgUnitViewSet, basename='org-unit')
router.register('cost-centers', views.CostCenterViewSet, basename='cost-center')
router.register('job-families', views.JobFamilyViewSet, basename='job-family')
router.register('jobs', views.JobViewSet, basename='job')
router.register('grades', views.GradeViewSet, basename='grade')
router.register('positions', views.PositionViewSet, basename='position')
router.register('persons', views.PersonViewSet, basename='person')
router.register('employees', views.EmployeeViewSet, basename='employee')
router.register('assignments', views.EmployeeAssignmentViewSet, basename='assignment')
router.register('settings', views.SystemSettingViewSet, basename='system-setting')
router.register('locations', views.LocationViewSet, basename='location')
router.register('contracts', views.EmploymentContractViewSet, basename='employment-contract')

urlpatterns = [
    path('settings/currency/', views.CurrencySettingView.as_view(), name='currency-setting'),
    path('', include(router.urls)),
]
