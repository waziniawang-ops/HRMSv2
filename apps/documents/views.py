from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsHRStaff, IsInternalUser
from apps.audit.mixins import AuditMixin
from apps.audit.utils import log_action

from .models import DocCategory, DocTemplate, DocRecord, DocPolicy, DocAcknowledgement, RetentionRule
from .serializers import (
    DocCategorySerializer, DocTemplateSerializer, DocRecordSerializer,
    DocPolicySerializer, DocAcknowledgementSerializer, RetentionRuleSerializer,
)


class DocCategoryViewSet(AuditMixin, ModelViewSet):
    queryset = DocCategory.objects.all().order_by('name')
    serializer_class = DocCategorySerializer
    filterset_fields = ['is_confidential', 'is_active']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class DocTemplateViewSet(AuditMixin, ModelViewSet):
    queryset = DocTemplate.objects.select_related('category', 'created_by').order_by('name')
    serializer_class = DocTemplateSerializer
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class DocRecordViewSet(AuditMixin, ModelViewSet):
    queryset = DocRecord.objects.select_related(
        'category', 'employee__person', 'template', 'uploaded_by'
    ).order_by('-created_at')
    serializer_class = DocRecordSerializer
    filterset_fields = ['status', 'category', 'employee', 'is_confidential']
    search_fields = ['title']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class DocPolicyViewSet(AuditMixin, ModelViewSet):
    queryset = DocPolicy.objects.select_related('category', 'created_by', 'published_by').order_by('-created_at')
    serializer_class = DocPolicySerializer
    filterset_fields = ['status', 'category', 'requires_acknowledgement']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'pending_acknowledgements']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def publish(self, request, pk=None):
        policy = self.get_object()
        if policy.status not in [DocPolicy.STATUS_DRAFT, DocPolicy.STATUS_UNDER_REVIEW]:
            return Response({'detail': 'Only draft or under-review policies can be published.'}, status=400)
        policy.status = DocPolicy.STATUS_PUBLISHED
        policy.published_at = timezone.now()
        policy.published_by = request.user
        policy.save(update_fields=['status', 'published_at', 'published_by'])
        log_action(request, 'PUBLISH', 'DocPolicy', str(policy.id), module='documents')
        return Response(DocPolicySerializer(policy, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsInternalUser])
    def acknowledge(self, request, pk=None):
        policy = self.get_object()
        if policy.status != DocPolicy.STATUS_PUBLISHED:
            return Response({'detail': 'Policy must be published to acknowledge.'}, status=400)
        try:
            employee = request.user.person.employee
        except Exception:
            return Response({'detail': 'No employee record found for current user.'}, status=400)
        ack, created = DocAcknowledgement.objects.get_or_create(
            policy=policy,
            employee=employee,
            version_acknowledged=policy.version,
            defaults={
                'ip_address': request.META.get('REMOTE_ADDR'),
            }
        )
        if not created:
            return Response({'detail': 'Already acknowledged this version.'}, status=400)
        log_action(request, 'ACKNOWLEDGE', 'DocPolicy', str(policy.id), module='documents')
        return Response(DocAcknowledgementSerializer(ack).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsInternalUser])
    def pending_acknowledgements(self, request):
        try:
            employee = request.user.person.employee
        except Exception:
            return Response([])
        acknowledged_ids = DocAcknowledgement.objects.filter(
            employee=employee
        ).values_list('policy_id', flat=True)
        pending = DocPolicy.objects.filter(
            status=DocPolicy.STATUS_PUBLISHED,
            requires_acknowledgement=True,
        ).exclude(id__in=acknowledged_ids)
        return Response(DocPolicySerializer(pending, many=True, context={'request': request}).data)


class DocAcknowledgementViewSet(AuditMixin, ModelViewSet):
    queryset = DocAcknowledgement.objects.select_related(
        'policy', 'employee__person'
    ).order_by('-acknowledged_at')
    serializer_class = DocAcknowledgementSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['policy', 'employee']
    http_method_names = ['get', 'head', 'options']


class RetentionRuleViewSet(AuditMixin, ModelViewSet):
    queryset = RetentionRule.objects.select_related('category').order_by('category__name')
    serializer_class = RetentionRuleSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['category', 'is_active', 'disposal_action']
