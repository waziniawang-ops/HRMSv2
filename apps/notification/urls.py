from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('templates', views.NotificationTemplateViewSet, basename='notification-template')
router.register('inbox', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
]
