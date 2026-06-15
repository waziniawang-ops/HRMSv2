from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('requisitions', views.JobRequisitionViewSet, basename='requisition')
router.register('postings', views.JobPostingViewSet, basename='job-posting')
router.register('applicants', views.ApplicantViewSet, basename='applicant')
router.register('applications', views.ApplicationViewSet, basename='application')
router.register('interviews', views.InterviewViewSet, basename='interview')
router.register('interview-feedbacks', views.InterviewFeedbackViewSet, basename='interview-feedback')
router.register('offers', views.OfferViewSet, basename='offer')
router.register('my-documents', views.ApplicantDocumentViewSet, basename='applicant-document')

urlpatterns = [
    path('', include(router.urls)),
    path('jobs/', views.PublicJobListView.as_view(), name='public-jobs'),
    path('jobs/<uuid:pk>/', views.PublicJobDetailView.as_view(), name='public-job-detail'),
    path('applicant/profile/', views.ApplicantProfileView.as_view(), name='applicant-profile'),
]
