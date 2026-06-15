import datetime
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import (
    IsHRMaker, IsHRChecker, IsRecruiter, IsInternalUser, IsApplicant, IsInterviewer,
    IsFinanceChecker,
)
from apps.audit.utils import log_action
from apps.workflow.engine import WorkflowEngine
from apps.workflow.models import WorkflowRequest
from apps.workflow.serializers import WorkflowRequestSerializer
from .models import (
    JobRequisition, JobPosting, Applicant, ApplicantProfile,
    Application, Interview, InterviewFeedback, Offer, ApplicantDocument,
)
from .serializers import (
    JobRequisitionSerializer, JobPostingSerializer, JobPostingPublicSerializer,
    ApplicantSerializer, ApplicantProfileSerializer, ApplicationSerializer,
    InterviewSerializer, InterviewFeedbackSerializer, OfferSerializer,
    ApplicantDocumentSerializer,
)


# ── Automation helpers ────────────────────────────────────────────────────────

def _advance_posting(application, new_status):
    """Push the parent job posting to a new status if it hasn't passed it already."""
    STATUS_ORDER = [
        JobPosting.STATUS_DRAFT, JobPosting.STATUS_POSTED,
        JobPosting.STATUS_SCREENING, JobPosting.STATUS_INTERVIEW,
        JobPosting.STATUS_OFFER_DRAFT, JobPosting.STATUS_OFFER_SUBMITTED,
        JobPosting.STATUS_OFFER_APPROVED, JobPosting.STATUS_OFFER_ACCEPTED,
        JobPosting.STATUS_ONBOARDING_STARTED, JobPosting.STATUS_CLOSED,
    ]
    posting = application.job_posting
    try:
        current_idx = STATUS_ORDER.index(posting.status)
        target_idx = STATUS_ORDER.index(new_status)
    except ValueError:
        return
    if target_idx > current_idx:
        posting.status = new_status
        posting.save(update_fields=['status'])


def _check_all_interviews_complete(application):
    """
    If all non-cancelled interviews for this application are completed,
    advance the application to INTERVIEW_COMPLETED and the posting to INTERVIEW.
    """
    remaining = application.interviews.exclude(
        status__in=[Interview.STATUS_COMPLETED, Interview.STATUS_CANCELLED, Interview.STATUS_NO_SHOW]
    )
    if not remaining.exists():
        application.stage = Application.STATUS_INTERVIEW_COMPLETED
        application.save(update_fields=['stage'])
        _advance_posting(application, JobPosting.STATUS_INTERVIEW)


def _create_onboarding_case(offer):
    """Auto-create an OnboardingCase with default tasks when an offer is accepted."""
    from apps.onboarding.models import OnboardingCase, OnboardingTask, OnboardingTemplate

    target_date = offer.start_date or (timezone.localdate() + datetime.timedelta(days=30))

    case = OnboardingCase.objects.create(
        offer=offer,
        status=OnboardingCase.STATUS_STARTED,
        target_start_date=target_date,
    )

    # Use active template if one exists, otherwise fall back to default task set
    template = OnboardingTemplate.objects.filter(is_active=True).first()
    if template and template.tasks:
        for task_def in template.tasks:
            OnboardingTask.objects.create(
                onboarding_case=case,
                task_code=task_def.get('task_code', OnboardingTask.TASK_CUSTOM),
                title=task_def.get('title', 'Task'),
                description=task_def.get('description', ''),
                is_required=task_def.get('required', True),
                order=task_def.get('order', 0),
            )
    else:
        defaults = [
            (OnboardingTask.TASK_PERSONAL_INFO,    'Personal Information Verification', True,  1),
            (OnboardingTask.TASK_RESUME,            'Resume Verification',               True,  2),
            (OnboardingTask.TASK_ACADEMIC_CERTS,    'Academic Certificates',             True,  3),
            (OnboardingTask.TASK_BANK_DETAILS,      'Bank Account Details',              True,  4),
            (OnboardingTask.TASK_EMERGENCY_CONTACT, 'Emergency Contact',                 True,  5),
            (OnboardingTask.TASK_CONTRACT_SIGNING,  'Employment Contract Signing',       True,  6),
            (OnboardingTask.TASK_ACCESS_REQUEST,    'Access Provisioning Request',       False, 7),
            (OnboardingTask.TASK_PAYROLL_SETUP,     'Payroll Setup',                     False, 8),
        ]
        for code, title, required, order in defaults:
            OnboardingTask.objects.create(
                onboarding_case=case,
                task_code=code,
                title=title,
                is_required=required,
                order=order,
            )

    return case


# ── ViewSets ──────────────────────────────────────────────────────────────────

