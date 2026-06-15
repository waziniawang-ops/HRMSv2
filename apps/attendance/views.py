from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsHRStaff
from apps.workflow.engine import WorkflowEngine
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import FaceDescriptor, AttendanceRecord
from .serializers import FaceDescriptorSerializer, AttendanceRecordSerializer


class FaceDescriptorViewSet(AuditMixin, ModelViewSet):
    queryset = FaceDescriptor.objects.select_related('employee__person', 'enrolled_by').order_by('employee__employee_number')
    serializer_class = FaceDescriptorSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employee']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']


class AttendanceRecordViewSet(AuditMixin, ModelViewSet):
    queryset = AttendanceRecord.objects.select_related('employee__person').order_by('-date', '-check_in')
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employee', 'date', 'method']
    search_fields = ['employee__person__legal_name', 'employee__employee_number']

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('ATTENDANCE_CORRECTION_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'AttendanceRecord', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('ATTENDANCE_CORRECTION_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('ATTENDANCE_CORRECTION_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class FaceVerifyView(APIView):
    """
    Kiosk endpoint — no authentication required.
    Accepts a 128-float face descriptor, finds the closest enrolled employee,
    and records check-in or check-out for today.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        descriptor = request.data.get('descriptor')
        if not isinstance(descriptor, list) or len(descriptor) != 128:
            return Response({'error': 'Invalid descriptor — expected list of 128 floats.'}, status=status.HTTP_400_BAD_REQUEST)

        face_match, distance = FaceDescriptor.find_best_match(descriptor)
        if face_match is None:
            return Response({'match': False, 'message': 'Face not recognised.'}, status=status.HTTP_200_OK)

        employee = face_match.employee
        today = timezone.localdate()
        now = timezone.now()

        record, created = AttendanceRecord.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'check_in': now, 'method': AttendanceRecord.METHOD_FACE},
        )

        if created:
            action = 'CHECK_IN'
        elif record.check_out is None:
            record.check_out = now
            record.save(update_fields=['check_out', 'updated_at'])
            action = 'CHECK_OUT'
        else:
            action = 'ALREADY_COMPLETE'

        check_in_str = record.check_in.strftime('%I:%M %p') if record.check_in else None
        check_out_str = record.check_out.strftime('%I:%M %p') if record.check_out else None

        return Response({
            'match': True,
            'distance': round(distance, 4),
            'employee_id': str(employee.id),
            'employee_name': employee.full_name,
            'employee_number': employee.employee_number,
            'action': action,
            'check_in': check_in_str,
            'check_out': check_out_str,
        })
