from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from apps.accounts.permissions import IsHRStaff, IsHRChecker, IsFinanceChecker, IsInternalUser
from apps.audit.utils import log_action

from .models import ClaimType, ExpensePolicy, ClaimRequest, ClaimLine, ClaimReceipt, TravelRequest
from .serializers import (
    ClaimTypeSerializer, ExpensePolicySerializer, ClaimRequestSerializer,
    ClaimLineSerializer, ClaimReceiptSerializer, TravelRequestSerializer,
)


class ClaimTypeViewSet(AuditMixin, ModelViewSet):
    queryset = ClaimType.objects.all().order_by('name')
    serializer_class = ClaimTypeSerializer
    filterset_fields = ['category', 'is_active', 'requires_receipt', 'requires_approval']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class ExpensePolicyViewSet(AuditMixin, ModelViewSet):
    queryset = ExpensePolicy.objects.select_related('created_by').order_by('-effective_date')
    serializer_class = ExpensePolicySerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['is_active']
    search_fields = ['name']


class ClaimRequestViewSet(AuditMixin, ModelViewSet):
    queryset = ClaimRequest.objects.select_related(
        'employee__person', 'approved_by'
    ).order_by('-created_at')
    serializer_class = ClaimRequestSerializer
    filterset_fields = ['status', 'employee', 'currency']
    search_fields = ['claim_number', 'claim_title', 'employee__employee_number']

    def get_permissions(self):
        if self.action in ['create', 'my_claims', 'list', 'retrieve']:
            return [IsInternalUser()]
        if self.action in ['approve']:
            return [IsHRChecker()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsInternalUser])
    def submit(self, request, pk=None):
        claim = self.get_object()
        if claim.status != ClaimRequest.STATUS_DRAFT:
            return Response({'detail': 'Only draft claims can be submitted.'}, status=400)
        claim.status = ClaimRequest.STATUS_SUBMITTED
        claim.submitted_at = timezone.now()
        claim.save(update_fields=['status', 'submitted_at', 'updated_at'])
        log_action(request, 'SUBMIT', 'ClaimRequest', str(claim.id), module='claims')
        return Response(ClaimRequestSerializer(claim, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        claim = self.get_object()
        if claim.status not in [ClaimRequest.STATUS_SUBMITTED, ClaimRequest.STATUS_IN_REVIEW]:
            return Response({'detail': 'Claim must be submitted or in review to approve.'}, status=400)
        claim.status = ClaimRequest.STATUS_APPROVED
        claim.approved_by = request.user
        claim.approved_at = timezone.now()
        claim.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        log_action(request, 'APPROVE', 'ClaimRequest', str(claim.id), module='claims')
        return Response(ClaimRequestSerializer(claim, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        claim = self.get_object()
        if claim.status not in [ClaimRequest.STATUS_SUBMITTED, ClaimRequest.STATUS_IN_REVIEW]:
            return Response({'detail': 'Claim must be submitted or in review to reject.'}, status=400)
        claim.status = ClaimRequest.STATUS_REJECTED
        claim.save(update_fields=['status', 'updated_at'])
        log_action(request, 'REJECT', 'ClaimRequest', str(claim.id), module='claims')
        return Response(ClaimRequestSerializer(claim, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def mark_paid(self, request, pk=None):
        claim = self.get_object()
        if claim.status != ClaimRequest.STATUS_APPROVED:
            return Response({'detail': 'Only approved claims can be marked as paid.'}, status=400)
        claim.status = ClaimRequest.STATUS_PAID
        claim.paid_at = timezone.now()
        claim.paid_by = request.user
        claim.save(update_fields=['status', 'paid_at', 'paid_by', 'updated_at'])
        log_action(request, 'MARK_PAID', 'ClaimRequest', str(claim.id), module='claims')
        return Response(ClaimRequestSerializer(claim, context={'request': request}).data)

    @action(detail=False, methods=['get'], permission_classes=[IsInternalUser])
    def my_claims(self, request):
        try:
            employee = request.user.person.employee
        except Exception:
            return Response({'detail': 'No employee record linked to your account.'}, status=400)
        qs = ClaimRequest.objects.filter(employee=employee).order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ClaimRequestSerializer(page, many=True, context={'request': request}).data)
        return Response(ClaimRequestSerializer(qs, many=True, context={'request': request}).data)


class ClaimLineViewSet(AuditMixin, ModelViewSet):
    queryset = ClaimLine.objects.select_related('claim', 'claim_type').order_by('expense_date')
    serializer_class = ClaimLineSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['claim', 'claim_type', 'is_approved']


class ClaimReceiptViewSet(AuditMixin, ModelViewSet):
    queryset = ClaimReceipt.objects.select_related('claim').order_by('-uploaded_at')
    serializer_class = ClaimReceiptSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['claim', 'line']


class TravelRequestViewSet(AuditMixin, ModelViewSet):
    queryset = TravelRequest.objects.select_related(
        'employee__person', 'approved_by'
    ).order_by('-departure_date')
    serializer_class = TravelRequestSerializer
    filterset_fields = ['status', 'employee', 'travel_type']
    search_fields = ['request_number', 'title', 'destination']

    def get_permissions(self):
        if self.action in ['create', 'my_travel_requests', 'list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsInternalUser])
    def submit(self, request, pk=None):
        travel = self.get_object()
        if travel.status != TravelRequest.STATUS_DRAFT:
            return Response({'detail': 'Only draft travel requests can be submitted.'}, status=400)
        travel.status = TravelRequest.STATUS_SUBMITTED
        travel.save(update_fields=['status', 'updated_at'])
        log_action(request, 'SUBMIT', 'TravelRequest', str(travel.id), module='claims')
        return Response(TravelRequestSerializer(travel, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def approve(self, request, pk=None):
        travel = self.get_object()
        if travel.status != TravelRequest.STATUS_SUBMITTED:
            return Response({'detail': 'Travel request must be submitted to approve.'}, status=400)
        travel.status = TravelRequest.STATUS_APPROVED
        travel.approved_by = request.user
        travel.approved_at = timezone.now()
        travel.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        log_action(request, 'APPROVE', 'TravelRequest', str(travel.id), module='claims')
        return Response(TravelRequestSerializer(travel, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def reject(self, request, pk=None):
        travel = self.get_object()
        if travel.status != TravelRequest.STATUS_SUBMITTED:
            return Response({'detail': 'Travel request must be submitted to reject.'}, status=400)
        travel.status = TravelRequest.STATUS_REJECTED
        travel.save(update_fields=['status', 'updated_at'])
        return Response(TravelRequestSerializer(travel, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def complete(self, request, pk=None):
        travel = self.get_object()
        if travel.status != TravelRequest.STATUS_APPROVED:
            return Response({'detail': 'Only approved travel requests can be completed.'}, status=400)
        travel.status = TravelRequest.STATUS_COMPLETED
        travel.save(update_fields=['status', 'updated_at'])
        return Response(TravelRequestSerializer(travel, context={'request': request}).data)

    @action(detail=False, methods=['get'], permission_classes=[IsInternalUser])
    def my_travel_requests(self, request):
        try:
            employee = request.user.person.employee
        except Exception:
            return Response({'detail': 'No employee record linked to your account.'}, status=400)
        qs = TravelRequest.objects.filter(employee=employee).order_by('-departure_date')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(TravelRequestSerializer(page, many=True, context={'request': request}).data)
        return Response(TravelRequestSerializer(qs, many=True, context={'request': request}).data)
