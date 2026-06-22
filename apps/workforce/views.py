from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsHRMaker, IsHRChecker, IsHRStaff, IsInternalUser
from apps.audit.utils import log_action
from apps.workflow.engine import WorkflowEngine
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import (
    WorkforcePlan, AttendancePolicy, AttendanceLog, LeaveType, LeaveBalance,
    LeaveRequest, OvertimeRequest, Roster, Transfer, Separation,
    ShiftTemplate, AttendanceException, HolidayCalendar, HolidayCalendarEntry,
    LeavePolicy, LeaveDocument,
)
from .serializers import (
    WorkforcePlanSerializer, AttendancePolicySerializer, AttendanceLogSerializer,
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveRequestSerializer,
    OvertimeRequestSerializer, RosterSerializer, TransferSerializer, SeparationSerializer,
    ShiftTemplateSerializer, AttendanceExceptionSerializer, HolidayCalendarSerializer,
    HolidayCalendarEntrySerializer, LeavePolicySerializer, LeaveDocumentSerializer,
)


class WorkforcePlanViewSet(AuditMixin, ModelViewSet):
    queryset = WorkforcePlan.objects.select_related('org_unit', 'prepared_by').order_by('-plan_year')
    serializer_class = WorkforcePlanSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['plan_year', 'org_unit', 'status']

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        plan = self.get_object()
        if plan.status != WorkforcePlan.STATUS_SUBMITTED:
            return Response({'detail': 'Plan must be submitted before approval.'}, status=400)
        plan.status = WorkforcePlan.STATUS_APPROVED
        plan.approved_by = request.user
        plan.approved_at = timezone.now()
        plan.save()
        log_action(request, 'APPROVE', 'WorkforcePlan', str(plan.id), module='workforce')
        return Response(WorkforcePlanSerializer(plan).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def submit(self, request, pk=None):
        plan = self.get_object()
        if plan.status != WorkforcePlan.STATUS_DRAFT:
            return Response({'detail': 'Only draft plans can be submitted.'}, status=400)
        plan.status = WorkforcePlan.STATUS_SUBMITTED
        plan.save()
        return Response(WorkforcePlanSerializer(plan).data)


class AttendancePolicyViewSet(AuditMixin, ModelViewSet):
    queryset = AttendancePolicy.objects.all().order_by('name')
    serializer_class = AttendancePolicySerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['policy_type', 'is_active']


class AttendanceLogViewSet(AuditMixin, ModelViewSet):
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['employee', 'date', 'is_present', 'source']

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceLog.objects.select_related('employee__person').order_by('-date')
        if not user.is_hr_staff:
            from apps.core_hr.models import Employee
            try:
                emp = Employee.objects.get(person__user=user)
                qs = qs.filter(employee=emp)
            except Employee.DoesNotExist:
                return qs.none()
        return qs

    def perform_create(self, serializer):
        log = serializer.save()
        log.compute_hours()
        log.save()

    @action(detail=False, methods=['get'])
    def my_attendance(self, request):
        from apps.core_hr.models import Employee
        try:
            employee = Employee.objects.get(person__user=request.user)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee record found.'}, status=404)
        logs = AttendanceLog.objects.filter(employee=employee).order_by('-date')[:30]
        return Response(AttendanceLogSerializer(logs, many=True).data)


class LeaveTypeViewSet(AuditMixin, ModelViewSet):
    queryset = LeaveType.objects.all().order_by('name')
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['is_paid', 'is_active']

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('LEAVE_TYPE_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'LeaveType', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('LEAVE_TYPE_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('LEAVE_TYPE_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class LeaveBalanceViewSet(AuditMixin, ModelViewSet):
    queryset = LeaveBalance.objects.select_related('employee__person', 'leave_type').all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employee', 'leave_type', 'year']

    @action(detail=False, methods=['get'])
    def my_balances(self, request):
        from apps.core_hr.models import Employee
        current_year = timezone.now().year
        try:
            employee = Employee.objects.get(person__user=request.user)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee record found.'}, status=404)
        balances = LeaveBalance.objects.filter(employee=employee, year=current_year)
        return Response(LeaveBalanceSerializer(balances, many=True).data)


class LeaveRequestViewSet(AuditMixin, ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['status', 'employee', 'leave_type']

    def get_queryset(self):
        user = self.request.user
        qs = LeaveRequest.objects.select_related('employee__person', 'leave_type', 'reviewed_by').order_by('-created_at')
        if not user.is_hr_staff:
            from apps.core_hr.models import Employee
            try:
                emp = Employee.objects.get(person__user=user)
                qs = qs.filter(employee=emp)
            except Employee.DoesNotExist:
                return qs.none()
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != LeaveRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be approved.'}, status=400)
        leave.status = LeaveRequest.STATUS_APPROVED
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.review_notes = request.data.get('notes', '')
        leave.save()
        log_action(request, 'APPROVE', 'LeaveRequest', str(leave.id), module='workforce')
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def reject(self, request, pk=None):
        leave = self.get_object()
        if leave.status not in [LeaveRequest.STATUS_PENDING, LeaveRequest.STATUS_DRAFT]:
            return Response({'detail': 'Cannot reject this request.'}, status=400)
        leave.status = LeaveRequest.STATUS_REJECTED
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.review_notes = request.data.get('notes', '')
        leave.save()
        log_action(request, 'REJECT', 'LeaveRequest', str(leave.id), module='workforce')
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        leave = self.get_object()
        if leave.status != LeaveRequest.STATUS_DRAFT:
            return Response({'detail': 'Only draft requests can be submitted.'}, status=400)
        leave.status = LeaveRequest.STATUS_PENDING
        leave.save()
        return Response(LeaveRequestSerializer(leave).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('LEAVE_REQUEST_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'LeaveRequest', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        obj.status = LeaveRequest.STATUS_PENDING
        obj.save(update_fields=['status'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('LEAVE_REQUEST_APPROVAL')
        from apps.workflow.models import WorkflowRequest
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.status = LeaveRequest.STATUS_APPROVED
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('LEAVE_REQUEST_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        obj.status = LeaveRequest.STATUS_REJECTED
        obj.reviewed_by = request.user
        obj.reviewed_at = timezone.now()
        obj.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return Response(WorkflowRequestSerializer(wf_req).data)


class OvertimeRequestViewSet(AuditMixin, ModelViewSet):
    serializer_class = OvertimeRequestSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['status', 'employee', 'date']

    def get_queryset(self):
        user = self.request.user
        qs = OvertimeRequest.objects.select_related('employee__person').order_by('-date')
        if not user.is_hr_staff:
            from apps.core_hr.models import Employee
            try:
                emp = Employee.objects.get(person__user=user)
                qs = qs.filter(employee=emp)
            except Employee.DoesNotExist:
                return qs.none()
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def approve(self, request, pk=None):
        ot = self.get_object()
        if ot.status != OvertimeRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be approved.'}, status=400)
        hours_approved = request.data.get('hours_approved', ot.hours_requested)
        ot.status = OvertimeRequest.STATUS_APPROVED
        ot.hours_approved = hours_approved
        ot.approved_by = request.user
        ot.approved_at = timezone.now()
        ot.save()
        log_action(request, 'APPROVE', 'OvertimeRequest', str(ot.id), module='workforce')
        return Response(OvertimeRequestSerializer(ot).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('OVERTIME_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'OvertimeRequest', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('OVERTIME_APPROVAL')
        from apps.workflow.models import WorkflowRequest
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.status = OvertimeRequest.STATUS_APPROVED
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
            obj.hours_approved = obj.hours_requested
            obj.save(update_fields=['status', 'approved_by', 'approved_at', 'hours_approved'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('OVERTIME_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        obj.status = OvertimeRequest.STATUS_REJECTED
        obj.save(update_fields=['status'])
        return Response(WorkflowRequestSerializer(wf_req).data)


class RosterViewSet(AuditMixin, ModelViewSet):
    queryset = Roster.objects.select_related('employee__person').order_by('-effective_date')
    serializer_class = RosterSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employee']


class TransferViewSet(AuditMixin, ModelViewSet):
    queryset = Transfer.objects.select_related(
        'employee__person', 'from_position', 'to_position'
    ).order_by('-created_at')
    serializer_class = TransferSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'movement_type', 'employee']

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status != Transfer.STATUS_PENDING:
            return Response({'detail': 'Only pending transfers can be approved.'}, status=400)
        transfer.status = Transfer.STATUS_APPROVED
        transfer.approved_by = request.user
        transfer.approved_at = timezone.now()
        transfer.save()
        log_action(request, 'APPROVE', 'Transfer', str(transfer.id), module='workforce')
        return Response(TransferSerializer(transfer).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('TRANSFER_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'Transfer', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TRANSFER_APPROVAL')
        from apps.workflow.models import WorkflowRequest
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.status = Transfer.STATUS_APPROVED
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
            obj.save(update_fields=['status', 'approved_by', 'approved_at'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TRANSFER_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        obj.status = Transfer.STATUS_REJECTED
        obj.save(update_fields=['status'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def complete(self, request, pk=None):
        from apps.core_hr.models import Employee
        transfer = self.get_object()
        if transfer.status != Transfer.STATUS_APPROVED:
            return Response({'detail': 'Transfer must be approved before completion.'}, status=400)
        employee = transfer.employee
        employee.position = transfer.to_position
        employee.org_unit = transfer.to_position.org_unit
        if transfer.to_grade:
            employee.grade = transfer.to_grade
        employee.save()
        transfer.to_position.status = 'OCCUPIED'
        transfer.to_position.incumbent_employee = employee
        transfer.to_position.save()
        transfer.from_position.status = 'VACANT'
        transfer.from_position.incumbent_employee = None
        transfer.from_position.save()
        transfer.status = Transfer.STATUS_COMPLETED
        transfer.save()
        log_action(request, 'COMPLETE', 'Transfer', str(transfer.id), module='workforce')
        return Response(TransferSerializer(transfer).data)


class SeparationViewSet(AuditMixin, ModelViewSet):
    queryset = Separation.objects.select_related('employee__person').order_by('-notice_date')
    serializer_class = SeparationSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'separation_type']

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        sep = self.get_object()
        if sep.status != Separation.STATUS_INITIATED:
            return Response({'detail': 'Only initiated separations can be approved.'}, status=400)
        sep.status = Separation.STATUS_APPROVED
        sep.approved_by = request.user
        sep.approved_at = timezone.now()
        sep.save()
        log_action(request, 'APPROVE', 'Separation', str(sep.id), module='workforce')
        return Response(SeparationSerializer(sep).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def complete(self, request, pk=None):
        sep = self.get_object()
        if sep.status != Separation.STATUS_APPROVED:
            return Response({'detail': 'Separation must be approved before completion.'}, status=400)
        employee = sep.employee
        status_map = {
            Separation.TYPE_RESIGNATION: 'RESIGNED',
            Separation.TYPE_TERMINATION: 'TERMINATED',
            Separation.TYPE_RETIREMENT: 'RETIRED',
            Separation.TYPE_END_OF_CONTRACT: 'TERMINATED',
            Separation.TYPE_REDUNDANCY: 'TERMINATED',
            Separation.TYPE_DEATH: 'TERMINATED',
        }
        employee.employment_status = status_map.get(sep.separation_type, 'TERMINATED')
        employee.termination_date = sep.last_working_date
        employee.save()
        if employee.position:
            employee.position.status = 'VACANT'
            employee.position.incumbent_employee = None
            employee.position.save()
        sep.status = Separation.STATUS_COMPLETED
        sep.save()
        log_action(request, 'COMPLETE', 'Separation', str(sep.id), module='workforce')
        return Response(SeparationSerializer(sep).data)


class ShiftTemplateViewSet(AuditMixin, ModelViewSet):
    queryset = ShiftTemplate.objects.select_related('policy').order_by('name')
    serializer_class = ShiftTemplateSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['is_active', 'policy']
    search_fields = ['name']


class AttendanceExceptionViewSet(AuditMixin, ModelViewSet):
    queryset = AttendanceException.objects.select_related('log__employee__person', 'resolved_by').order_by('-detected_at')
    serializer_class = AttendanceExceptionSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['exception_type', 'is_resolved', 'log__employee']

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        exc = self.get_object()
        from django.utils import timezone
        exc.is_resolved = True
        exc.resolution_notes = request.data.get('resolution_notes', '')
        exc.resolved_by = request.user
        exc.resolved_at = timezone.now()
        exc.save()
        log_action(request, 'UPDATE', 'AttendanceException', str(exc.id), module='workforce')
        return Response(AttendanceExceptionSerializer(exc).data)


class HolidayCalendarViewSet(AuditMixin, ModelViewSet):
    queryset = HolidayCalendar.objects.all().order_by('-year', 'country')
    serializer_class = HolidayCalendarSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['year', 'country', 'is_active']


class HolidayCalendarEntryViewSet(AuditMixin, ModelViewSet):
    queryset = HolidayCalendarEntry.objects.select_related('calendar').order_by('date')
    serializer_class = HolidayCalendarEntrySerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['calendar', 'holiday_type', 'is_paid']


class LeavePolicyViewSet(AuditMixin, ModelViewSet):
    queryset = LeavePolicy.objects.select_related('leave_type', 'grade').order_by('leave_type', 'grade')
    serializer_class = LeavePolicySerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['leave_type', 'grade', 'employment_type', 'is_active']


class LeaveDocumentViewSet(AuditMixin, ModelViewSet):
    queryset = LeaveDocument.objects.select_related('leave_request').order_by('-uploaded_at')
    serializer_class = LeaveDocumentSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['leave_request', 'document_type']
    http_method_names = ['get', 'post', 'head', 'options']
