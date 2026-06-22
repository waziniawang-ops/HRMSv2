from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from apps.audit.utils import log_action
from apps.accounts.permissions import IsHRStaff, IsHRMaker, IsHRChecker, IsSystemAdmin

from .models import SalaryComponent, GradeBand, EmployeePackage, CompensationChange, BonusCycle, BonusAllocation
from .serializers import (
    SalaryComponentSerializer, GradeBandSerializer, EmployeePackageSerializer,
    CompensationChangeSerializer, BonusCycleSerializer, BonusAllocationSerializer,
)


class SalaryComponentViewSet(AuditMixin, ModelViewSet):
    queryset = SalaryComponent.objects.all().order_by('name')
    serializer_class = SalaryComponentSerializer
    filterset_fields = ['category', 'is_active', 'is_taxable', 'is_pensionable']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsHRStaff()]
        return [IsSystemAdmin()]


class GradeBandViewSet(AuditMixin, ModelViewSet):
    queryset = GradeBand.objects.select_related('grade', 'component').order_by('grade', 'component')
    serializer_class = GradeBandSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['grade', 'component', 'is_active']


class EmployeePackageViewSet(AuditMixin, ModelViewSet):
    queryset = EmployeePackage.objects.select_related(
        'employee__person', 'approved_by', 'created_by'
    ).order_by('-effective_date')
    serializer_class = EmployeePackageSerializer
    permission_classes = [IsHRMaker]
    filterset_fields = ['employee', 'status']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def submit_for_approval(self, request, pk=None):
        pkg = self.get_object()
        if pkg.status != EmployeePackage.STATUS_DRAFT:
            return Response({'detail': 'Only draft packages can be submitted.'}, status=400)
        from apps.workflow.engine import WorkflowEngine
        engine = WorkflowEngine('COMPENSATION_PACKAGE_APPROVAL')
        if not pkg.workflow_request:
            wf_req = engine.create_request(request.user, 'EmployeePackage', pkg.id)
            pkg.workflow_request = wf_req
            pkg.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, pkg.workflow_request)
        from apps.workflow.serializers import WorkflowRequestSerializer
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        pkg = self.get_object()
        if not pkg.workflow_request:
            return Response({'detail': 'No workflow request.'}, status=400)
        from apps.workflow.engine import WorkflowEngine
        from apps.workflow.models import WorkflowRequest
        engine = WorkflowEngine('COMPENSATION_PACKAGE_APPROVAL')
        wf_req = engine.approve(request, pkg.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            EmployeePackage.objects.filter(
                employee=pkg.employee, status=EmployeePackage.STATUS_ACTIVE
            ).update(status=EmployeePackage.STATUS_SUPERSEDED, valid_to=pkg.effective_date)
            pkg.status = EmployeePackage.STATUS_ACTIVE
            pkg.approved_by = request.user
            pkg.approved_at = timezone.now()
            pkg.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        from apps.workflow.serializers import WorkflowRequestSerializer
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        pkg = self.get_object()
        if not pkg.workflow_request:
            return Response({'detail': 'No workflow request.'}, status=400)
        from apps.workflow.engine import WorkflowEngine
        engine = WorkflowEngine('COMPENSATION_PACKAGE_APPROVAL')
        wf_req = engine.reject(request, pkg.workflow_request, request.data.get('comment', ''))
        from apps.workflow.serializers import WorkflowRequestSerializer
        return Response(WorkflowRequestSerializer(wf_req).data)


class CompensationChangeViewSet(AuditMixin, ModelViewSet):
    queryset = CompensationChange.objects.select_related('employee__person', 'created_by').order_by('-created_at')
    serializer_class = CompensationChangeSerializer
    permission_classes = [IsHRMaker]
    filterset_fields = ['employee', 'change_type', 'status']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class BonusCycleViewSet(AuditMixin, ModelViewSet):
    queryset = BonusCycle.objects.select_related('created_by').order_by('-year', 'name')
    serializer_class = BonusCycleSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['year', 'bonus_type', 'status']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def open_cycle(self, request, pk=None):
        cycle = self.get_object()
        if cycle.status != BonusCycle.STATUS_DRAFT:
            return Response({'detail': 'Only draft cycles can be opened.'}, status=400)
        cycle.status = BonusCycle.STATUS_OPEN
        cycle.save(update_fields=['status', 'updated_at'])
        log_action(request, 'OPEN', 'BonusCycle', str(cycle.id), module='compensation')
        return Response(BonusCycleSerializer(cycle).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def close_cycle(self, request, pk=None):
        cycle = self.get_object()
        if cycle.status != BonusCycle.STATUS_OPEN:
            return Response({'detail': 'Only open cycles can be closed.'}, status=400)
        cycle.status = BonusCycle.STATUS_CLOSED
        cycle.approved_by = request.user
        cycle.approved_at = timezone.now()
        cycle.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        return Response(BonusCycleSerializer(cycle).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def mark_paid(self, request, pk=None):
        cycle = self.get_object()
        if cycle.status != BonusCycle.STATUS_CLOSED:
            return Response({'detail': 'Only closed cycles can be marked as paid.'}, status=400)
        cycle.status = BonusCycle.STATUS_PAID
        cycle.save(update_fields=['status', 'updated_at'])
        return Response(BonusCycleSerializer(cycle).data)


class BonusAllocationViewSet(AuditMixin, ModelViewSet):
    queryset = BonusAllocation.objects.select_related(
        'cycle', 'employee__person', 'approved_by'
    ).order_by('-created_at')
    serializer_class = BonusAllocationSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['cycle', 'employee', 'status']

    def perform_create(self, serializer):
        serializer.save(recommended_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        alloc = self.get_object()
        if alloc.status != BonusAllocation.STATUS_PENDING:
            return Response({'detail': 'Only pending allocations can be approved.'}, status=400)
        approved_amount = request.data.get('approved_amount', alloc.recommended_amount)
        alloc.status = BonusAllocation.STATUS_APPROVED
        alloc.approved_amount = approved_amount
        alloc.approved_by = request.user
        alloc.save(update_fields=['status', 'approved_amount', 'approved_by'])
        return Response(BonusAllocationSerializer(alloc).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        alloc = self.get_object()
        if alloc.status != BonusAllocation.STATUS_PENDING:
            return Response({'detail': 'Only pending allocations can be rejected.'}, status=400)
        alloc.status = BonusAllocation.STATUS_REJECTED
        alloc.save(update_fields=['status'])
        return Response(BonusAllocationSerializer(alloc).data)
