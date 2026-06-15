from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from rest_framework.decorators import action

from apps.accounts.permissions import IsHRStaff, IsHRMaker, IsHRChecker, IsInternalUser, IsSystemAdmin
from apps.audit.utils import log_action
from apps.workflow.engine import WorkflowEngine
from apps.workflow.models import WorkflowRequest
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import OrgUnit, CostCenter, JobFamily, Job, Grade, Position, Person, Employee, EmployeeAssignment, SystemSetting
from .serializers import (
    OrgUnitSerializer, CostCenterSerializer, JobFamilySerializer, JobSerializer,
    GradeSerializer, PositionSerializer, PersonSerializer, EmployeeSerializer,
    EmployeeAssignmentSerializer, SystemSettingSerializer,
)


class OrgUnitViewSet(AuditMixin, ModelViewSet):
    queryset = OrgUnit.objects.all().order_by('name')
    serializer_class = OrgUnitSerializer
    filterset_fields = ['type', 'status', 'parent']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('ORG_UNIT_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'OrgUnit', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('ORG_UNIT_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('ORG_UNIT_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class CostCenterViewSet(AuditMixin, ModelViewSet):
    queryset = CostCenter.objects.all().order_by('code')
    serializer_class = CostCenterSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['is_active', 'org_unit']
    search_fields = ['code', 'name']


class JobFamilyViewSet(AuditMixin, ModelViewSet):
    queryset = JobFamily.objects.all().order_by('name')
    serializer_class = JobFamilySerializer
    permission_classes = [IsHRStaff]
    search_fields = ['code', 'name']


class JobViewSet(AuditMixin, ModelViewSet):
    queryset = Job.objects.select_related('job_family').order_by('job_title')
    serializer_class = JobSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['job_family', 'is_active']
    search_fields = ['job_code', 'job_title']

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('JOB_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'Job', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('JOB_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('JOB_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class GradeViewSet(AuditMixin, ModelViewSet):
    queryset = Grade.objects.all().order_by('level')
    serializer_class = GradeSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['is_active']
    search_fields = ['grade_code', 'grade_name']

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('JOB_GRADE_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'Grade', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('JOB_GRADE_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('JOB_GRADE_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class PositionViewSet(AuditMixin, ModelViewSet):
    queryset = Position.objects.select_related(
        'job', 'org_unit', 'grade', 'cost_center', 'incumbent_employee'
    ).order_by('position_code')
    serializer_class = PositionSerializer
    permission_classes = [IsHRMaker]
    filterset_fields = ['status', 'org_unit', 'grade', 'is_critical']
    search_fields = ['position_code', 'title']

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def submit_for_approval(self, request, pk=None):
        position = self.get_object()
        if position.status != Position.STATUS_DRAFT:
            return Response({'detail': 'Only draft positions can be submitted.'}, status=400)
        engine = WorkflowEngine('POSITION_APPROVAL')
        wf_req, created = None, True
        if position.workflow_request:
            wf_req = position.workflow_request
        else:
            wf_req = engine.create_request(request.user, 'Position', position.id)
            position.workflow_request = wf_req
            position.save()
        wf_req = engine.submit(request, wf_req)
        log_action(request, 'SUBMIT', 'Position', str(position.id), module='core_hr')
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        position = self.get_object()
        if not position.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('POSITION_APPROVAL')
        wf_req = engine.approve(request, position.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            position.status = Position.STATUS_APPROVED
            position.save()
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        position = self.get_object()
        if not position.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('POSITION_APPROVAL')
        wf_req = engine.reject(request, position.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class PersonViewSet(AuditMixin, ModelViewSet):
    queryset = Person.objects.all().order_by('legal_name')
    serializer_class = PersonSerializer
    permission_classes = [IsHRStaff]
    search_fields = ['legal_name', 'email', 'phone']


class EmployeeViewSet(AuditMixin, ModelViewSet):
    queryset = Employee.objects.select_related(
        'person', 'manager__person', 'position', 'org_unit', 'grade'
    ).order_by('employee_number')
    serializer_class = EmployeeSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employment_status', 'org_unit', 'grade', 'manager']
    search_fields = ['employee_number', 'person__legal_name', 'person__email']

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        employee = self.get_object()
        assignments = employee.assignments.all()
        return Response(EmployeeAssignmentSerializer(assignments, many=True).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('EMPLOYEE_RECORD_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'Employee', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('EMPLOYEE_RECORD_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('EMPLOYEE_RECORD_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class EmployeeAssignmentViewSet(AuditMixin, ModelViewSet):
    queryset = EmployeeAssignment.objects.all().order_by('-valid_from')
    serializer_class = EmployeeAssignmentSerializer
    permission_classes = [IsHRMaker]
    filterset_fields = ['employee', 'position', 'is_primary']

    def _sync_employee(self, assignment):
        """When a primary assignment is saved, push its fields onto the Employee record."""
        if not assignment.is_primary:
            return
        emp = assignment.employee
        emp.position = assignment.position
        emp.org_unit = assignment.org_unit
        emp.grade = assignment.grade
        emp.manager = assignment.manager
        emp.save(update_fields=['position', 'org_unit', 'grade', 'manager'])

    def perform_create(self, serializer):
        assignment = serializer.save()
        self._sync_employee(assignment)

    def perform_update(self, serializer):
        assignment = serializer.save()
        self._sync_employee(assignment)


# ── Currency list used for the select UI ──────────────────────────────────────
SUPPORTED_CURRENCIES = [
    {'code': 'BND', 'name': 'Brunei Dollar',       'symbol': 'BND$'},
    {'code': 'USD', 'name': 'US Dollar',            'symbol': 'USD$'},
    {'code': 'SGD', 'name': 'Singapore Dollar',     'symbol': 'S$'},
    {'code': 'MYR', 'name': 'Malaysian Ringgit',    'symbol': 'RM'},
    {'code': 'GBP', 'name': 'British Pound',        'symbol': '£'},
    {'code': 'EUR', 'name': 'Euro',                 'symbol': '€'},
    {'code': 'AUD', 'name': 'Australian Dollar',    'symbol': 'A$'},
    {'code': 'JPY', 'name': 'Japanese Yen',         'symbol': '¥'},
    {'code': 'CNY', 'name': 'Chinese Yuan',         'symbol': 'CN¥'},
    {'code': 'HKD', 'name': 'Hong Kong Dollar',     'symbol': 'HK$'},
    {'code': 'SAR', 'name': 'Saudi Riyal',          'symbol': '﷼'},
    {'code': 'AED', 'name': 'UAE Dirham',           'symbol': 'د.إ'},
]


class CurrencySettingView(APIView):
    """
    GET  — returns current currency + full list of supported currencies.
           All authenticated users can read.
    PUT  — updates the active currency. System Admin only.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsInternalUser()]
        return [IsSystemAdmin()]

    def get(self, request):
        setting, _ = SystemSetting.objects.get_or_create(
            key='DEFAULT_CURRENCY',
            defaults={'value': 'BND', 'description': 'System default currency code'},
        )
        active = next(
            (c for c in SUPPORTED_CURRENCIES if c['code'] == setting.value),
            SUPPORTED_CURRENCIES[0],  # fallback to BND
        )
        return Response({
            'code':       active['code'],
            'name':       active['name'],
            'symbol':     active['symbol'],
            'currencies': SUPPORTED_CURRENCIES,
        })

    def put(self, request):
        code = request.data.get('code', '').strip().upper()
        valid_codes = {c['code'] for c in SUPPORTED_CURRENCIES}
        if code not in valid_codes:
            return Response({'detail': f'Invalid currency code: {code}. Supported: {sorted(valid_codes)}'}, status=400)
        setting, _ = SystemSetting.objects.get_or_create(key='DEFAULT_CURRENCY')
        setting.value = code
        setting.description = 'System default currency code'
        setting.updated_by = request.user
        setting.save()
        log_action(request, 'UPDATE', 'SystemSetting', setting.key, module='core_hr',
                   after_json={'currency': code})
        active = next(c for c in SUPPORTED_CURRENCIES if c['code'] == code)
        return Response({
            'code':       active['code'],
            'name':       active['name'],
            'symbol':     active['symbol'],
            'currencies': SUPPORTED_CURRENCIES,
        })


class SystemSettingViewSet(AuditMixin, ModelViewSet):
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsSystemAdmin]
    http_method_names = ['get', 'patch', 'head', 'options']

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
