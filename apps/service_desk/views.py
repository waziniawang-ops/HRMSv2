from django.db.models import F
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.audit.mixins import AuditMixin
from apps.accounts.permissions import IsHRStaff, IsInternalUser
from apps.audit.utils import log_action

from .models import TicketCategory, HRTicket, TicketComment, KnowledgeCategory, KnowledgeArticle, SatisfactionSurvey
from .serializers import (
    TicketCategorySerializer, HRTicketSerializer, TicketCommentSerializer,
    KnowledgeCategorySerializer, KnowledgeArticleSerializer, SatisfactionSurveySerializer,
)


class TicketCategoryViewSet(AuditMixin, ModelViewSet):
    queryset = TicketCategory.objects.all().order_by('name')
    serializer_class = TicketCategorySerializer
    filterset_fields = ['is_active', 'is_confidential', 'parent']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class HRTicketViewSet(AuditMixin, ModelViewSet):
    queryset = HRTicket.objects.select_related(
        'category', 'raised_by', 'assigned_to', 'on_behalf_of__person'
    ).prefetch_related('comments').order_by('-created_at')
    serializer_class = HRTicketSerializer
    filterset_fields = ['status', 'priority', 'category', 'assigned_to']
    search_fields = ['ticket_number', 'subject']

    def get_permissions(self):
        return [IsInternalUser()]

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required.'}, status=400)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            agent = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        ticket.assigned_to = agent
        ticket.status = HRTicket.STATUS_IN_PROGRESS
        ticket.save(update_fields=['assigned_to', 'status', 'updated_at'])
        log_action(request, 'ASSIGN', 'HRTicket', str(ticket.id), module='service_desk')
        return Response(HRTicketSerializer(ticket).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status in [HRTicket.STATUS_RESOLVED, HRTicket.STATUS_CLOSED, HRTicket.STATUS_CANCELLED]:
            return Response({'detail': 'Ticket is already resolved or closed.'}, status=400)
        ticket.status = HRTicket.STATUS_RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.resolution_notes = request.data.get('resolution_notes', '')
        ticket.save(update_fields=['status', 'resolved_at', 'resolution_notes', 'updated_at'])
        log_action(request, 'RESOLVE', 'HRTicket', str(ticket.id), module='service_desk')
        return Response(HRTicketSerializer(ticket).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def close(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == HRTicket.STATUS_CANCELLED:
            return Response({'detail': 'Cannot close a cancelled ticket.'}, status=400)
        ticket.status = HRTicket.STATUS_CLOSED
        ticket.closed_at = timezone.now()
        if not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        ticket.save(update_fields=['status', 'closed_at', 'resolved_at', 'updated_at'])
        log_action(request, 'CLOSE', 'HRTicket', str(ticket.id), module='service_desk')
        return Response(HRTicketSerializer(ticket).data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketCommentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['get'])
    def my_tickets(self, request):
        qs = HRTicket.objects.filter(raised_by=request.user).order_by('-created_at')
        serializer = HRTicketSerializer(qs, many=True)
        return Response(serializer.data)


class TicketCommentViewSet(AuditMixin, ModelViewSet):
    queryset = TicketComment.objects.select_related('author', 'ticket').order_by('created_at')
    serializer_class = TicketCommentSerializer
    filterset_fields = ['ticket', 'is_internal', 'author']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_permissions(self):
        return [IsInternalUser()]


class KnowledgeCategoryViewSet(AuditMixin, ModelViewSet):
    queryset = KnowledgeCategory.objects.all().order_by('name')
    serializer_class = KnowledgeCategorySerializer
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class KnowledgeArticleViewSet(AuditMixin, ModelViewSet):
    queryset = KnowledgeArticle.objects.select_related('category', 'author').order_by('-published_at')
    serializer_class = KnowledgeArticleSerializer
    filterset_fields = ['status', 'category', 'is_featured', 'author']
    search_fields = ['title', 'content']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'increment_views']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = KnowledgeArticle.STATUS_PUBLISHED
        article.published_at = timezone.now()
        article.save(update_fields=['status', 'published_at', 'updated_at'])
        log_action(request, 'PUBLISH', 'KnowledgeArticle', str(article.id), module='service_desk')
        return Response(KnowledgeArticleSerializer(article).data)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        article = self.get_object()
        KnowledgeArticle.objects.filter(pk=article.pk).update(views_count=F('views_count') + 1)
        article.refresh_from_db(fields=['views_count'])
        return Response({'views_count': article.views_count})


class SatisfactionSurveyViewSet(AuditMixin, ModelViewSet):
    queryset = SatisfactionSurvey.objects.select_related('ticket').order_by('-submitted_at')
    serializer_class = SatisfactionSurveySerializer
    filterset_fields = ['ticket']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_permissions(self):
        return [IsInternalUser()]
