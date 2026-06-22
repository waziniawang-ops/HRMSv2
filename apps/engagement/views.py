import uuid as _uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsHRStaff, IsInternalUser
from apps.audit.mixins import AuditMixin
from apps.audit.utils import log_action

from .models import (
    SurveyTemplate, EngagementSurvey, SurveyResponse,
    ActionPlan, RecognitionType, RecognitionAward,
    RecognitionNomination, EmployeePoints,
)
from .serializers import (
    SurveyTemplateSerializer, EngagementSurveySerializer, SurveyResponseSerializer,
    ActionPlanSerializer, RecognitionTypeSerializer, RecognitionAwardSerializer,
    RecognitionNominationSerializer, EmployeePointsSerializer,
)


class SurveyTemplateViewSet(AuditMixin, ModelViewSet):
    queryset = SurveyTemplate.objects.select_related('created_by').order_by('name')
    serializer_class = SurveyTemplateSerializer
    filterset_fields = ['survey_type', 'is_active']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class EngagementSurveyViewSet(AuditMixin, ModelViewSet):
    queryset = EngagementSurvey.objects.select_related('template', 'launched_by').order_by('-created_at')
    serializer_class = EngagementSurveySerializer
    filterset_fields = ['status', 'target_audience', 'template']
    search_fields = ['title']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'submit_response']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def launch(self, request, pk=None):
        survey = self.get_object()
        if survey.status != EngagementSurvey.STATUS_DRAFT:
            return Response({'detail': 'Only draft surveys can be launched.'}, status=400)
        survey.status = EngagementSurvey.STATUS_ACTIVE
        survey.save(update_fields=['status'])
        log_action(request, 'LAUNCH', 'EngagementSurvey', str(survey.id), module='engagement')
        return Response(EngagementSurveySerializer(survey, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def close_survey(self, request, pk=None):
        survey = self.get_object()
        if survey.status != EngagementSurvey.STATUS_ACTIVE:
            return Response({'detail': 'Only active surveys can be closed.'}, status=400)
        survey.status = EngagementSurvey.STATUS_CLOSED
        survey.save(update_fields=['status'])
        log_action(request, 'CLOSE', 'EngagementSurvey', str(survey.id), module='engagement')
        return Response(EngagementSurveySerializer(survey, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsInternalUser])
    def submit_response(self, request, pk=None):
        survey = self.get_object()
        if survey.status != EngagementSurvey.STATUS_ACTIVE:
            return Response({'detail': 'Survey is not currently active.'}, status=400)
        employee = None
        if not survey.is_anonymous:
            try:
                employee = request.user.person.employee
            except Exception:
                return Response({'detail': 'No employee record found for current user.'}, status=400)
        token = str(_uuid.uuid4()).replace('-', '')
        response_obj, created = SurveyResponse.objects.get_or_create(
            survey=survey,
            employee=employee,
            defaults={'response_token': token}
        )
        if not created and response_obj.is_complete:
            return Response({'detail': 'You have already submitted a response to this survey.'}, status=400)
        response_obj.responses = request.data.get('responses', {})
        response_obj.enps_score = request.data.get('enps_score')
        response_obj.is_complete = True
        response_obj.submitted_at = timezone.now()
        response_obj.save()
        survey.response_count = survey.responses.filter(is_complete=True).count()
        survey.save(update_fields=['response_count'])
        return Response(SurveyResponseSerializer(response_obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        survey = self.get_object()
        if survey.status == EngagementSurvey.STATUS_ACTIVE and not request.user.is_hr_staff:
            return Response({'detail': 'Results available only after survey is closed.'}, status=403)
        responses = survey.responses.filter(is_complete=True)
        total = responses.count()
        if total < survey.anonymity_threshold and survey.is_anonymous:
            return Response({'detail': f'Minimum {survey.anonymity_threshold} responses required to view results.'}, status=403)
        enps_scores = list(responses.exclude(enps_score__isnull=True).values_list('enps_score', flat=True))
        return Response({
            'survey_id': str(survey.id),
            'title': survey.title,
            'total_responses': total,
            'completion_rate': round((total / max(survey.response_count, 1)) * 100, 1),
            'enps_scores': enps_scores,
            'average_enps': round(sum(enps_scores) / len(enps_scores), 1) if enps_scores else None,
        })


class SurveyResponseViewSet(AuditMixin, ModelViewSet):
    queryset = SurveyResponse.objects.select_related('survey', 'employee__person').order_by('-submitted_at')
    serializer_class = SurveyResponseSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['survey', 'is_complete']
    http_method_names = ['get', 'head', 'options']


class ActionPlanViewSet(AuditMixin, ModelViewSet):
    queryset = ActionPlan.objects.select_related('survey', 'assigned_to', 'created_by').order_by('target_date')
    serializer_class = ActionPlanSerializer
    filterset_fields = ['survey', 'status', 'assigned_to']
    search_fields = ['title', 'focus_area']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class RecognitionTypeViewSet(AuditMixin, ModelViewSet):
    queryset = RecognitionType.objects.all().order_by('name')
    serializer_class = RecognitionTypeSerializer
    filterset_fields = ['recognition_category', 'is_active']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class RecognitionAwardViewSet(AuditMixin, ModelViewSet):
    queryset = RecognitionAward.objects.select_related(
        'nominated_by__person', 'recipient__person', 'recognition_type'
    ).order_by('-created_at')
    serializer_class = RecognitionAwardSerializer
    filterset_fields = ['recipient', 'nominated_by', 'recognition_type', 'status', 'is_public']
    search_fields = ['message']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_received', 'create']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=False, methods=['get'], permission_classes=[IsInternalUser])
    def my_received(self, request):
        try:
            employee = request.user.person.employee
        except Exception:
            return Response([])
        awards = RecognitionAward.objects.filter(
            recipient=employee, status=RecognitionAward.STATUS_APPROVED
        ).select_related('nominated_by__person', 'recognition_type').order_by('-created_at')
        return Response(RecognitionAwardSerializer(awards, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def approve(self, request, pk=None):
        award = self.get_object()
        award.status = RecognitionAward.STATUS_APPROVED
        award.reviewed_by = request.user
        award.reviewed_at = timezone.now()
        award.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        if award.points_awarded > 0:
            points_obj, _ = EmployeePoints.objects.get_or_create(employee=award.recipient)
            points_obj.total_earned += award.points_awarded
            points_obj.save(update_fields=['total_earned', 'updated_at'])
        return Response(RecognitionAwardSerializer(award).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def reject(self, request, pk=None):
        award = self.get_object()
        award.status = RecognitionAward.STATUS_REJECTED
        award.reviewed_by = request.user
        award.reviewed_at = timezone.now()
        award.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return Response(RecognitionAwardSerializer(award).data)


class RecognitionNominationViewSet(AuditMixin, ModelViewSet):
    queryset = RecognitionNomination.objects.select_related(
        'nominator__person', 'nominee__person', 'recognition_type'
    ).order_by('-created_at')
    serializer_class = RecognitionNominationSerializer
    filterset_fields = ['status', 'recognition_type', 'nominee']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def approve(self, request, pk=None):
        nomination = self.get_object()
        if nomination.status not in [RecognitionNomination.STATUS_SUBMITTED, RecognitionNomination.STATUS_UNDER_REVIEW]:
            return Response({'detail': 'Cannot approve in current status.'}, status=400)
        nomination.status = RecognitionNomination.STATUS_APPROVED
        nomination.save(update_fields=['status'])
        award = RecognitionAward.objects.create(
            nominated_by=nomination.nominator,
            recipient=nomination.nominee,
            recognition_type=nomination.recognition_type,
            message=nomination.justification,
            points_awarded=nomination.recognition_type.points_value,
            status=RecognitionAward.STATUS_APPROVED,
        )
        if award.points_awarded > 0:
            points_obj, _ = EmployeePoints.objects.get_or_create(employee=award.recipient)
            points_obj.total_earned += award.points_awarded
            points_obj.save(update_fields=['total_earned', 'updated_at'])
        return Response(RecognitionNominationSerializer(nomination).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def reject(self, request, pk=None):
        nomination = self.get_object()
        nomination.status = RecognitionNomination.STATUS_REJECTED
        nomination.save(update_fields=['status'])
        return Response(RecognitionNominationSerializer(nomination).data)


class EmployeePointsViewSet(ModelViewSet):
    queryset = EmployeePoints.objects.select_related('employee__person').order_by('-total_earned')
    serializer_class = EmployeePointsSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['employee']
    http_method_names = ['get', 'head', 'options']

    @action(detail=False, methods=['get'])
    def my_points(self, request):
        try:
            employee = request.user.person.employee
            points_obj, _ = EmployeePoints.objects.get_or_create(employee=employee)
            return Response(EmployeePointsSerializer(points_obj).data)
        except Exception:
            return Response({'total_earned': 0, 'total_redeemed': 0, 'available_points': 0})
