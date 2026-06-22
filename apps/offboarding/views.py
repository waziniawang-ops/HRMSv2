from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsHRStaff, IsHRChecker
from apps.audit.mixins import AuditMixin
from apps.audit.utils import log_action

from .models import (
    OffboardingCase, ClearanceTask, AssetClearance,
    AccessRevocation, ExitInterview, FinalSettlement,
)
from .serializers import (
    OffboardingCaseSerializer, ClearanceTaskSerializer, AssetClearanceSerializer,
    AccessRevocationSerializer, ExitInterviewSerializer, FinalSettlementSerializer,
)

DEFAULT_CLEARANCE_TASKS = [
    {'task_name': 'Revoke network & system access', 'department': 'IT', 'task_type': 'IT_ACCESS'},
    {'task_name': 'Retrieve laptop/devices', 'department': 'IT', 'task_type': 'ASSET_RETURN'},
    {'task_name': 'Retrieve access badge', 'department': 'Admin', 'task_type': 'ASSET_RETURN'},
    {'task_name': 'Finance clearance & expense reconciliation', 'department': 'Finance', 'task_type': 'FINANCE_CLEARANCE'},
    {'task_name': 'Library & resource return', 'department': 'Admin', 'task_type': 'LIBRARY'},
    {'task_name': 'HR documentation & file update', 'department': 'HR', 'task_type': 'ADMIN'},
    {'task_name': 'Medical clearance', 'department': 'Medical', 'task_type': 'MEDICAL'},
]


