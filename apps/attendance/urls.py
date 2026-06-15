from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('faces', views.FaceDescriptorViewSet, basename='face-descriptor')
router.register('records', views.AttendanceRecordViewSet, basename='attendance-record')

urlpatterns = [
    path('', include(router.urls)),
    path('verify/', views.FaceVerifyView.as_view(), name='face-verify'),
]
