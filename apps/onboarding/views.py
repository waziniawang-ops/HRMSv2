from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsHRMaker, IsHRChecker, IsHRStaff, IsInternalUser
from apps.audit.utils import log_action
from apps.workflow.engine import WorkflowEngine
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import OnboardingTemplate, OnboardingCase, OnboardingTask, OnboardingDocument
from .serializers import (
    OnboardingTemplateSerializer, OnboardingCaseSerializer,
    OnboardingTaskSerializer, OnboardingDocumentSerializer,
)


class OnboardingTemplateViewSet(AuditMixin, ModelViewSet):
    queryset = OnboardingTemplate.objects.all().order_by('name')
    serializer_class = OnboardingTemplateSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']


class OnboardingCaseViewSet(AuditMixin, ModelViewSet):
    queryset = OnboardingCase.objects.select_related(
        'offer__application__applicant', 'offer__position', 'template', 'assigned_hr'
    ).order_by('-created_at')
    serializer_class = OnboardingCaseSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'assigned_hr']
    search_fields = ['offer__application__applicant__full_name']

    def perform_create(self, serializer):
        case = serializer.save()
        self._create_tasks_from_template(case)
        log_action(self.request, 'CREATE', 'OnboardingCase', str(case.id), module='onboarding')

    def _create_tasks_from_template(self, case):
        if not case.template:
            default_tasks = [
                {'task_code': 'PERSONAL_INFO', 'title': 'Personal Information Verification', 'is_required': True, 'order': 1},
                {'task_code': 'RESUME', 'title': 'Resume Verification', 'is_required': True, 'order': 2},
                {'task_code': 'ACADEMIC_CERTS', 'title': 'Academic Certificates', 'is_required': True, 'order': 3},
                {'task_code': 'BANK_DETAILS', 'title': 'Bank Account Details', 'is_required': True, 'order': 4},
                {'task_code': 'EMERGENCY_CONTACT', 'title': 'Emergency Contact', 'is_required': True, 'order': 5},
                {'task_code': 'CONTRACT_SIGNING', 'title': 'Employment Contract Signing', 'is_required': True, 'order': 6},
                {'task_code': 'ACCESS_REQUEST', 'title': 'Access Provisioning Request', 'is_required': False, 'order': 7},
                {'task_code': 'PAYROLL_SETUP', 'title': 'Payroll Setup', 'is_required': True, 'order': 8},
            ]
        else:
            default_tasks = case.template.tasks

        for task_data in default_tasks:
            OnboardingTask.objects.create(
                onboarding_case=case,
                task_code=task_data.get('task_code', 'CUSTOM'),
                title=task_data['title'],
                description=task_data.get('description', ''),
                is_required=task_data.get('is_required', True),
                order=task_data.get('order', 0),
            )

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    @transaction.atomic
    def complete_and_convert(self, request, pk=None):
        case = self.get_object()
        if case.status != OnboardingCase.STATUS_PENDING_HR:
            return Response({'detail': 'Case must be in PENDING_HR status to complete.'}, status=400)

        required_incomplete = case.tasks.filter(
            is_required=True
        ).exclude(status=OnboardingTask.STATUS_COMPLETED)
        if required_incomplete.exists():
            titles = list(required_incomplete.values_list('title', flat=True))
            return Response({'detail': f'Required tasks not completed: {titles}'}, status=400)

        case.status = OnboardingCase.STATUS_COMPLETED
        case.hr_verified_at = timezone.now()
        case.hr_verified_by = request.user
        case.completed_at = timezone.now()
        case.save()

        employee = self._create_employee(case, request)
        log_action(request, 'CREATE', 'Employee', str(employee.id), module='onboarding',
                   after_json={'source': 'onboarding', 'case_id': str(case.id)})

        return Response({
            'detail': 'Onboarding completed. Employee created.',
            'employee_id': str(employee.id),
            'employee_number': employee.employee_number,
        })

    def _create_employee(self, case, request):
        from apps.core_hr.models import Person, Employee
        offer = case.offer
        applicant = offer.application.applicant

        # Get or create Person
        if case.candidate_person:
            person = case.candidate_person
        else:
            person, _ = Person.objects.get_or_create(
                email=applicant.email,
                defaults={
                    'legal_name': applicant.full_name,
                    'phone': applicant.phone,
                }
            )
            case.candidate_person = person
            case.save()

        # Generate employee number
        from django.utils import timezone as tz
        last_emp = Employee.objects.order_by('-created_at').first()
        next_num = 1
        if last_emp and last_emp.employee_number.startswith('EMP-'):
            try:
                next_num = int(last_emp.employee_number.split('-')[-1]) + 1
            except ValueError:
                pass
        employee_number = f"EMP-{next_num:06d}"

        employee = Employee.objects.create(
            person=person,
            employee_number=employee_number,
            hire_date=offer.start_date or tz.localdate(),
            employment_status=Employee.STATUS_PROBATION,
            position=offer.position,
            org_unit=offer.position.org_unit,
            grade=offer.grade,
            source_onboarding=case,
        )

        offer.position.status = 'OCCUPIED'
        offer.position.incumbent_employee = employee
        offer.position.save()

        return employee

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def submit_for_hr_review(self, request, pk=None):
        case = self.get_object()
        case.status = OnboardingCase.STATUS_PENDING_HR
        case.save()
        return Response(OnboardingCaseSerializer(case).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('ONBOARDING_CASE_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'OnboardingCase', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('ONBOARDING_CASE_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('ONBOARDING_CASE_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class OnboardingTaskViewSet(AuditMixin, ModelViewSet):
    queryset = OnboardingTask.objects.all().order_by('order')
    serializer_class = OnboardingTaskSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['status', 'onboarding_case', 'is_required']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.status == OnboardingTask.STATUS_COMPLETED:
            return Response({'detail': 'Task already completed.'}, status=400)
        task.status = OnboardingTask.STATUS_COMPLETED
        task.completed_by = request.user
        task.completed_at = timezone.now()
        task.notes = request.data.get('notes', task.notes)
        task.save()

        case = task.onboarding_case
        case.status = OnboardingCase.STATUS_IN_PROGRESS
        case.save()

        return Response(OnboardingTaskSerializer(task).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def verify(self, request, pk=None):
        task = self.get_object()
        task.hr_verified = True
        task.save()
        return Response(OnboardingTaskSerializer(task).data)


class OnboardingDocumentViewSet(AuditMixin, ModelViewSet):
    queryset = OnboardingDocument.objects.all().order_by('-uploaded_at')
    serializer_class = OnboardingDocumentSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['document_type', 'is_verified', 'onboarding_case']

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def verify(self, request, pk=None):
        doc = self.get_object()
        doc.is_verified = True
        doc.verified_by = request.user
        doc.verified_at = timezone.now()
        doc.save()
        return Response(OnboardingDocumentSerializer(doc, context={'request': request}).data)
