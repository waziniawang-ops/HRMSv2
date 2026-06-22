from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('rules', views.WorkflowRuleViewSet, basename='workflow-rule')
router.register('attachments', views.WorkflowAttachmentViewSet, basename='workflow-attachment')
router.register('actors', views.WorkflowActorViewSet, basename='workflow-actor')

urlpatterns = [
    path('', include(router.urls)),
    path('requests/', views.WorkflowRequestListView.as_view(), name='workflow-request-list'),
    path('requests/<uuid:pk>/', views.WorkflowRequestDetailView.as_view(), name='workflow-request-detail'),
    path('requests/<uuid:pk>/submit/', views.WorkflowSubmitView.as_view(), name='workflow-submit'),
    path('requests/<uuid:pk>/approve/', views.WorkflowApproveView.as_view(), name='workflow-approve'),
    path('requests/<uuid:pk>/reject/', views.WorkflowRejectView.as_view(), name='workflow-reject'),
    path('requests/<uuid:pk>/return/', views.WorkflowReturnView.as_view(), name='workflow-return'),
    path('requests/<uuid:pk>/comments/', views.WorkflowAddCommentView.as_view(), name='workflow-comment'),
]
