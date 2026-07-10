from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from apps.audit.utils import log_action
from apps.accounts.permissions import IsHRStaff, IsHRChecker, IsHRMaker, IsSystemAdmin, IsInternalUser
from apps.core_hr.models import SystemSetting

from .models import (
    PayrollCalendar, PayrollElement, EmployeePayrollProfile,
    PayrollRun, PayslipLine, Payslip, PayrollAdjustment, PayrollGLPosting,
    AccountingIntegration,
)
from .serializers import (
    PayrollCalendarSerializer, PayrollElementSerializer, EmployeePayrollProfileSerializer,
    PayrollRunSerializer, PayslipLineSerializer, PayslipSerializer,
    PayrollAdjustmentSerializer, PayrollGLPostingSerializer, AccountingIntegrationSerializer,
)

NET_PAY_ACCOUNT_KEY = 'PAYROLL_GL_NET_PAY_ACCOUNT'
CONTRIBUTIONS_ACCOUNT_KEY = 'PAYROLL_GL_CONTRIBUTIONS_PAYABLE_ACCOUNT'
NET_PAY_ACCOUNT_DEFAULT = '2100'
CONTRIBUTIONS_ACCOUNT_DEFAULT = '2200'


class PayrollGLSettingsView(APIView):
    """
    GET — returns the GL accounts used by GL posting auto-generation.
          All authenticated internal users can read.
    PUT — updates the accounts. System Admin only.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsInternalUser()]
        return [IsSystemAdmin()]

    def get(self, request):
        net_pay, _ = SystemSetting.objects.get_or_create(
            key=NET_PAY_ACCOUNT_KEY,
            defaults={'value': NET_PAY_ACCOUNT_DEFAULT, 'description': 'GL account credited for net pay payable when generating GL postings'},
        )
        contributions, _ = SystemSetting.objects.get_or_create(
            key=CONTRIBUTIONS_ACCOUNT_KEY,
            defaults={'value': CONTRIBUTIONS_ACCOUNT_DEFAULT, 'description': 'GL account credited for employer contributions payable when generating GL postings'},
        )
        return Response({
            'net_pay_account': net_pay.value,
            'contributions_payable_account': contributions.value,
        })

    def put(self, request):
        net_pay_account = request.data.get('net_pay_account', '').strip()
        contributions_payable_account = request.data.get('contributions_payable_account', '').strip()
        if not net_pay_account or not contributions_payable_account:
            return Response({'detail': 'Both net_pay_account and contributions_payable_account are required.'}, status=400)

        net_pay, _ = SystemSetting.objects.update_or_create(
            key=NET_PAY_ACCOUNT_KEY,
            defaults={'value': net_pay_account, 'updated_by': request.user,
                      'description': 'GL account credited for net pay payable when generating GL postings'},
        )
        contributions, _ = SystemSetting.objects.update_or_create(
            key=CONTRIBUTIONS_ACCOUNT_KEY,
            defaults={'value': contributions_payable_account, 'updated_by': request.user,
                      'description': 'GL account credited for employer contributions payable when generating GL postings'},
        )
        log_action(request, 'UPDATE', 'SystemSetting', NET_PAY_ACCOUNT_KEY, module='payroll',
                   after_json={'net_pay_account': net_pay.value, 'contributions_payable_account': contributions.value})
        return Response({
            'net_pay_account': net_pay.value,
            'contributions_payable_account': contributions.value,
        })


class AccountingIntegrationSettingsView(APIView):
    """
    GET — returns the accounting integration config (API key never included, only
          whether one is set). Readable by HR/payroll staff so the GL Postings page
          can decide whether to enable "Send to Accounting System".
    PUT — updates the config. System Admin only.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsHRStaff()]
        return [IsSystemAdmin()]

    def get(self, request):
        integration = AccountingIntegration.get_settings()
        return Response(AccountingIntegrationSerializer(integration).data)

    def put(self, request):
        integration = AccountingIntegration.get_settings()
        serializer = AccountingIntegrationSerializer(integration, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        log_action(request, 'UPDATE', 'AccountingIntegration', 'settings', module='payroll')
        return Response(AccountingIntegrationSerializer(integration).data)


class AccountingIntegrationTestView(APIView):
    permission_classes = [IsSystemAdmin]

    def post(self, request):
        integration = AccountingIntegration.get_settings()
        if not integration.is_configured:
            return Response({'detail': 'Set the API URL and API key before testing.'}, status=400)

        import requests
        headers = _accounting_auth_headers(integration)
        try:
            resp = requests.post(
                integration.api_url,
                json={'test': True, 'source': 'HRMSv2'},
                headers=headers,
                timeout=8,
            )
            success = resp.ok
            detail = f'HTTP {resp.status_code}' if success else f'HTTP {resp.status_code}: {resp.text[:200]}'
        except requests.RequestException as exc:
            success = False
            detail = str(exc)[:500]

        integration.last_test_at = timezone.now()
        integration.last_test_success = success
        integration.last_test_detail = detail
        integration.save(update_fields=['last_test_at', 'last_test_success', 'last_test_detail'])
        log_action(request, 'TEST_CONNECTION', 'AccountingIntegration', 'settings', module='payroll')
        return Response(AccountingIntegrationSerializer(integration).data, status=200 if success else 502)


def _accounting_auth_headers(integration):
    headers = {'Content-Type': 'application/json'}
    if integration.auth_header_name:
        prefix = f'{integration.auth_header_prefix} ' if integration.auth_header_prefix else ''
        headers[integration.auth_header_name] = f'{prefix}{integration.api_key}'
    return headers


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

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def generate_gl_postings(self, request, pk=None):
        run = self.get_object()
        if run.status not in [PayrollRun.STATUS_LOCKED, PayrollRun.STATUS_APPROVED, PayrollRun.STATUS_PAID]:
            return Response({'detail': 'GL postings can only be generated for locked, approved, or paid runs.'}, status=400)
        if not Payslip.objects.filter(payroll_run=run).exists():
            return Response({'detail': 'Generate payslips before creating GL postings.'}, status=400)

        existing = PayrollGLPosting.objects.filter(payroll_run=run)
        if existing.filter(is_posted=True).exists():
            return Response({'detail': 'GL postings for this run have already been posted and cannot be regenerated.'}, status=400)
        existing.delete()

        from collections import defaultdict
        from django.db.models import Sum
        from apps.core_hr.models import EmployeeAssignment

        def gl_setting(key, default):
            return SystemSetting.objects.filter(key=key).values_list('value', flat=True).first() or default

        net_pay_account = gl_setting(NET_PAY_ACCOUNT_KEY, NET_PAY_ACCOUNT_DEFAULT)
        contributions_account = gl_setting(CONTRIBUTIONS_ACCOUNT_KEY, CONTRIBUTIONS_ACCOUNT_DEFAULT)
        posting_date = run.pay_date or run.period_end

        lines = PayslipLine.objects.filter(payroll_run=run).select_related('element')
        emp_ids = lines.values_list('employee_id', flat=True).distinct()
        cost_centers = {
            a.employee_id: a.position.cost_center
            for a in EmployeeAssignment.objects.filter(
                employee_id__in=emp_ids, is_primary=True, valid_to__isnull=True
            ).select_related('position__cost_center')
        }

        debit_totals = defaultdict(lambda: 0)
        credit_totals = defaultdict(lambda: 0)
        contribution_totals = defaultdict(lambda: 0)

        for line in lines:
            cc = cost_centers.get(line.employee_id)
            key = (line.element.name, line.element.gl_account or 'UNMAPPED', cc)
            if line.element.category in (PayrollElement.CATEGORY_BASIC, PayrollElement.CATEGORY_ALLOWANCE):
                debit_totals[key] += line.amount
            elif line.element.category in (PayrollElement.CATEGORY_DEDUCTION, PayrollElement.CATEGORY_TAX):
                credit_totals[key] += line.amount
            elif line.element.category == PayrollElement.CATEGORY_CONTRIBUTION:
                debit_totals[key] += line.amount
                contribution_totals[cc] += line.amount

        postings = []
        for (elem_name, gl_account, cc), amount in debit_totals.items():
            if amount:
                postings.append(PayrollGLPosting(
                    payroll_run=run, gl_account=gl_account, entry_type=PayrollGLPosting.ENTRY_DEBIT,
                    description=f'{elem_name} expense', amount=amount, cost_center=cc, posting_date=posting_date,
                ))
        for (elem_name, gl_account, cc), amount in credit_totals.items():
            if amount:
                postings.append(PayrollGLPosting(
                    payroll_run=run, gl_account=gl_account, entry_type=PayrollGLPosting.ENTRY_CREDIT,
                    description=f'{elem_name} payable', amount=amount, cost_center=cc, posting_date=posting_date,
                ))
        for cc, amount in contribution_totals.items():
            if amount:
                postings.append(PayrollGLPosting(
                    payroll_run=run, gl_account=contributions_account, entry_type=PayrollGLPosting.ENTRY_CREDIT,
                    description='Employer contributions payable', amount=amount, cost_center=cc, posting_date=posting_date,
                ))

        net_by_cc = defaultdict(lambda: 0)
        for p in Payslip.objects.filter(payroll_run=run):
            net_by_cc[cost_centers.get(p.employee_id)] += p.net_pay
        for cc, amount in net_by_cc.items():
            if amount:
                postings.append(PayrollGLPosting(
                    payroll_run=run, gl_account=net_pay_account, entry_type=PayrollGLPosting.ENTRY_CREDIT,
                    description='Net pay payable', amount=amount, cost_center=cc, posting_date=posting_date,
                ))

        PayrollGLPosting.objects.bulk_create(postings)

        totals = PayrollGLPosting.objects.filter(payroll_run=run).values('entry_type').annotate(total=Sum('amount'))
        total_debit = next((t['total'] for t in totals if t['entry_type'] == PayrollGLPosting.ENTRY_DEBIT), 0) or 0
        total_credit = next((t['total'] for t in totals if t['entry_type'] == PayrollGLPosting.ENTRY_CREDIT), 0) or 0

        log_action(request, 'GENERATE_GL_POSTINGS', 'PayrollRun', str(run.id), module='payroll')
        return Response({
            'created': len(postings),
            'total_debit': total_debit,
            'total_credit': total_credit,
            'balanced': total_debit == total_credit,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def post_gl_postings(self, request, pk=None):
        run = self.get_object()
        postings = PayrollGLPosting.objects.filter(payroll_run=run, is_posted=False)
        count = postings.count()
        if count == 0:
            return Response({'detail': 'No unposted GL postings for this run.'}, status=400)
        postings.update(is_posted=True, posted_at=timezone.now())
        log_action(request, 'POST_ALL_GL', 'PayrollRun', str(run.id), module='payroll')
        return Response({'posted': count})

    @action(detail=True, methods=['get'], permission_classes=[IsHRStaff])
    def export_gl_csv(self, request, pk=None):
        import csv
        from django.http import HttpResponse

        run = self.get_object()
        postings = PayrollGLPosting.objects.filter(payroll_run=run).select_related('cost_center').order_by('posting_date', 'gl_account')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="gl_postings_{run.period_start}_{run.period_end}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'GL Account', 'Description', 'Debit', 'Credit', 'Cost Center', 'Payroll Run', 'Posted'])
        for p in postings:
            writer.writerow([
                p.posting_date.isoformat(),
                p.gl_account,
                p.description,
                p.amount if p.entry_type == PayrollGLPosting.ENTRY_DEBIT else '',
                p.amount if p.entry_type == PayrollGLPosting.ENTRY_CREDIT else '',
                p.cost_center.code if p.cost_center else '',
                str(run.id),
                'Yes' if p.is_posted else 'No',
            ])
        log_action(request, 'EXPORT_GL_CSV', 'PayrollRun', str(run.id), module='payroll')
        return response

    @action(detail=True, methods=['post'], permission_classes=[IsHRChecker])
    def send_gl_to_accounting(self, request, pk=None):
        import requests

        run = self.get_object()
        integration = AccountingIntegration.get_settings()
        if not integration.is_configured:
            return Response({'detail': 'Accounting system API is not configured. Set it up in Settings first.'}, status=400)

        postings = PayrollGLPosting.objects.filter(
            payroll_run=run, is_posted=True, sent_to_accounting_at__isnull=True
        ).select_related('cost_center')
        if not postings.exists():
            return Response({'detail': 'No posted GL entries pending send for this run.'}, status=400)

        payload = {
            'source': 'HRMSv2',
            'payroll_run': str(run.id),
            'period_start': str(run.period_start),
            'period_end': str(run.period_end),
            'entries': [
                {
                    'date': p.posting_date.isoformat(),
                    'account': p.gl_account,
                    'description': p.description,
                    'entry_type': p.entry_type,
                    'amount': str(p.amount),
                    'cost_center': p.cost_center.code if p.cost_center else None,
                }
                for p in postings
            ],
        }

        try:
            resp = requests.post(integration.api_url, json=payload, headers=_accounting_auth_headers(integration), timeout=15)
            if not resp.ok:
                return Response(
                    {'detail': f'Accounting system rejected the request: HTTP {resp.status_code} — {resp.text[:300]}'},
                    status=502,
                )
        except requests.RequestException as exc:
            return Response({'detail': f'Failed to reach accounting system: {exc}'}, status=502)

        count = postings.update(sent_to_accounting_at=timezone.now())
        log_action(request, 'SEND_GL_TO_ACCOUNTING', 'PayrollRun', str(run.id), module='payroll')
        return Response({'sent': count})


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
