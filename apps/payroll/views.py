from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from apps.audit.utils import log_action
from apps.accounts.permissions import IsHRStaff, IsHRChecker, IsHRMaker, IsSystemAdmin

from .models import (
    PayrollCalendar, PayrollElement, EmployeePayrollProfile,
    PayrollRun, PayslipLine, Payslip, PayrollAdjustment, PayrollGLPosting,
)
from .serializers import (
    PayrollCalendarSerializer, PayrollElementSerializer, EmployeePayrollProfileSerializer,
    PayrollRunSerializer, PayslipLineSerializer, PayslipSerializer,
    PayrollAdjustmentSerializer, PayrollGLPostingSerializer,
)


class PayrollCalendarViewSet(AuditMixin, ModelViewSet):
    queryset = PayrollCalendar.objects.all().order_by('name')
    serializer_class = PayrollCalendarSerializer
    filterset_fields = ['pay_group', 'is_active']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsHRStaff()]
        return [IsSystemAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PayrollElementViewSet(AuditMixin, ModelViewSet):
    queryset = PayrollElement.objects.all().order_by('display_order', 'name')
    serializer_class = PayrollElementSerializer
    filterset_fields = ['category', 'is_active', 'is_taxable', 'is_pensionable']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsHRStaff()]
        return [IsSystemAdmin()]


class EmployeePayrollProfileViewSet(AuditMixin, ModelViewSet):
    queryset = EmployeePayrollProfile.objects.select_related(
        'employee__person', 'calendar'
    ).order_by('employee__employee_number')
    serializer_class = EmployeePayrollProfileSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['employee', 'calendar', 'is_active']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PayrollRunViewSet(AuditMixin, ModelViewSet):
    queryset = PayrollRun.objects.select_related('calendar', 'created_by', 'approved_by').order_by('-period_start')
    serializer_class = PayrollRunSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['calendar', 'status']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def lock_run(self, request, pk=None):
        run = self.get_object()
        if run.status not in [PayrollRun.STATUS_DRAFT, PayrollRun.STATUS_PROCESSING]:
            return Response({'detail': 'Only draft or processing runs can be locked.'}, status=400)
        run.status = PayrollRun.STATUS_LOCKED
        run.locked_at = timezone.now()
        run.save(update_fields=['status', 'locked_at', 'updated_at'])
        log_action(request, 'LOCK', 'PayrollRun', str(run.id), module='payroll')
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        run = self.get_object()
        if run.status != PayrollRun.STATUS_LOCKED:
            return Response({'detail': 'Only locked runs can be approved.'}, status=400)
        run.status = PayrollRun.STATUS_APPROVED
        run.approved_by = request.user
        run.approved_at = timezone.now()
        run.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        log_action(request, 'APPROVE', 'PayrollRun', str(run.id), module='payroll')
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def mark_paid(self, request, pk=None):
        run = self.get_object()
        if run.status != PayrollRun.STATUS_APPROVED:
            return Response({'detail': 'Only approved runs can be marked as paid.'}, status=400)
        pay_date = request.data.get('pay_date')
        run.status = PayrollRun.STATUS_PAID
        if pay_date:
            run.pay_date = pay_date
        run.save(update_fields=['status', 'pay_date', 'updated_at'])
        log_action(request, 'MARK_PAID', 'PayrollRun', str(run.id), module='payroll')
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRMaker])
    def generate_payslips(self, request, pk=None):
        run = self.get_object()
        if run.status not in [PayrollRun.STATUS_PROCESSING, PayrollRun.STATUS_LOCKED]:
            return Response({'detail': 'Payslips can only be generated for processing or locked runs.'}, status=400)

        from django.db.models import Sum, Q
        employees = PayslipLine.objects.filter(payroll_run=run).values_list('employee', flat=True).distinct()
        created_count = 0

        for emp_id in employees:
            lines = PayslipLine.objects.filter(payroll_run=run, employee_id=emp_id)
            basic = lines.filter(element__category='BASIC').aggregate(s=Sum('amount'))['s'] or 0
            allowances = lines.filter(element__category='ALLOWANCE').aggregate(s=Sum('amount'))['s'] or 0
            gross = basic + allowances
            deductions = lines.filter(is_deduction=True).aggregate(s=Sum('amount'))['s'] or 0
            tax = lines.filter(element__category='TAX').aggregate(s=Sum('amount'))['s'] or 0
            pension = lines.filter(element__category='CONTRIBUTION').aggregate(s=Sum('amount'))['s'] or 0
            net = gross - deductions

            payslip, created = Payslip.objects.update_or_create(
                payroll_run=run, employee_id=emp_id,
                defaults={
                    'basic_pay': basic,
                    'total_allowances': allowances,
                    'gross_pay': gross,
                    'total_deductions': deductions,
                    'tax_amount': tax,
                    'pension_amount': pension,
                    'net_pay': net,
                    'payslip_date': run.period_end,
                    'generated_at': timezone.now(),
                }
            )
            if created:
                created_count += 1

        total_gross = Payslip.objects.filter(payroll_run=run).aggregate(s=Sum('gross_pay'))['s'] or 0
        total_ded = Payslip.objects.filter(payroll_run=run).aggregate(s=Sum('total_deductions'))['s'] or 0
        total_net = Payslip.objects.filter(payroll_run=run).aggregate(s=Sum('net_pay'))['s'] or 0
        emp_count = Payslip.objects.filter(payroll_run=run).count()
        run.total_gross = total_gross
        run.total_deductions = total_ded
        run.total_net = total_net
        run.employee_count = emp_count
        run.save(update_fields=['total_gross', 'total_deductions', 'total_net', 'employee_count', 'updated_at'])

        log_action(request, 'GENERATE_PAYSLIPS', 'PayrollRun', str(run.id), module='payroll')
        return Response({'created': created_count, 'total_employees': emp_count})


