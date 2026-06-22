from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.audit.mixins import AuditMixin
from apps.accounts.permissions import IsHRStaff, IsInternalUser
from apps.audit.utils import log_action

from .models import ESSRequestType, ESSRequest, ProfileChangeRequest, ManagerDelegation
from .serializers import (
    ESSRequestTypeSerializer, ESSRequestSerializer,
    ProfileChangeRequestSerializer, PolicyAcknowledgementSerializer,
    ManagerDelegationSerializer,
)
from apps.documents.models import DocAcknowledgement as PolicyAcknowledgement


class ESSRequestTypeViewSet(AuditMixin, ModelViewSet):
    queryset = ESSRequestType.objects.filter(is_active=True).order_by('name')
    serializer_class = ESSRequestTypeSerializer
    filterset_fields = ['category', 'is_active', 'requires_approval']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class ESSRequestViewSet(AuditMixin, ModelViewSet):
    queryset = ESSRequest.objects.select_related(
        'employee__person', 'request_type', 'resolved_by'
    ).order_by('-created_at')
    serializer_class = ESSRequestSerializer
    filterset_fields = ['status', 'request_type', 'employee']
    search_fields = ['subject']

    def get_permissions(self):
        if self.action in ['create', 'my_requests']:
            return [IsInternalUser()]
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        obj = self.get_object()
        if obj.status != ESSRequest.STATUS_DRAFT:
            return Response({'detail': 'Only draft requests can be submitted.'}, status=400)
        obj.status = ESSRequest.STATUS_SUBMITTED
        obj.save(update_fields=['status', 'updated_at'])
        log_action(request, 'SUBMIT', 'ESSRequest', str(obj.id), module='ess')
        return Response(ESSRequestSerializer(obj).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def resolve(self, request, pk=None):
        obj = self.get_object()
        if obj.status not in [ESSRequest.STATUS_SUBMITTED, ESSRequest.STATUS_IN_REVIEW, ESSRequest.STATUS_APPROVED]:
            return Response({'detail': 'Request cannot be resolved in its current state.'}, status=400)
        obj.status = ESSRequest.STATUS_COMPLETED
        obj.resolved_by = request.user
        obj.resolved_at = timezone.now()
        obj.resolution_notes = request.data.get('resolution_notes', '')
        obj.save(update_fields=['status', 'resolved_by', 'resolved_at', 'resolution_notes', 'updated_at'])
        log_action(request, 'RESOLVE', 'ESSRequest', str(obj.id), module='ess')
        return Response(ESSRequestSerializer(obj).data)

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        try:
            employee = request.user.person.employee
        except Exception:
            return Response({'detail': 'No employee profile found for this user.'}, status=404)
        qs = ESSRequest.objects.filter(employee=employee).order_by('-created_at')
        serializer = ESSRequestSerializer(qs, many=True)
        return Response(serializer.data)


class ProfileChangeRequestViewSet(AuditMixin, ModelViewSet):
    queryset = ProfileChangeRequest.objects.select_related(
        'employee__person', 'reviewed_by'
    ).order_by('-created_at')
    serializer_class = ProfileChangeRequestSerializer
    filterset_fields = ['status', 'employee', 'field_name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def approve(self, request, pk=None):
        obj = self.get_object()
        if obj.status != ProfileChangeRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be approved.'}, status=400)
        obj.status = ProfileChangeRequest.STATUS_APPROVED
        obj.reviewed_by = request.user
        obj.review_notes = request.data.get('review_notes', '')
        obj.save(update_fields=['status', 'reviewed_by', 'review_notes', 'updated_at'])
        log_action(request, 'APPROVE', 'ProfileChangeRequest', str(obj.id), module='ess')
        return Response(ProfileChangeRequestSerializer(obj).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def reject(self, request, pk=None):
        obj = self.get_object()
        if obj.status != ProfileChangeRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be rejected.'}, status=400)
        obj.status = ProfileChangeRequest.STATUS_REJECTED
        obj.reviewed_by = request.user
        obj.review_notes = request.data.get('review_notes', '')
        obj.save(update_fields=['status', 'reviewed_by', 'review_notes', 'updated_at'])
        log_action(request, 'REJECT', 'ProfileChangeRequest', str(obj.id), module='ess')
        return Response(ProfileChangeRequestSerializer(obj).data)


class PolicyAcknowledgementViewSet(AuditMixin, ModelViewSet):
    queryset = PolicyAcknowledgement.objects.select_related(
        'employee__person', 'policy'
    ).order_by('-acknowledged_at')
    serializer_class = PolicyAcknowledgementSerializer
    filterset_fields = ['employee', 'policy']
    http_method_names = ['get', 'post', 'head', 'options']

    def get_permissions(self):
        return [IsInternalUser()]

    def perform_create(self, serializer):
        ip = self.request.META.get('REMOTE_ADDR')
        serializer.save(ip_address=ip)


class ManagerDelegationViewSet(AuditMixin, ModelViewSet):
    queryset = ManagerDelegation.objects.select_related(
        'delegator__person', 'delegate__person', 'created_by'
    ).order_by('-valid_from')
    serializer_class = ManagerDelegationSerializer
    filterset_fields = ['delegator', 'delegate', 'is_active', 'delegation_type']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]
