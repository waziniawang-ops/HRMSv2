from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.audit.mixins import AuditMixin
from apps.accounts.permissions import IsHRStaff, IsInternalUser
from apps.audit.utils import log_action

from .models import ERCaseCategory, ERCase, CaseParty, CaseEvidence, CaseHearing, CaseOutcome, ERAppeal
from .serializers import (
    ERCaseCategorySerializer, ERCaseSerializer, CasePartySerializer,
    CaseEvidenceSerializer, CaseHearingSerializer, CaseOutcomeSerializer, ERAppealSerializer,
)


class ERCaseCategoryViewSet(AuditMixin, ModelViewSet):
    queryset = ERCaseCategory.objects.all().order_by('name')
    serializer_class = ERCaseCategorySerializer
    filterset_fields = ['is_grievance', 'is_disciplinary', 'is_active']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class ERCaseViewSet(AuditMixin, ModelViewSet):
    queryset = ERCase.objects.select_related(
        'category', 'subject_employee__person', 'opened_by', 'assigned_investigator'
    ).prefetch_related('parties').order_by('-created_at')
    serializer_class = ERCaseSerializer
    filterset_fields = ['status', 'case_type', 'severity', 'subject_employee']
    search_fields = ['case_number', 'subject']
    permission_classes = [IsHRStaff]

    @action(detail=True, methods=['post'])
    def assign_investigator(self, request, pk=None):
        case = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id is required.'}, status=400)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            investigator = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        case.assigned_investigator = investigator
        if case.status == ERCase.STATUS_OPEN:
            case.status = ERCase.STATUS_UNDER_INVESTIGATION
        case.save(update_fields=['assigned_investigator', 'status', 'updated_at'])
        log_action(request, 'ASSIGN_INVESTIGATOR', 'ERCase', str(case.id), module='employee_relations')
        return Response(ERCaseSerializer(case).data)

    @action(detail=True, methods=['post'])
    def close_case(self, request, pk=None):
        case = self.get_object()
        if case.status == ERCase.STATUS_CLOSED:
            return Response({'detail': 'Case is already closed.'}, status=400)
        case.status = ERCase.STATUS_CLOSED
        case.closed_at = timezone.now()
        case.save(update_fields=['status', 'closed_at', 'updated_at'])
        log_action(request, 'CLOSE', 'ERCase', str(case.id), module='employee_relations')
        return Response(ERCaseSerializer(case).data)

    @action(detail=True, methods=['post'])
    def add_legal_hold(self, request, pk=None):
        case = self.get_object()
        case.legal_hold = True
        case.save(update_fields=['legal_hold', 'updated_at'])
        log_action(request, 'LEGAL_HOLD', 'ERCase', str(case.id), module='employee_relations')
        return Response(ERCaseSerializer(case).data)

    @action(detail=True, methods=['post'])
    def remove_legal_hold(self, request, pk=None):
        case = self.get_object()
        case.legal_hold = False
        case.save(update_fields=['legal_hold', 'updated_at'])
        log_action(request, 'REMOVE_LEGAL_HOLD', 'ERCase', str(case.id), module='employee_relations')
        return Response(ERCaseSerializer(case).data)


class CasePartyViewSet(AuditMixin, ModelViewSet):
    queryset = CaseParty.objects.select_related(
        'case', 'employee__person'
    ).order_by('added_at')
    serializer_class = CasePartySerializer
    filterset_fields = ['case', 'employee', 'role']
    permission_classes = [IsHRStaff]


class CaseEvidenceViewSet(AuditMixin, ModelViewSet):
    queryset = CaseEvidence.objects.select_related('case', 'added_by').order_by('created_at')
    serializer_class = CaseEvidenceSerializer
    filterset_fields = ['case', 'evidence_type', 'is_confidential']
    search_fields = ['title']
    permission_classes = [IsHRStaff]


class CaseHearingViewSet(AuditMixin, ModelViewSet):
    queryset = CaseHearing.objects.select_related('case').order_by('hearing_date')
    serializer_class = CaseHearingSerializer
    filterset_fields = ['case', 'status', 'hearing_type']
    permission_classes = [IsHRStaff]

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        hearing = self.get_object()
        hearing.status = CaseHearing.STATUS_COMPLETED
        hearing.outcome_summary = request.data.get('outcome_summary', hearing.outcome_summary)
        hearing.save(update_fields=['status', 'outcome_summary', 'updated_at'])
        if hearing.case.status == ERCase.STATUS_HEARING_SCHEDULED:
            hearing.case.status = ERCase.STATUS_HEARING_COMPLETED
            hearing.case.save(update_fields=['status', 'updated_at'])
        return Response(CaseHearingSerializer(hearing).data)


class CaseOutcomeViewSet(AuditMixin, ModelViewSet):
    queryset = CaseOutcome.objects.select_related('case', 'decided_by').order_by('-created_at')
    serializer_class = CaseOutcomeSerializer
    filterset_fields = ['case', 'outcome_type', 'letter_issued']
    permission_classes = [IsHRStaff]

    def perform_create(self, serializer):
        outcome = serializer.save()
        case = outcome.case
        if case.status not in [ERCase.STATUS_CLOSED, ERCase.STATUS_APPEALED]:
            case.status = ERCase.STATUS_OUTCOME_ISSUED
            case.save(update_fields=['status', 'updated_at'])


class ERAppealViewSet(AuditMixin, ModelViewSet):
    queryset = ERAppeal.objects.select_related(
        'case', 'appellant__person', 'reviewed_by'
    ).order_by('-appeal_date')
    serializer_class = ERAppealSerializer
    filterset_fields = ['case', 'appellant', 'status']
    permission_classes = [IsHRStaff]

    @action(detail=True, methods=['post'])
    def uphold(self, request, pk=None):
        appeal = self.get_object()
        appeal.status = ERAppeal.STATUS_UPHELD
        appeal.reviewed_by = request.user
        appeal.review_notes = request.data.get('review_notes', '')
        appeal.save(update_fields=['status', 'reviewed_by', 'review_notes', 'updated_at'])
        appeal.case.status = ERCase.STATUS_APPEALED
        appeal.case.save(update_fields=['status', 'updated_at'])
        log_action(request, 'UPHOLD_APPEAL', 'ERAppeal', str(appeal.id), module='employee_relations')
        return Response(ERAppealSerializer(appeal).data)

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        appeal = self.get_object()
        appeal.status = ERAppeal.STATUS_DISMISSED
        appeal.reviewed_by = request.user
        appeal.review_notes = request.data.get('review_notes', '')
        appeal.save(update_fields=['status', 'reviewed_by', 'review_notes', 'updated_at'])
        log_action(request, 'DISMISS_APPEAL', 'ERAppeal', str(appeal.id), module='employee_relations')
        return Response(ERAppealSerializer(appeal).data)
