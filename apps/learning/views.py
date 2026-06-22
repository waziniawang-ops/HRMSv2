from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsHRStaff, IsLDOfficer, IsLDChecker, IsInternalUser
from apps.audit.utils import log_action
from apps.workflow.engine import WorkflowEngine
from apps.workflow.models import WorkflowRequest
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import (
    Course, LearningPath, AssignmentRule, LearningAssignment,
    CourseSession, Enrollment, Assessment, CourseCompletion, Certificate,
    TrainingRequest, SkillGap, LearningTranscript,
)
from .serializers import (
    CourseSerializer, LearningPathSerializer, AssignmentRuleSerializer,
    LearningAssignmentSerializer, CourseSessionSerializer, EnrollmentSerializer,
    AssessmentSerializer, CourseCompletionSerializer, CertificateSerializer,
    TrainingRequestSerializer, SkillGapSerializer, LearningTranscriptSerializer,
)


class CourseViewSet(AuditMixin, ModelViewSet):
    queryset = Course.objects.all().order_by('title')
    serializer_class = CourseSerializer
    filterset_fields = ['course_type', 'status', 'is_mandatory']
    search_fields = ['code', 'title']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [(IsLDOfficer | IsLDChecker)()]
        return [IsLDOfficer()]

    @action(detail=True, methods=['post'], permission_classes=[IsLDChecker])
    def publish(self, request, pk=None):
        course = self.get_object()
        if course.status != Course.STATUS_DRAFT:
            return Response({'detail': 'Only draft courses can be published.'}, status=400)
        course.status = Course.STATUS_PUBLISHED
        course.approved_by = request.user
        course.save()
        log_action(request, 'PUBLISH', 'Course', str(course.id), module='learning')
        return Response(CourseSerializer(course).data)

    @action(detail=True, methods=['post'], permission_classes=[IsLDOfficer])
    def archive(self, request, pk=None):
        course = self.get_object()
        course.status = Course.STATUS_ARCHIVED
        course.save()
        return Response(CourseSerializer(course).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('COURSE_PUBLICATION_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'Course', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('COURSE_PUBLICATION_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.status = Course.STATUS_PUBLISHED
            obj.approved_by = request.user
            obj.save(update_fields=['status', 'approved_by'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('COURSE_PUBLICATION_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class LearningPathViewSet(AuditMixin, ModelViewSet):
    queryset = LearningPath.objects.all().order_by('name')
    serializer_class = LearningPathSerializer
    permission_classes = [IsLDOfficer]
    filterset_fields = ['status']


class AssignmentRuleViewSet(AuditMixin, ModelViewSet):
    queryset = AssignmentRule.objects.select_related('course', 'learning_path').filter(is_active=True)
    serializer_class = AssignmentRuleSerializer
    permission_classes = [IsLDOfficer]
    filterset_fields = ['trigger', 'is_active']


class LearningAssignmentViewSet(AuditMixin, ModelViewSet):
    queryset = LearningAssignment.objects.select_related(
        'employee__person', 'course', 'learning_path'
    ).order_by('-created_at')
    serializer_class = LearningAssignmentSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['status', 'employee', 'course']

    @action(detail=False, methods=['get'], permission_classes=[IsInternalUser])
    def my_assignments(self, request):
        from apps.core_hr.models import Employee
        try:
            employee = Employee.objects.get(person__user=request.user)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee record found.'}, status=404)
        assignments = LearningAssignment.objects.filter(employee=employee).order_by('-created_at')
        return Response(LearningAssignmentSerializer(assignments, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsInternalUser])
    def start(self, request, pk=None):
        assignment = self.get_object()
        if assignment.status != LearningAssignment.STATUS_ASSIGNED:
            return Response({'detail': 'Assignment already started or completed.'}, status=400)
        assignment.status = LearningAssignment.STATUS_IN_PROGRESS
        assignment.save()
        return Response(LearningAssignmentSerializer(assignment).data)


class CourseSessionViewSet(AuditMixin, ModelViewSet):
    queryset = CourseSession.objects.select_related('course').order_by('-start_datetime')
    serializer_class = CourseSessionSerializer
    permission_classes = [IsLDOfficer]
    filterset_fields = ['course', 'status']

    @action(detail=True, methods=['post'])
    def complete_session(self, request, pk=None):
        session = self.get_object()
        session.status = CourseSession.STATUS_COMPLETED
        session.save()
        return Response(CourseSessionSerializer(session).data)


class EnrollmentViewSet(AuditMixin, ModelViewSet):
    queryset = Enrollment.objects.select_related('employee__person', 'course_session__course').all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['course_session', 'employee', 'status']

    @action(detail=True, methods=['post'], permission_classes=[IsLDOfficer])
    def mark_attended(self, request, pk=None):
        enrollment = self.get_object()
        enrollment.status = Enrollment.STATUS_ATTENDED
        enrollment.attended_at = timezone.now()
        enrollment.save()
        return Response(EnrollmentSerializer(enrollment).data)


class AssessmentViewSet(AuditMixin, ModelViewSet):
    queryset = Assessment.objects.select_related('employee__person', 'course').order_by('-attempted_at')
    serializer_class = AssessmentSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['course', 'employee', 'is_passed']


class CourseCompletionViewSet(AuditMixin, ModelViewSet):
    queryset = CourseCompletion.objects.select_related(
        'employee__person', 'course'
    ).prefetch_related('certificate').order_by('-completed_at')
    serializer_class = CourseCompletionSerializer
    permission_classes = [IsLDOfficer]
    filterset_fields = ['employee', 'course', 'is_valid']

    def perform_create(self, serializer):
        import uuid as uuid_module
        completion = serializer.save()
        cert_number = f"CERT-{str(completion.id).upper()[:8]}"
        Certificate.objects.create(
            completion=completion,
            certificate_number=cert_number,
            expiry_date=completion.expiry_date,
        )
        assignment = LearningAssignment.objects.filter(
            employee=completion.employee, course=completion.course
        ).first()
        if assignment:
            assignment.status = LearningAssignment.STATUS_COMPLETED
            assignment.save()
        log_action(self.request, 'CREATE', 'CourseCompletion', str(completion.id), module='learning')


class TrainingRequestViewSet(AuditMixin, ModelViewSet):
    queryset = TrainingRequest.objects.select_related('employee__person').order_by('-created_at')
    serializer_class = TrainingRequestSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['status', 'employee']

    @action(detail=True, methods=['post'], permission_classes=[IsLDOfficer])
    def approve(self, request, pk=None):
        req = self.get_object()
        if req.status != TrainingRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be approved.'}, status=400)
        req.status = TrainingRequest.STATUS_APPROVED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.review_notes = request.data.get('notes', '')
        req.save()
        log_action(request, 'APPROVE', 'TrainingRequest', str(req.id), module='learning')
        return Response(TrainingRequestSerializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsLDOfficer])
    def reject(self, request, pk=None):
        req = self.get_object()
        if req.status != TrainingRequest.STATUS_PENDING:
            return Response({'detail': 'Only pending requests can be rejected.'}, status=400)
        req.status = TrainingRequest.STATUS_REJECTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.review_notes = request.data.get('notes', '')
        req.save()
        return Response(TrainingRequestSerializer(req).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('TRAINING_ASSIGNMENT_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'TrainingRequest', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TRAINING_ASSIGNMENT_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            obj.status = TrainingRequest.STATUS_APPROVED
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('TRAINING_ASSIGNMENT_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        obj.status = TrainingRequest.STATUS_REJECTED
        obj.reviewed_by = request.user
        obj.reviewed_at = timezone.now()
        obj.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return Response(WorkflowRequestSerializer(wf_req).data)


class SkillGapViewSet(AuditMixin, ModelViewSet):
    queryset = SkillGap.objects.select_related('employee__person', 'recommended_course').order_by('-gap')
    serializer_class = SkillGapSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employee', 'is_closed']

    @action(detail=True, methods=['post'])
    def close_gap(self, request, pk=None):
        gap = self.get_object()
        gap.is_closed = True
        gap.closed_at = timezone.now()
        gap.save()
        return Response(SkillGapSerializer(gap).data)

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('SKILL_GAP_PLAN_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'SkillGap', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('SKILL_GAP_PLAN_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('SKILL_GAP_PLAN_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class LearningTranscriptViewSet(AuditMixin, ModelViewSet):
    queryset = LearningTranscript.objects.select_related('employee__person').order_by('employee__employee_number')
    serializer_class = LearningTranscriptSerializer
    filterset_fields = ['employee']
    http_method_names = ['get', 'head', 'options']

    def get_permissions(self):
        return [IsInternalUser()]