class OffboardingCaseViewSet(AuditMixin, ModelViewSet):
    queryset = OffboardingCase.objects.select_related(
        'employee__person', 'initiated_by', 'hr_owner'
    ).order_by('-created_at')
    serializer_class = OffboardingCaseSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'employee', 'rehire_eligible', 'legal_hold']
    search_fields = ['employee__employee_number', 'employee__person__legal_name']

    @action(detail=True, methods=['post'])
    def initiate(self, request, pk=None):
        case = self.get_object()
        if case.clearance_tasks.exists():
            return Response({'detail': 'Clearance tasks already created.'}, status=400)
        for task_data in DEFAULT_CLEARANCE_TASKS:
            ClearanceTask.objects.create(case=case, **task_data)
        case.status = OffboardingCase.STATUS_IN_PROGRESS
        case.save(update_fields=['status'])
        log_action(request, 'INITIATE', 'OffboardingCase', str(case.id), module='offboarding')
        return Response(OffboardingCaseSerializer(case, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def complete_case(self, request, pk=None):
        case = self.get_object()
        incomplete = case.clearance_tasks.exclude(status__in=['COMPLETED', 'WAIVED'])
        if incomplete.exists():
            return Response(
                {'detail': f'{incomplete.count()} clearance task(s) still pending.'},
                status=400
            )
        case.status = OffboardingCase.STATUS_COMPLETED
        case.completed_at = timezone.now()
        case.save(update_fields=['status', 'completed_at'])
        log_action(request, 'COMPLETE', 'OffboardingCase', str(case.id), module='offboarding')
        return Response(OffboardingCaseSerializer(case, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def schedule_exit_interview(self, request, pk=None):
        case = self.get_object()
        interview_date = request.data.get('exit_interview_scheduled_date')
        if not interview_date:
            return Response({'detail': 'exit_interview_scheduled_date is required.'}, status=400)
        case.exit_interview_scheduled_date = interview_date
        case.save(update_fields=['exit_interview_scheduled_date'])
        return Response(OffboardingCaseSerializer(case, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def add_legal_hold(self, request, pk=None):
        case = self.get_object()
        case.legal_hold = True
        case.save(update_fields=['legal_hold'])
        log_action(request, 'LEGAL_HOLD', 'OffboardingCase', str(case.id), module='offboarding')
        return Response({'detail': 'Legal hold applied.'})


class ClearanceTaskViewSet(AuditMixin, ModelViewSet):
    queryset = ClearanceTask.objects.select_related('case__employee__person', 'assigned_to').order_by('due_date')
    serializer_class = ClearanceTaskSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['case', 'status', 'task_type', 'assigned_to']

    @action(detail=True, methods=['post'])
    def complete_task(self, request, pk=None):
        task = self.get_object()
        notes = request.data.get('completion_notes', '')
        task.status = ClearanceTask.STATUS_COMPLETED
        task.completion_notes = notes
        task.completed_by = request.user
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completion_notes', 'completed_by', 'completed_at'])
        return Response(ClearanceTaskSerializer(task).data)

    @action(detail=True, methods=['post'])
    def waive_task(self, request, pk=None):
        task = self.get_object()
        task.status = ClearanceTask.STATUS_WAIVED
        task.completion_notes = request.data.get('reason', 'Waived by HR')
        task.save(update_fields=['status', 'completion_notes'])
        return Response(ClearanceTaskSerializer(task).data)


class AssetClearanceViewSet(AuditMixin, ModelViewSet):
    queryset = AssetClearance.objects.select_related('case__employee__person').order_by('created_at')
    serializer_class = AssetClearanceSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['case', 'return_status', 'asset_type']

    @action(detail=True, methods=['post'])
    def mark_returned(self, request, pk=None):
        asset = self.get_object()
        asset.return_status = AssetClearance.RETURN_RETURNED
        asset.return_date = timezone.now().date()
        asset.condition_on_return = request.data.get('condition_on_return', AssetClearance.CONDITION_GOOD)
        asset.condition_notes = request.data.get('condition_notes', '')
        asset.cleared_by = request.user
        asset.save()
        return Response(AssetClearanceSerializer(asset).data)


class AccessRevocationViewSet(AuditMixin, ModelViewSet):
    queryset = AccessRevocation.objects.select_related('case__employee__person').order_by('created_at')
    serializer_class = AccessRevocationSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['case', 'status', 'access_type']

    @action(detail=True, methods=['post'])
    def mark_revoked(self, request, pk=None):
        rev = self.get_object()
        rev.status = AccessRevocation.STATUS_REVOKED
        rev.revoked_by = request.user
        rev.revoked_at = timezone.now()
        rev.save(update_fields=['status', 'revoked_by', 'revoked_at'])
        return Response(AccessRevocationSerializer(rev).data)


class ExitInterviewViewSet(AuditMixin, ModelViewSet):
    queryset = ExitInterview.objects.select_related('case__employee__person', 'conducted_by').order_by('-created_at')
    serializer_class = ExitInterviewSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['case', 'format', 'overall_sentiment']


class FinalSettlementViewSet(AuditMixin, ModelViewSet):
    queryset = FinalSettlement.objects.select_related('case__employee__person', 'approved_by').order_by('-created_at')
    serializer_class = FinalSettlementSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['case', 'status', 'payment_method']

    def perform_create(self, serializer):
        settlement = serializer.save()
        settlement.compute_total()
        settlement.save(update_fields=['total_settlement'])

    def perform_update(self, serializer):
        settlement = serializer.save()
        settlement.compute_total()
        settlement.save(update_fields=['total_settlement'])

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        settlement = self.get_object()
        if settlement.status != FinalSettlement.STATUS_DRAFT:
            return Response({'detail': 'Only draft settlements can be submitted.'}, status=400)
        settlement.status = FinalSettlement.STATUS_SUBMITTED
        settlement.save(update_fields=['status'])
        return Response(FinalSettlementSerializer(settlement).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        settlement = self.get_object()
        if settlement.status != FinalSettlement.STATUS_SUBMITTED:
            return Response({'detail': 'Only submitted settlements can be approved.'}, status=400)
        settlement.status = FinalSettlement.STATUS_APPROVED
        settlement.approved_by = request.user
        settlement.save(update_fields=['status', 'approved_by'])
        log_action(request, 'APPROVE', 'FinalSettlement', str(settlement.id), module='offboarding')
        return Response(FinalSettlementSerializer(settlement).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def mark_paid(self, request, pk=None):
        settlement = self.get_object()
        if settlement.status != FinalSettlement.STATUS_APPROVED:
            return Response({'detail': 'Settlement must be approved before marking as paid.'}, status=400)
        settlement.status = FinalSettlement.STATUS_PAID
        settlement.settlement_date = timezone.now().date()
        settlement.save(update_fields=['status', 'settlement_date'])
        case = settlement.case
        case.settlement_status = OffboardingCase.SETTLEMENT_PAID
        case.settlement_paid_at = timezone.now().date()
        case.final_settlement_amount = settlement.total_settlement
        case.save(update_fields=['settlement_status', 'settlement_paid_at', 'final_settlement_amount'])
        return Response(FinalSettlementSerializer(settlement).data)