class PayslipLineViewSet(AuditMixin, ModelViewSet):
    queryset = PayslipLine.objects.select_related(
        'employee__person', 'element', 'payroll_run'
    ).order_by('element__display_order')
    serializer_class = PayslipLineSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['payroll_run', 'employee', 'element', 'is_deduction']


class PayslipViewSet(AuditMixin, ModelViewSet):
    queryset = Payslip.objects.select_related(
        'employee__person', 'payroll_run__calendar'
    ).order_by('-payslip_date')
    serializer_class = PayslipSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['payroll_run', 'employee', 'is_locked']
    http_method_names = ['get', 'head', 'options']


class PayrollAdjustmentViewSet(AuditMixin, ModelViewSet):
    queryset = PayrollAdjustment.objects.select_related(
        'employee__person', 'element', 'payroll_run'
    ).order_by('-created_at')
    serializer_class = PayrollAdjustmentSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['payroll_run', 'employee', 'status']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def approve(self, request, pk=None):
        adj = self.get_object()
        if adj.status != PayrollAdjustment.STATUS_PENDING:
            return Response({'detail': 'Only pending adjustments can be approved.'}, status=400)
        adj.status = PayrollAdjustment.STATUS_APPROVED
        adj.approved_by = request.user
        adj.save(update_fields=['status', 'approved_by', 'updated_at'])
        return Response(PayrollAdjustmentSerializer(adj).data)

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def reject(self, request, pk=None):
        adj = self.get_object()
        if adj.status != PayrollAdjustment.STATUS_PENDING:
            return Response({'detail': 'Only pending adjustments can be rejected.'}, status=400)
        adj.status = PayrollAdjustment.STATUS_REJECTED
        adj.save(update_fields=['status', 'updated_at'])
        return Response(PayrollAdjustmentSerializer(adj).data)


class PayrollGLPostingViewSet(AuditMixin, ModelViewSet):
    queryset = PayrollGLPosting.objects.select_related('payroll_run', 'cost_center').order_by('posting_date')
    serializer_class = PayrollGLPostingSerializer
    permission_classes = [IsHRStaff]
    filterset_fields = ['payroll_run', 'is_posted', 'cost_center']

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def post_to_gl(self, request, pk=None):
        posting = self.get_object()
        if posting.is_posted:
            return Response({'detail': 'Already posted.'}, status=400)
        posting.is_posted = True
        posting.posted_at = timezone.now()
        posting.save(update_fields=['is_posted', 'posted_at'])
        log_action(request, 'POST_GL', 'PayrollGLPosting', str(posting.id), module='payroll')
        return Response(PayrollGLPostingSerializer(posting).data)
