from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from apps.accounts.permissions import IsHRStaff, IsHRMaker, IsHRChecker

from .models import BenefitPlan, EligibilityRule, BenefitEnrollment, BenefitDependent, BenefitClaimReference, BenefitCost
from .serializers import (
    BenefitPlanSerializer, EligibilityRuleSerializer, BenefitEnrollmentSerializer,
    BenefitDependentSerializer, BenefitClaimReferenceSerializer, BenefitCostSerializer,
)


class BenefitPlanViewSet(AuditMixin, ModelViewSet):
    queryset = BenefitPlan.objects.all().order_by('name')
    serializer_class = BenefitPlanSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name', 'provider']

    @action(detail=True, methods=['get'])
    def check_eligibility(self, request, pk=None):
        plan = self.get_object()
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response({'detail': 'employee_id query param required.'}, status=400)

        from apps.core_hr.models import Employee
        try:
            employee = Employee.objects.select_related('grade').get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'detail': 'Employee not found.'}, status=404)

        rules = plan.eligibility_rules.filter(is_active=True)
        if not rules.exists():
            return Response({'eligible': True, 'reason': 'No eligibility restrictions defined.'})

        from django.utils import timezone as tz
        from datetime import date
        months_of_service = 0
        if employee.hire_date:
            delta = date.today() - employee.hire_date
            months_of_service = delta.days // 30

        for rule in rules:
            grade_match = (rule.grade is None) or (rule.grade == employee.grade)
            emp_type = getattr(employee, 'employment_type', '')
            type_match = (not rule.employment_type) or (rule.employment_type == emp_type)
            service_match = months_of_service >= rule.min_service_months
            if grade_match and type_match and service_match:
                return Response({'eligible': True, 'reason': 'Employee meets eligibility criteria.'})

        return Response({'eligible': False, 'reason': 'Employee does not meet any eligibility rule.'})


class EligibilityRuleViewSet(AuditMixin, ModelViewSet):
    queryset = EligibilityRule.objects.select_related('plan', 'grade').order_by('plan', 'grade')
    serializer_class = EligibilityRuleSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['plan', 'grade', 'is_active', 'employment_type']


class BenefitEnrollmentViewSet(AuditMixin, ModelViewSet):
    queryset = BenefitEnrollment.objects.select_related(
        'employee__person', 'plan', 'approved_by'
    ).order_by('-enrollment_date')
    serializer_class = BenefitEnrollmentSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employee', 'plan', 'status']

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def submit_for_approval(self, request, pk=None):
        enrollment = self.get_object()
        from apps.workflow.engine import WorkflowEngine
        engine = WorkflowEngine('BENEFIT_ENROLLMENT_APPROVAL')
        if not enrollment.workflow_request:
            wf_req = engine.create_request(request.user, 'BenefitEnrollment', enrollment.id)
            enrollment.workflow_request = wf_req
            enrollment.save(update_fields=['workflow_request'])
        wf_req = engine.submit(request, enrollment.workflow_request)
        from apps.workflow.serializers import WorkflowRequestSerializer
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        enrollment = self.get_object()
        if not enrollment.workflow_request:
            return Response({'detail': 'No workflow request.'}, status=400)
        from apps.workflow.engine import WorkflowEngine
        from apps.workflow.models import WorkflowRequest
        engine = WorkflowEngine('BENEFIT_ENROLLMENT_APPROVAL')
        wf_req = engine.approve(request, enrollment.workflow_request, request.data.get('comment', ''))
        if wf_req.status == WorkflowRequest.STATUS_APPROVED:
            enrollment.status = BenefitEnrollment.STATUS_ACTIVE
            enrollment.approved_by = request.user
            enrollment.approved_at = timezone.now()
            enrollment.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        from apps.workflow.serializers import WorkflowRequestSerializer
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        enrollment = self.get_object()
        if not enrollment.workflow_request:
            return Response({'detail': 'No workflow request.'}, status=400)
        from apps.workflow.engine import WorkflowEngine
        engine = WorkflowEngine('BENEFIT_ENROLLMENT_APPROVAL')
        wf_req = engine.reject(request, enrollment.workflow_request, request.data.get('comment', ''))
        from apps.workflow.serializers import WorkflowRequestSerializer
        return Response(WorkflowRequestSerializer(wf_req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def suspend(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.status != BenefitEnrollment.STATUS_ACTIVE:
            return Response({'detail': 'Only active enrollments can be suspended.'}, status=400)
        enrollment.status = BenefitEnrollment.STATUS_SUSPENDED
        enrollment.save(update_fields=['status', 'updated_at'])
        return Response(BenefitEnrollmentSerializer(enrollment).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def end_enrollment(self, request, pk=None):
        enrollment = self.get_object()
        if enrollment.status == BenefitEnrollment.STATUS_ENDED:
            return Response({'detail': 'Already ended.'}, status=400)
        end_date = request.data.get('end_date')
        enrollment.status = BenefitEnrollment.STATUS_ENDED
        if end_date:
            enrollment.end_date = end_date
        enrollment.save(update_fields=['status', 'end_date', 'updated_at'])
        return Response(BenefitEnrollmentSerializer(enrollment).data)


class BenefitDependentViewSet(AuditMixin, ModelViewSet):
    queryset = BenefitDependent.objects.select_related('enrollment__employee__person').order_by('name')
    serializer_class = BenefitDependentSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['enrollment', 'relationship', 'is_active']


class BenefitClaimReferenceViewSet(AuditMixin, ModelViewSet):
    queryset = BenefitClaimReference.objects.select_related(
        'enrollment__employee__person', 'enrollment__plan', 'approved_by'
    ).order_by('-claim_date')
    serializer_class = BenefitClaimReferenceSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['enrollment', 'status']

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve_claim(self, request, pk=None):
        claim = self.get_object()
        if claim.status not in [BenefitClaimReference.STATUS_SUBMITTED, BenefitClaimReference.STATUS_PROCESSING]:
            return Response({'detail': 'Claim cannot be approved in current status.'}, status=400)
        approved_amount = request.data.get('approved_amount', claim.amount_claimed)
        claim.status = BenefitClaimReference.STATUS_APPROVED
        claim.amount_approved = approved_amount
        claim.approved_by = request.user
        claim.save(update_fields=['status', 'amount_approved', 'approved_by', 'updated_at'])
        return Response(BenefitClaimReferenceSerializer(claim).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject_claim(self, request, pk=None):
        claim = self.get_object()
        if claim.status not in [BenefitClaimReference.STATUS_SUBMITTED, BenefitClaimReference.STATUS_PROCESSING]:
            return Response({'detail': 'Claim cannot be rejected in current status.'}, status=400)
        claim.status = BenefitClaimReference.STATUS_REJECTED
        claim.save(update_fields=['status', 'updated_at'])
        return Response(BenefitClaimReferenceSerializer(claim).data)


class BenefitCostViewSet(AuditMixin, ModelViewSet):
    queryset = BenefitCost.objects.select_related(
        'enrollment__employee__person', 'enrollment__plan'
    ).order_by('-period_start')
    serializer_class = BenefitCostSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['enrollment', 'is_paid', 'payroll_run']
