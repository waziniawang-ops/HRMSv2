from django.db.models import Count, Avg, Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsHRStaff, IsInternalUser, IsHRPerformance, IsLDOfficer, IsLDChecker,
    IsTalentCommittee, IsRecruiter, IsHiringManager,
)


class HRDashboardView(APIView):
    permission_classes = [IsHRStaff]

    def get(self, request):
        from apps.core_hr.models import Employee, Position, OrgUnit
        from apps.recruitment.models import JobRequisition, JobPosting, Application, Offer
        from apps.onboarding.models import OnboardingCase
        from apps.workflow.models import WorkflowRequest

        total_employees = Employee.objects.filter(
            employment_status__in=['ACTIVE', 'PROBATION']
        ).count()

        open_vacancies = Position.objects.filter(status='VACANT').count()

        pending_approvals = WorkflowRequest.objects.filter(
            status__in=['SUBMITTED', 'IN_REVIEW']
        ).count()

        active_requisitions = JobRequisition.objects.filter(
            status='APPROVED'
        ).count()

        open_postings = JobPosting.objects.filter(status='POSTED').count()

        pending_onboarding = OnboardingCase.objects.filter(
            status__in=['STARTED', 'IN_PROGRESS', 'PENDING_HR']
        ).count()

        new_hires_this_month = Employee.objects.filter(
            hire_date__year=timezone.localdate().year,
            hire_date__month=timezone.localdate().month,
        ).count()

        return Response({
            'total_active_employees': total_employees,
            'open_vacancies': open_vacancies,
            'pending_approvals': pending_approvals,
            'active_requisitions': active_requisitions,
            'open_job_postings': open_postings,
            'pending_onboarding_cases': pending_onboarding,
            'new_hires_this_month': new_hires_this_month,
        })


class HeadcountByOrgUnitView(APIView):
    permission_classes = [IsHRStaff]

    def get(self, request):
        from apps.core_hr.models import Employee
        data = Employee.objects.filter(
            employment_status__in=['ACTIVE', 'PROBATION']
        ).values(
            'org_unit__id', 'org_unit__name', 'org_unit__type'
        ).annotate(
            headcount=Count('id')
        ).order_by('-headcount')
        return Response(list(data))


class HiringFunnelView(APIView):
    permission_classes = [IsHRStaff | IsRecruiter | IsHiringManager]

    def get(self, request):
        from apps.recruitment.models import Application, Offer, JobPosting
        year = int(request.query_params.get('year', timezone.localdate().year))

        applications = Application.objects.filter(
            applied_at__year=year
        ).count()

        shortlisted = Application.objects.filter(
            applied_at__year=year,
            stage__in=['SCREENING', 'INTERVIEW', 'OFFER', 'ONBOARDING']
        ).count()

        offers_made = Offer.objects.filter(
            created_at__year=year
        ).count()

        offers_accepted = Offer.objects.filter(
            created_at__year=year,
            status='ACCEPTED'
        ).count()

        return Response({
            'year': year,
            'total_applications': applications,
            'shortlisted': shortlisted,
            'offers_made': offers_made,
            'offers_accepted': offers_accepted,
            'offer_acceptance_rate': round((offers_accepted / offers_made * 100) if offers_made else 0, 1),
        })


class TimeToHireView(APIView):
    permission_classes = [IsHRStaff | IsRecruiter | IsHiringManager]

    def get(self, request):
        from apps.recruitment.models import Offer, JobRequisition
        from django.db.models import ExpressionWrapper, F, DurationField, Avg

        year = int(request.query_params.get('year', timezone.localdate().year))

        accepted_offers = Offer.objects.filter(
            status='ACCEPTED',
            created_at__year=year,
        ).select_related('application__job_posting__requisition')

        total_days = 0
        count = 0
        for offer in accepted_offers:
            try:
                req = offer.application.job_posting.requisition
                if req.created_at:
                    days = (offer.created_at.date() - req.created_at.date()).days
                    total_days += days
                    count += 1
            except Exception:
                pass

        avg_days = round(total_days / count, 1) if count else 0

        return Response({
            'year': year,
            'hires_count': count,
            'avg_time_to_hire_days': avg_days,
        })


