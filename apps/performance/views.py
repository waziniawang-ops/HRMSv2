from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsHRStaff, IsHRChecker, IsHRPerformance, IsInternalUser
from apps.audit.utils import log_action
from apps.workflow.engine import WorkflowEngine
from apps.workflow.models import WorkflowRequest
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import (
    PerformanceCycle, CompetencyModel, Competency, GoalPlan, Goal, GoalProgress,
    ReviewForm, ReviewRating, CalibrationSession, CalibratedRating,
    FinalOutcome, ImprovementPlan,
)
from .serializers import (
    PerformanceCycleSerializer, CompetencyModelSerializer, CompetencySerializer,
    GoalPlanSerializer, GoalSerializer, GoalProgressSerializer,
    ReviewFormSerializer, ReviewRatingSerializer,
    CalibrationSessionSerializer, CalibratedRatingSerializer,
    FinalOutcomeSerializer, ImprovementPlanSerializer,
)


class PerformanceCycleViewSet(AuditMixin, ModelViewSet):
    queryset = PerformanceCycle.objects.all().order_by('-cycle_year')
    serializer_class = PerformanceCycleSerializer
    permission_classes = [IsHRPerformance]
    filterset_fields = ['status', 'cycle_year']

    @action(detail=True, methods=['post'])
    def advance_status(self, request, pk=None):
        cycle = self.get_object()
        transitions = {
            PerformanceCycle.STATUS_DRAFT: PerformanceCycle.STATUS_ACTIVE,
            PerformanceCycle.STATUS_ACTIVE: PerformanceCycle.STATUS_GOAL_SETTING,
            PerformanceCycle.STATUS_GOAL_SETTING: PerformanceCycle.STATUS_MID_YEAR,
            PerformanceCycle.STATUS_MID_YEAR: PerformanceCycle.STATUS_YEAR_END,
            PerformanceCycle.STATUS_YEAR_END: PerformanceCycle.STATUS_CALIBRATION,
            PerformanceCycle.STATUS_CALIBRATION: PerformanceCycle.STATUS_COMPLETED,
            PerformanceCycle.STATUS_COMPLETED: PerformanceCycle.STATUS_CLOSED,
        }
        next_status = transitions.get(cycle.status)
        if not next_status:
            return Response({'detail': 'Cycle is already in final state.'}, status=400)
        cycle.status = next_status
        cycle.save()
        log_action(request, 'UPDATE', 'PerformanceCycle', str(cycle.id), module='performance',
                   after_json={'status': next_status})
        return Response(PerformanceCycleSerializer(cycle).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('PERFORMANCE_CYCLE_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'PerformanceCycle', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('PERFORMANCE_CYCLE_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('PERFORMANCE_CYCLE_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class CompetencyModelViewSet(AuditMixin, ModelViewSet):
    queryset = CompetencyModel.objects.prefetch_related('competencies').filter(is_active=True)
    serializer_class = CompetencyModelSerializer
    permission_classes = [IsHRPerformance]
    filterset_fields = ['is_active']


class CompetencyViewSet(AuditMixin, ModelViewSet):
    queryset = Competency.objects.select_related('model').all()
    serializer_class = CompetencySerializer
    permission_classes = [IsHRPerformance]
    filterset_fields = ['model']


class GoalPlanViewSet(AuditMixin, ModelViewSet):
    serializer_class = GoalPlanSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['status', 'employee', 'cycle']

    def get_queryset(self):
        user = self.request.user
        qs = GoalPlan.objects.select_related('employee__person', 'cycle', 'approved_by').prefetch_related('goals').order_by('-created_at')
        if user.is_hr_staff or user.has_role('HR_PERFORMANCE', 'MANAGER', 'HIRING_MANAGER'):
            return qs
        from apps.core_hr.models import Employee
        try:
            emp = Employee.objects.get(person__user=user)
            return qs.filter(employee=emp)
        except Employee.DoesNotExist:
            return qs.none()

    @action(detail=False, methods=['get'])
    def my_plans(self, request):
        from apps.core_hr.models import Employee
        try:
            employee = Employee.objects.get(person__user=request.user)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee record found.'}, status=404)
        plans = GoalPlan.objects.filter(employee=employee).order_by('-created_at')
        return Response(GoalPlanSerializer(plans, many=True).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        plan = self.get_object()
        if plan.status != GoalPlan.STATUS_DRAFT:
            return Response({'detail': 'Only draft plans can be submitted.'}, status=400)
        plan.status = GoalPlan.STATUS_SUBMITTED
        plan.save()
        return Response(GoalPlanSerializer(plan).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRPerformance])
    def approve(self, request, pk=None):
        plan = self.get_object()
        if plan.status not in [GoalPlan.STATUS_SUBMITTED, GoalPlan.STATUS_MANAGER_APPROVED]:
            return Response({'detail': 'Plan not ready for approval.'}, status=400)
        plan.status = GoalPlan.STATUS_HR_APPROVED
        plan.approved_by = request.user
        plan.approved_at = timezone.now()
        plan.save()
        log_action(request, 'APPROVE', 'GoalPlan', str(plan.id), module='performance')
        return Response(GoalPlanSerializer(plan).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('GOAL_PLAN_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'GoalPlan', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('GOAL_PLAN_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.status = GoalPlan.STATUS_HR_APPROVED
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
            obj.save(update_fields=['status', 'approved_by', 'approved_at'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('GOAL_PLAN_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class GoalViewSet(AuditMixin, ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['goal_plan', 'category', 'status']

    def get_queryset(self):
        user = self.request.user
        qs = Goal.objects.select_related('goal_plan__employee__person').order_by('-weight', 'title')
        if user.is_hr_staff or user.has_role('HR_PERFORMANCE', 'MANAGER', 'HIRING_MANAGER'):
            return qs
        from apps.core_hr.models import Employee
        try:
            emp = Employee.objects.get(person__user=user)
            return qs.filter(goal_plan__employee=emp)
        except Employee.DoesNotExist:
            return qs.none()


class GoalProgressViewSet(AuditMixin, ModelViewSet):
    queryset = GoalProgress.objects.select_related('goal', 'recorded_by').order_by('-update_date')
    serializer_class = GoalProgressSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['goal']


class ReviewFormViewSet(AuditMixin, ModelViewSet):
    serializer_class = ReviewFormSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['cycle', 'employee', 'review_type', 'status']

    def get_queryset(self):
        user = self.request.user
        qs = ReviewForm.objects.select_related('cycle', 'employee__person', 'reviewer').prefetch_related('ratings').order_by('-created_at')
        if user.is_hr_staff or user.has_role('HR_PERFORMANCE', 'MANAGER', 'HIRING_MANAGER'):
            return qs
        from apps.core_hr.models import Employee
        try:
            emp = Employee.objects.get(person__user=user)
            return qs.filter(employee=emp)
        except Employee.DoesNotExist:
            return qs.none()

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        from apps.core_hr.models import Employee
        try:
            employee = Employee.objects.get(person__user=request.user)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee record found.'}, status=404)
        reviews = ReviewForm.objects.filter(employee=employee).order_by('-created_at')
        return Response(ReviewFormSerializer(reviews, many=True).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        form = self.get_object()
        if form.status != ReviewForm.STATUS_IN_PROGRESS:
            return Response({'detail': 'Only in-progress forms can be submitted.'}, status=400)
        form.status = ReviewForm.STATUS_SUBMITTED
        form.submitted_at = timezone.now()
        form.save()
        log_action(request, 'SUBMIT', 'ReviewForm', str(form.id), module='performance')
        return Response(ReviewFormSerializer(form).data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        form = self.get_object()
        if form.status != ReviewForm.STATUS_SUBMITTED:
            return Response({'detail': 'Only submitted forms can be acknowledged.'}, status=400)
        form.status = ReviewForm.STATUS_ACKNOWLEDGED
        form.acknowledged_at = timezone.now()
        form.save()
        return Response(ReviewFormSerializer(form).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('PERFORMANCE_REVIEW_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'ReviewForm', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('PERFORMANCE_REVIEW_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('PERFORMANCE_REVIEW_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class ReviewRatingViewSet(AuditMixin, ModelViewSet):
    queryset = ReviewRating.objects.select_related('review_form', 'competency', 'goal').all()
    serializer_class = ReviewRatingSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['review_form', 'competency', 'goal']


class CalibrationSessionViewSet(AuditMixin, ModelViewSet):
    queryset = CalibrationSession.objects.select_related(
        'cycle', 'org_unit', 'facilitator'
    ).prefetch_related('calibrated_ratings').order_by('-session_date')
    serializer_class = CalibrationSessionSerializer
    permission_classes = [IsHRPerformance]
    filterset_fields = ['cycle', 'org_unit', 'status']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        session = self.get_object()
        session.status = CalibrationSession.STATUS_COMPLETED
        session.save()
        log_action(request, 'COMPLETE', 'CalibrationSession', str(session.id), module='performance')
        return Response(CalibrationSessionSerializer(session).data)


class CalibratedRatingViewSet(AuditMixin, ModelViewSet):
    queryset = CalibratedRating.objects.select_related('session', 'employee__person').all()
    serializer_class = CalibratedRatingSerializer
    permission_classes = [IsHRPerformance]
    filterset_fields = ['session', 'employee']


class FinalOutcomeViewSet(AuditMixin, ModelViewSet):
    queryset = FinalOutcome.objects.select_related(
        'cycle', 'employee__person', 'approved_by'
    ).order_by('-created_at')
    serializer_class = FinalOutcomeSerializer
    permission_classes = [IsHRPerformance]
    filterset_fields = ['cycle', 'employee', 'outcome_label']

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        outcome = self.get_object()
        outcome.approved_by = request.user
        outcome.save()
        log_action(request, 'APPROVE', 'FinalOutcome', str(outcome.id), module='performance')
        return Response(FinalOutcomeSerializer(outcome).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('PERFORMANCE_OUTCOME_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'FinalOutcome', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('PERFORMANCE_OUTCOME_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.approved_by = request.user
            obj.save(update_fields=['approved_by'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('PERFORMANCE_OUTCOME_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class ImprovementPlanViewSet(AuditMixin, ModelViewSet):
    queryset = ImprovementPlan.objects.select_related(
        'employee__person', 'cycle', 'initiated_by'
    ).order_by('-created_at')
    serializer_class = ImprovementPlanSerializer
    permission_classes = [IsHRPerformance]
    filterset_fields = ['status', 'employee', 'cycle']