class JobRequisitionViewSet(AuditMixin, ModelViewSet):
    queryset = JobRequisition.objects.select_related(
        'position', 'requested_by'
    ).order_by('-created_at')
    serializer_class = JobRequisitionSerializer
    permission_classes = [IsHRMaker]
    filterset_fields = ['status', 'hiring_reason', 'position__org_unit']
    search_fields = ['requisition_number', 'justification']

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def submit(self, request, pk=None):
        req = self.get_object()
        if req.status != JobRequisition.STATUS_DRAFT:
            return Response({'detail': 'Only draft requisitions can be submitted.'}, status=400)
        if req.position.status not in ['APPROVED', 'VACANT']:
            return Response({'detail': 'Position must be approved or vacant before creating a requisition.'}, status=400)
        engine = WorkflowEngine('RECRUITMENT_REQUISITION_APPROVAL')
        if not req.workflow_request:
            wf_req = engine.create_request(request.user, 'JobRequisition', req.id)
            req.workflow_request = wf_req
            req.save()
        wf_req = engine.submit(request, req.workflow_request)
        req.status = JobRequisition.STATUS_SUBMITTED
        req.save()
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        req = self.get_object()
        if not req.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('RECRUITMENT_REQUISITION_APPROVAL')
        wf_req = engine.approve(request, req.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            req.status = JobRequisition.STATUS_APPROVED
            req.save()
            # AUTO: create a draft job posting so the recruiter only needs to fill details
            position = req.position
            JobPosting.objects.create(
                requisition=req,
                title=position.title,
                description=(
                    f"Position: {position.title}\n"
                    f"Department: {getattr(position.org_unit, 'name', '')}\n\n"
                    f"Justification: {req.justification}\n\n"
                    "Please update this description with full job details before publishing."
                ),
                requirements='',
                responsibilities='',
                visibility=JobPosting.VISIBILITY_BOTH,
                status=JobPosting.STATUS_DRAFT,
                closing_date=req.target_start_date,
                created_by=request.user,
            )
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        req = self.get_object()
        if not req.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('RECRUITMENT_REQUISITION_APPROVAL')
        wf_req = engine.reject(request, req.workflow_request, request.data.get('comment', ''))
        req.status = JobRequisition.STATUS_REJECTED
        req.save()
        return Response(WorkflowRequestSerializer(wf_req).data)


class JobPostingViewSet(AuditMixin, ModelViewSet):
    serializer_class = JobPostingSerializer
    permission_classes = [IsRecruiter]
    filterset_fields = ['status', 'visibility', 'requisition']
    search_fields = ['title', 'description']

    def get_queryset(self):
        return JobPosting.objects.select_related('requisition', 'created_by').order_by('-created_at')

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def submit_for_approval(self, request, pk=None):
        posting = self.get_object()
        if posting.status != JobPosting.STATUS_DRAFT:
            return Response({'detail': 'Only draft postings can be submitted.'}, status=400)
        if posting.requisition.status != JobRequisition.STATUS_APPROVED:
            return Response({'detail': 'Requisition must be approved before posting.'}, status=400)
        engine = WorkflowEngine('JOB_POSTING_APPROVAL')
        if not posting.workflow_request:
            wf_req = engine.create_request(request.user, 'JobPosting', posting.id)
            posting.workflow_request = wf_req
            posting.save()
        wf_req = engine.submit(request, posting.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve_and_publish(self, request, pk=None):
        posting = self.get_object()
        if not posting.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('JOB_POSTING_APPROVAL')
        wf_req = engine.approve(request, posting.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            posting.status = JobPosting.STATUS_POSTED
            if not posting.opening_date:
                posting.opening_date = timezone.localdate()
            posting.save()
            log_action(request, 'PUBLISH', 'JobPosting', str(posting.id), module='recruitment')
        return Response(JobPostingSerializer(posting, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        posting = self.get_object()
        if not posting.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('JOB_POSTING_APPROVAL')
        wf_req = engine.reject(request, posting.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class PublicJobListView(generics.ListAPIView):
    """Public endpoint — no auth required."""
    serializer_class = JobPostingPublicSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ['title', 'description']
    filterset_fields = ['visibility']

    def get_queryset(self):
        return JobPosting.objects.filter(
            status=JobPosting.STATUS_POSTED,
            visibility__in=[JobPosting.VISIBILITY_EXTERNAL, JobPosting.VISIBILITY_BOTH],
        ).order_by('-created_at')


class PublicJobDetailView(generics.RetrieveAPIView):
    serializer_class = JobPostingPublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return JobPosting.objects.filter(status=JobPosting.STATUS_POSTED)


class ApplicantViewSet(AuditMixin, ModelViewSet):
    queryset = Applicant.objects.select_related('user').order_by('-created_at')
    serializer_class = ApplicantSerializer
    filterset_fields = ['profile_status']
    search_fields = ['full_name', 'email']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsRecruiter()]
        if self.action == 'me':
            return [IsApplicant()]
        return [IsApplicant()]

    def get_object(self):
        if self.request.user.role == 'APPLICANT':
            return self.request.user.applicant
        return super().get_object()

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsApplicant])
    def me(self, request):
        applicant = request.user.applicant
        if request.method == 'PATCH':
            serializer = self.get_serializer(applicant, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(self.get_serializer(applicant).data)


class ApplicantProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ApplicantProfileSerializer
    permission_classes = [IsApplicant]

    def get_object(self):
        applicant = self.request.user.applicant
        profile, _ = ApplicantProfile.objects.get_or_create(applicant=applicant)
        return profile


class ApplicationViewSet(AuditMixin, ModelViewSet):
    serializer_class = ApplicationSerializer
    filterset_fields = ['stage', 'job_posting']

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [(IsApplicant | IsRecruiter)()]
        return [IsRecruiter()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'APPLICANT':
            return Application.objects.filter(applicant__user=user).order_by('-applied_at')
        return Application.objects.select_related(
            'applicant', 'job_posting'
        ).order_by('-applied_at')

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def shortlist(self, request, pk=None):
        app = self.get_object()
        if app.stage not in [Application.STATUS_APPLIED, Application.STATUS_UNDER_REVIEW]:
            return Response({'detail': 'Application is not in a shortlistable stage.'}, status=400)

        # AUTO: advance posting to SCREENING
        _advance_posting(app, JobPosting.STATUS_SCREENING)

        # AUTO: create first-round interview scheduled 7 days from now
        interview = Interview.objects.create(
            application=app,
            interview_type=Interview.TYPE_VIDEO,
            status=Interview.STATUS_SCHEDULED,
            scheduled_at=timezone.now() + datetime.timedelta(days=7),
            round_number=1,
            notes='Auto-scheduled after shortlisting. Adjust date/time and add panel members as needed.',
            created_by=request.user,
        )

        app.stage = Application.STATUS_INTERVIEW_SCHEDULED
        app.save()
        log_action(request, 'UPDATE', 'Application', str(app.id), module='recruitment',
                   after_json={'stage': app.stage, 'auto_interview_id': str(interview.id)})
        return Response(ApplicationSerializer(app, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def reject(self, request, pk=None):
        app = self.get_object()
        reason = request.data.get('reason', '')
        app.stage = Application.STATUS_REJECTED
        app.rejection_reason = reason
        app.save()
        return Response(ApplicationSerializer(app, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        app = self.get_object()
        if app.applicant.user != request.user:
            return Response({'detail': 'Not your application.'}, status=403)
        app.stage = Application.STATUS_WITHDRAWN
        app.save()
        return Response(ApplicationSerializer(app, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('APPLICANT_SHORTLIST_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'Application', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('APPLICANT_SHORTLIST_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('APPLICANT_SHORTLIST_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class InterviewViewSet(AuditMixin, ModelViewSet):
    queryset = Interview.objects.select_related('application', 'created_by').order_by('-scheduled_at')
    serializer_class = InterviewSerializer
    permission_classes = [IsRecruiter]
    filterset_fields = ['status', 'interview_type', 'application']

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def complete(self, request, pk=None):
        interview = self.get_object()
        if interview.status == Interview.STATUS_COMPLETED:
            return Response({'detail': 'Interview already completed.'}, status=400)
        interview.status = Interview.STATUS_COMPLETED
        interview.save()
        # AUTO: only advance application when ALL interviews for it are done
        _check_all_interviews_complete(interview.application)
        return Response(InterviewSerializer(interview, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def submit_for_approval(self, request, pk=None):
        obj = self.get_object()
        engine = WorkflowEngine('INTERVIEW_SCHEDULE_APPROVAL')
        if not obj.workflow_request:
            wf_req = engine.create_request(request.user, 'Interview', obj.id)
            obj.workflow_request = wf_req
            obj.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, obj.workflow_request)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def workflow_approve(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('INTERVIEW_SCHEDULE_APPROVAL')
        wf_req = engine.approve(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def workflow_reject(self, request, pk=None):
        obj = self.get_object()
        if not obj.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('INTERVIEW_SCHEDULE_APPROVAL')
        wf_req = engine.reject(request, obj.workflow_request, request.data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_req).data)


class InterviewFeedbackViewSet(AuditMixin, ModelViewSet):
    queryset = InterviewFeedback.objects.all().order_by('-submitted_at')
    serializer_class = InterviewFeedbackSerializer
    filterset_fields = ['interview', 'recommendation']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsRecruiter()]
        return [IsInterviewer()]

    def perform_create(self, serializer):
        feedback = serializer.save()
        # Lock immediately so feedback cannot be edited after submission
        feedback.is_locked = True
        feedback.save(update_fields=['is_locked'])
        # AUTO: if all panel members have submitted, auto-complete the interview
        interview = feedback.interview
        panel_count = interview.panel.count()
        feedback_count = interview.feedbacks.count()
        if panel_count > 0 and feedback_count >= panel_count:
            interview.status = Interview.STATUS_COMPLETED
            interview.save(update_fields=['status'])
            _check_all_interviews_complete(interview.application)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_locked:
            return Response({'detail': 'Feedback is locked and cannot be edited.'}, status=400)
        return super().update(request, *args, **kwargs)


class OfferViewSet(AuditMixin, ModelViewSet):
    queryset = Offer.objects.select_related('application', 'position', 'grade').order_by('-created_at')
    serializer_class = OfferSerializer
    filterset_fields = ['status', 'application']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [(IsRecruiter | IsFinanceChecker)()]
        return [IsRecruiter()]

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def submit_for_approval(self, request, pk=None):
        offer = self.get_object()
        if offer.status != Offer.STATUS_DRAFT:
            return Response({'detail': 'Only draft offers can be submitted.'}, status=400)
        engine = WorkflowEngine('OFFER_APPROVAL')
        if not offer.workflow_request:
            wf_req = engine.create_request(request.user, 'Offer', offer.id)
            offer.workflow_request = wf_req
            offer.save()
        wf_req = engine.submit(request, offer.workflow_request)
        offer.status = Offer.STATUS_SUBMITTED
        offer.save()
        # AUTO: advance posting status
        _advance_posting(offer.application, JobPosting.STATUS_OFFER_SUBMITTED)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsFinanceChecker])
    def approve(self, request, pk=None):
        offer = self.get_object()
        if not offer.workflow_request:
            return Response({'detail': 'No workflow request found.'}, status=400)
        engine = WorkflowEngine('OFFER_APPROVAL')
        wf_req = engine.approve(request, offer.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            offer.status = Offer.STATUS_APPROVED
            offer.save()
            # AUTO: advance posting status
            _advance_posting(offer.application, JobPosting.STATUS_OFFER_APPROVED)
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsApplicant])
    def accept(self, request, pk=None):
        offer = self.get_object()
        if offer.status != Offer.STATUS_SENT:
            return Response({'detail': 'Only sent offers can be accepted.'}, status=400)
        if offer.application.applicant.user != request.user:
            return Response({'detail': 'This offer is not for you.'}, status=403)
        offer.status = Offer.STATUS_ACCEPTED
        offer.accepted_at = timezone.now()
        offer.save()

        application = offer.application
        application.stage = Application.STATUS_ONBOARDING
        application.save()

        log_action(request, 'APPROVE', 'Offer', str(offer.id), module='recruitment',
                   after_json={'status': 'ACCEPTED'})

        # AUTO: advance posting and create onboarding case
        _advance_posting(application, JobPosting.STATUS_ONBOARDING_STARTED)
        onboarding_case = _create_onboarding_case(offer)

        return Response({
            **OfferSerializer(offer, context={'request': request}).data,
            'onboarding_case_id': str(onboarding_case.id),
        })

    @action(detail=True, methods=['post'], permission_classes=[IsApplicant])
    def decline(self, request, pk=None):
        offer = self.get_object()
        if offer.application.applicant.user != request.user:
            return Response({'detail': 'This offer is not for you.'}, status=403)
        offer.status = Offer.STATUS_DECLINED
        offer.declined_reason = request.data.get('reason', '')
        offer.save()
        return Response(OfferSerializer(offer, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecruiter])
    def send(self, request, pk=None):
        offer = self.get_object()
        if offer.status != Offer.STATUS_APPROVED:
            return Response({'detail': 'Offer must be approved before sending.'}, status=400)
        offer.status = Offer.STATUS_SENT
        offer.save()
        offer.application.stage = Application.STATUS_OFFERED
        offer.application.save()
        return Response(OfferSerializer(offer, context={'request': request}).data)


class ApplicantDocumentViewSet(ModelViewSet):
    serializer_class = ApplicantDocumentSerializer
    permission_classes = [IsApplicant]

    def get_queryset(self):
        return ApplicantDocument.objects.filter(applicant__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user.applicant)
