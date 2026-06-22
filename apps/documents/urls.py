from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.DocCategoryViewSet, basename='doc-category')
router.register('templates', views.DocTemplateViewSet, basename='doc-template')
router.register('records', views.DocRecordViewSet, basename='doc-record')
router.register('policies', views.DocPolicyViewSet, basename='doc-policy')
router.register('acknowledgements', views.DocAcknowledgementViewSet, basename='doc-acknowledgement')
router.register('retention-rules', views.RetentionRuleViewSet, basename='retention-rule')

urlpatterns = [
    path('', include(router.urls)),
]