class SuccessionRiskView(APIView):
    permission_classes = [IsHRStaff | IsTalentCommittee]

    def get(self, request):
        from apps.succession.models import SuccessionPlan, TalentProfile

        critical_no_plan = 0
        from apps.core_hr.models import Position
        critical_positions = Position.objects.filter(is_critical=True, status__in=['OCCUPIED', 'VACANT'])
        critical_ids_with_plan = set(
            SuccessionPlan.objects.filter(
                position__in=critical_positions,
                status__in=['ACTIVE', 'APPROVED']
            ).values_list('position_id', flat=True)
        )
        critical_no_plan = critical_positions.exclude(id__in=critical_ids_with_plan).count()

        high_risk_plans = SuccessionPlan.objects.filter(risk_level='CRITICAL').count()
        high_flight_risk = TalentProfile.objects.filter(flight_risk='HIGH').count()

        single_successor = SuccessionPlan.objects.filter(
            status__in=['ACTIVE', 'APPROVED']
        ).annotate(
            nominee_count=Count('nominees')
        ).filter(nominee_count__lte=1).count()

        return Response({
            'critical_positions_without_plan': critical_no_plan,
            'high_risk_succession_plans': high_risk_plans,
            'high_flight_risk_employees': high_flight_risk,
            'plans_with_single_or_no_successor': single_successor,
        })


class PerformanceDistributionView(APIView):
    permission_classes = [IsHRStaff | IsHRPerformance]

    def get(self, request):
        from apps.performance.models import FinalOutcome

        year = int(request.query_params.get('year', timezone.localdate().year))
        distribution = FinalOutcome.objects.filter(
            cycle__cycle_year=year
        ).values('outcome_label').annotate(count=Count('id')).order_by('outcome_label')

        avg_rating = FinalOutcome.objects.filter(
            cycle__cycle_year=year
        ).aggregate(avg=Avg('final_rating'))

        return Response({
            'year': year,
            'distribution': list(distribution),
            'average_rating': round(float(avg_rating['avg'] or 0), 2),
        })


class LearningComplianceView(APIView):
    permission_classes = [IsHRStaff | IsLDOfficer | IsLDChecker]

    def get(self, request):
        from apps.learning.models import LearningAssignment, Course
        total = LearningAssignment.objects.filter(
            course__is_mandatory=True
        ).count()
        completed = LearningAssignment.objects.filter(
            course__is_mandatory=True,
            status='COMPLETED'
        ).count()
        overdue = LearningAssignment.objects.filter(
            course__is_mandatory=True,
            status='OVERDUE'
        ).count()

        compliance_rate = round((completed / total * 100) if total else 0, 1)
        return Response({
            'mandatory_assignments_total': total,
            'completed': completed,
            'overdue': overdue,
            'compliance_rate': compliance_rate,
        })


class AttritionReportView(APIView):
    permission_classes = [IsHRStaff]

    def get(self, request):
        from apps.workforce.models import Separation
        from apps.core_hr.models import Employee
        year = int(request.query_params.get('year', timezone.localdate().year))

        separations = Separation.objects.filter(
            last_working_date__year=year,
            status='COMPLETED'
        ).values('separation_type').annotate(count=Count('id'))

        avg_active = Employee.objects.filter(
            employment_status__in=['ACTIVE', 'PROBATION']
        ).count()

        total_exits = sum(s['count'] for s in separations)
        attrition_rate = round((total_exits / avg_active * 100) if avg_active else 0, 1)

        return Response({
            'year': year,
            'separations_by_type': list(separations),
            'total_exits': total_exits,
            'attrition_rate_pct': attrition_rate,
        })
