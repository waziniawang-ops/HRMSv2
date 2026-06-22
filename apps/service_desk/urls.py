from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.TicketCategoryViewSet, basename='ticket-category')
router.register('tickets', views.HRTicketViewSet, basename='hr-ticket')
router.register('comments', views.TicketCommentViewSet, basename='ticket-comment')
router.register('knowledge-categories', views.KnowledgeCategoryViewSet, basename='knowledge-category')
router.register('knowledge-articles', views.KnowledgeArticleViewSet, basename='knowledge-article')
router.register('satisfaction-surveys', views.SatisfactionSurveyViewSet, basename='satisfaction-survey')

urlpatterns = [
    path('', include(router.urls)),
]
