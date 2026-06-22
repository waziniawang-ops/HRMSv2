from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from apps.accounts.permissions import IsHRStaff, IsInternalUser
from apps.audit.utils import log_action

from .models import (
    HSEIncidentType, HSEIncident, IncidentInvestigation,
    CorrectiveAction, WellbeingProgram, WellbeingEnrollment, MedicalFitnessRecord,
)
from .serializers import (
    HSEIncidentTypeSerializer, HSEIncidentSerializer, IncidentInvestigationSerializer,
    CorrectiveActionSerializer, WellbeingProgramSerializer,
    WellbeingEnrollmentSerializer, MedicalFitnessRecordSerializer,
)


class HSEIncidentTypeViewSet(AuditMixin, ModelViewSet):
    queryset = HSEIncidentType.objects.all().order_by('name')
    serializer_class = HSEIncidentTypeSerializer
    filterset_fields = ['is_active', 'default_severity']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class HSEIncidentViewSet(AuditMixin, ModelViewSet):
    queryset = HSEIncident.objects.select_related(
        'incident_type', 'reported_by'
    ).order_by('-incident_date')
    serializer_class = HSEIncidentSerializer
    filterset_fields = ['status', 'severity', 'incident_type', 'is_work_related']
    search_fields = ['incident_number', 'title', 'location']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def close_incident(self, request, pk=None):
        incident = self.get_object()
        if incident.status == HSEIncident.STATUS_CLOSED:
            return Response({'detail': 'Incident is already closed.'}, status=400)
        incident.status = HSEIncident.STATUS_CLOSED
        incident.save(update_fields=['status', 'updated_at'])
        log_action(request, 'CLOSE', 'HSEIncident', str(incident.id), module='hse')
        return Response(HSEIncidentSerializer(incident, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def start_investigation(self, request, pk=None):
        incident = self.get_object()
        data = request.data
        investigation = IncidentInvestigation.objects.create(
            incident=incident,
            lead_investigator=request.user,
            team_members=data.get('team_members', []),
            investigation_start=data.get('investigation_start', timezone.localdate()),
            target_close_date=data.get('target_close_date'),
        )
        incident.status = HSEIncident.STATUS_UNDER_INVESTIGATION
        incident.save(update_fields=['status', 'updated_at'])
        log_action(request, 'CREATE', 'IncidentInvestigation', str(investigation.id), module='hse')
        return Response(IncidentInvestigationSerializer(investigation, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class IncidentInvestigationViewSet(AuditMixin, ModelViewSet):
    queryset = IncidentInvestigation.objects.select_related('incident', 'lead_investigator').order_by('-investigation_start')
    serializer_class = IncidentInvestigationSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'incident', 'lead_investigator']

    @action(detail=True, methods=['post'])
    def complete_investigation(self, request, pk=None):
        inv = self.get_object()
        if inv.status == IncidentInvestigation.STATUS_COMPLETED:
            return Response({'detail': 'Investigation already completed.'}, status=400)
        inv.status = IncidentInvestigation.STATUS_COMPLETED
        inv.completed_at = timezone.now()
        inv.root_cause = request.data.get('root_cause', inv.root_cause)
        inv.findings = request.data.get('findings', inv.findings)
        inv.recommendations = request.data.get('recommendations', inv.recommendations)
        inv.save()
        return Response(IncidentInvestigationSerializer(inv, context={'request': request}).data)


class CorrectiveActionViewSet(AuditMixin, ModelViewSet):
    queryset = CorrectiveAction.objects.select_related('investigation', 'incident', 'assigned_to').order_by('due_date')
    serializer_class = CorrectiveActionSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'priority', 'assigned_to', 'action_type']

    @action(detail=True, methods=['post'])
    def complete_action(self, request, pk=None):
        action_obj = self.get_object()
        action_obj.status = CorrectiveAction.STATUS_COMPLETED
        action_obj.completed_at = timezone.now()
        action_obj.completion_evidence = request.data.get('completion_evidence', '')
        action_obj.save()
        return Response(CorrectiveActionSerializer(action_obj, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def verify_action(self, request, pk=None):
        action_obj = self.get_object()
        if action_obj.status != CorrectiveAction.STATUS_COMPLETED:
            return Response({'detail': 'Action must be completed before verification.'}, status=400)
        action_obj.verified_by = request.user
        action_obj.verified_at = timezone.now()
        action_obj.save(update_fields=['verified_by', 'verified_at', 'updated_at'])
        return Response(CorrectiveActionSerializer(action_obj, context={'request': request}).data)


class WellbeingProgramViewSet(AuditMixin, ModelViewSet):
    queryset = WellbeingProgram.objects.select_related('created_by', 'facilitator').order_by('-start_date')
    serializer_class = WellbeingProgramSerializer
    filterset_fields = ['status', 'program_type', 'is_mandatory']
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'enroll']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsInternalUser])
    def enroll(self, request, pk=None):
        program = self.get_object()
        try:
            employee = request.user.person.employee
        except Exception:
            return Response({'detail': 'No employee record linked to your account.'}, status=400)
        if program.status != WellbeingProgram.STATUS_ACTIVE:
            return Response({'detail': 'Program is not currently active.'}, status=400)
        if program.max_participants and program.current_enrollment >= program.max_participants:
            return Response({'detail': 'Program is full.'}, status=400)
        enrollment, created = WellbeingEnrollment.objects.get_or_create(
            program=program, employee=employee,
            defaults={'status': WellbeingEnrollment.STATUS_ACTIVE}
        )
        if not created:
            return Response({'detail': 'Already enrolled in this program.'}, status=400)
        program.current_enrollment += 1
        program.save(update_fields=['current_enrollment'])
        return Response(WellbeingEnrollmentSerializer(enrollment, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def activate_program(self, request, pk=None):
        program = self.get_object()
        program.status = WellbeingProgram.STATUS_ACTIVE
        program.save(update_fields=['status', 'updated_at'])
        return Response(WellbeingProgramSerializer(program, context={'request': request}).data)


class WellbeingEnrollmentViewSet(AuditMixin, ModelViewSet):
    queryset = WellbeingEnrollment.objects.select_related('program', 'employee__person').order_by('-enrolled_at')
    serializer_class = WellbeingEnrollmentSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['program', 'employee', 'status']


class MedicalFitnessRecordViewSet(AuditMixin, ModelViewSet):
    queryset = MedicalFitnessRecord.objects.select_related('employee__person').order_by('-assessment_date')
    serializer_class = MedicalFitnessRecordSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['fitness_status', 'employee']
    search_fields = ['employee__employee_number', 'employee__person__legal_name']
