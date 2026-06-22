from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('salary-components', views.SalaryComponentViewSet, basename='salary-component')
router.register('grade-bands', views.GradeBandViewSet, basename='grade-band')
router.register('employee-packages', views.EmployeePackageViewSet, basename='employee-package')
router.register('compensation-changes', views.CompensationChangeViewSet, basename='comp-change')
router.register('bonus-cycles', views.BonusCycleViewSet, basename='bonus-cycle')
router.register('bonus-allocations', views.BonusAllocationViewSet, basename='bonus-allocation')

urlpatterns = [
    path('', include(router.urls)),
]
