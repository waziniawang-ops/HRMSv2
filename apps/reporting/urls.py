from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.HRDashboardView.as_view(), name='hr-dashboard'),
    path('headcount/', views.HeadcountByOrgUnitView.as_view(), name='headcount-by-org'),
    path('hiring-funnel/', views.HiringFunnelView.as_view(), name='hiring-funnel'),
    path('time-to-hire/', views.TimeToHireView.as_view(), name='time-to-hire'),
    path('succession-risk/', views.SuccessionRiskView.as_view(), name='succession-risk'),
    path('performance-distribution/', views.PerformanceDistributionView.as_view(), name='performance-distribution'),
    path('learning-compliance/', views.LearningComplianceView.as_view(), name='learning-compliance'),
    path('attrition/', views.AttritionReportView.as_view(), name='attrition-report'),
]
