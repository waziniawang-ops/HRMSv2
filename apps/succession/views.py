from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsHRStaff, IsHRChecker, IsTalentCommittee, IsManagerOrAbove
from apps.audit.utils import log_action
from apps.workflow.engine import WorkflowEngine
from apps.workflow.models import WorkflowRequest
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import (
    SuccessionPlan, SuccessorNomination, TalentPool, TalentProfile,
    DevelopmentPlan, DevelopmentActivity, CriticalRole,
)
from .serializers import (
    SuccessionPlanSerializer, SuccessorNominationSerializer,
    TalentPoolSerializer, TalentProfileSerializer,
    DevelopmentPlanSerializer, DevelopmentActivitySerializer,
    CriticalRoleSerializer,
)


class SuccessionPlanViewSet(AuditMixin, ModelViewSet):
    queryset = SuccessionPlan.objects.select_related(
        'position', 'incumbent__person', 'prepared_by'
    ).prefetch_related('nominees').order_by('-plan_year')
    serializer_class = SuccessionPlanSerializer
    permission_classes = [IsHRStaff | IsTalentCommittee]
    filterset_fields = ['status', 'risk_level', 'plan_year', 'position']

    @action(detail=True, methods=['post'], permission_classes=[IsTalentCommittee])
    def approve(self, request, pk=None):
        plan = self.get_object()
        if plan.status not in [SuccessionPlan.STATUS_DRAFT, SuccessionPlan.STATUS_UNDER_REVIEW]:
            return Response({'detail': 'Plan cannot be approved in current state.'}, status=400)
        plan.status = SuccessionPlan.STATUS_APPROVED
        plan.approved_by = request.user
        plan.approved_at = timezone.now()
        plan.save()
        log_action(request, 'APPROVE', 'SuccessionPlan', str(plan.id), module='succession')
        return Response(SuccessionPlanSerializer(plan).data)

    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        plan = self.get_object()
        if plan.status != SuccessionPlan.STATUS_DRAFT:
            return Response({'detail': 'Only draft plans can be submitted for review.'}, status=400)
        plan.status = SuccessionPlan.STATUS_UNDER_REVIEW
        plan.save()
        return Response(SuccessionPlanSerializer(plan).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('SUCCESSION_PLAN_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'SuccessionPlan', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('SUCCESSION_PLAN_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.status = SuccessionPlan.STATUS_APPROVED
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
            obj.save(update_fields=['status', 'approved_by', 'approved_at'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('SUCCESSION_PLAN_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class SuccessorNominationViewSet(AuditMixin, ModelViewSet):
    queryset = SuccessorNomination.objects.select_related(
        'succession_plan__position', 'candidate__person'
    ).order_by('priority_rank')
    serializer_class = SuccessorNominationSerializer
    permission_classes = [IsManagerOrAbove | IsTalentCommittee]
    filterset_fields = ['succession_plan', 'candidate', 'readiness_level']


class TalentPoolViewSet(AuditMixin, ModelViewSet):
    queryset = TalentPool.objects.all().order_by('tier', 'name')
    serializer_class = TalentPoolSerializer
    permission_classes = [IsHRStaff | IsTalentCommittee]
    filterset_fields = ['tier', 'is_active']

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('TALENT_POOL_NOMINATION')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'TalentPool', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TALENT_POOL_NOMINATION')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TALENT_POOL_NOMINATION')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class TalentProfileViewSet(AuditMixin, ModelViewSet):
    queryset = TalentProfile.objects.select_related(
        'employee__person', 'talent_pool', 'assessed_by'
    ).all()
    serializer_class = TalentProfileSerializer
    permission_classes = [IsManagerOrAbove | IsTalentCommittee]
    filterset_fields = ['flight_risk', 'talent_pool', 'nine_box_score', 'mobility_preference']

    def perform_create(self, serializer):
        serializer.save(assessed_by=self.request.user, last_assessed_at=timezone.now())

    def perform_update(self, serializer):
        serializer.save(assessed_by=self.request.user, last_assessed_at=timezone.now())

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('TALENT_PROFILE_REVIEW')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'TalentProfile', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TALENT_PROFILE_REVIEW')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TALENT_PROFILE_REVIEW')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=False, methods=['get'])
    def nine_box_grid(self, request):
        profiles = TalentProfile.objects.select_related(
            'employee__person'
        ).filter(nine_box_score__isnull=False).order_by('nine_box_score')
        grid = {}
        for p in profiles:
            score = str(p.nine_box_score)
            if score not in grid:
                grid[score] = []
            grid[score].append({
                'id': str(p.employee.id),
                'name': p.employee.person.legal_name,
                'score': p.nine_box_score,
                'label': p.get_nine_box_score_display(),
                'flight_risk': p.flight_risk,
            })
        return Response(grid)

    @action(detail=False, methods=['get'])
    def flight_risk_report(self, request):
        high_risk = TalentProfile.objects.select_related(
            'employee__person', 'employee__position'
        ).filter(flight_risk='HIGH').values(
            'employee__id', 'employee__person__legal_name',
            'employee__position__title', 'nine_box_score',
        )
        return Response(list(high_risk))


class DevelopmentPlanViewSet(AuditMixin, ModelViewSet):
    queryset = DevelopmentPlan.objects.select_related(
        'employee__person', 'created_by'
    ).prefetch_related('activities').order_by('-created_at')
    serializer_class = DevelopmentPlanSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'employee']


class DevelopmentActivityViewSet(AuditMixin, ModelViewSet):
    queryset = DevelopmentActivity.objects.select_related('development_plan').order_by('target_date')
    serializer_class = DevelopmentActivitySerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['development_plan', 'activity_type', 'status']

    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        activity = self.get_object()
        activity.status = DevelopmentActivity.STATUS_COMPLETED
        activity.completed_at = timezone.now().date()
        activity.outcome_notes = request.data.get('outcome_notes', '')
        activity.save()
        return Response(DevelopmentActivitySerializer(activity).data)


class CriticalRoleViewSet(AuditMixin, ModelViewSet):
    queryset = CriticalRole.objects.select_related('position').order_by('position__title')
    serializer_class = CriticalRoleSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['risk_level', 'has_identified_successor', 'is_active']
    search_fields = ['position__title', 'rationale']
