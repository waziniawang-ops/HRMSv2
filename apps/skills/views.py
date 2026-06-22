from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin
from apps.accounts.permissions import IsHRStaff, IsInternalUser
from apps.audit.utils import log_action

from .models import (
    SkillCategory, Skill, ProficiencyScale, JobSkillRequirement,
    EmployeeSkill, SkillEvidence, SkillGapAnalysis, SkillGap,
)
from .serializers import (
    SkillCategorySerializer, SkillSerializer, ProficiencyScaleSerializer,
    JobSkillRequirementSerializer, EmployeeSkillSerializer, SkillEvidenceSerializer,
    SkillGapAnalysisSerializer, SkillGapSerializer,
)


class SkillCategoryViewSet(AuditMixin, ModelViewSet):
    queryset = SkillCategory.objects.all().order_by('name')
    serializer_class = SkillCategorySerializer
    filterset_fields = ['is_active', 'parent']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class SkillViewSet(AuditMixin, ModelViewSet):
    queryset = Skill.objects.select_related('category').order_by('name')
    serializer_class = SkillSerializer
    filterset_fields = ['category', 'is_active']
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class ProficiencyScaleViewSet(AuditMixin, ModelViewSet):
    queryset = ProficiencyScale.objects.all().order_by('level')
    serializer_class = ProficiencyScaleSerializer
    search_fields = ['code', 'name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class JobSkillRequirementViewSet(AuditMixin, ModelViewSet):
    queryset = JobSkillRequirement.objects.select_related(
        'job', 'skill', 'required_level'
    ).order_by('job__job_title', 'skill__name')
    serializer_class = JobSkillRequirementSerializer
    filterset_fields = ['job', 'skill', 'is_mandatory', 'required_level']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInternalUser()]
        return [IsHRStaff()]


class EmployeeSkillViewSet(AuditMixin, ModelViewSet):
    queryset = EmployeeSkill.objects.select_related(
        'employee__person', 'skill__category', 'proficiency', 'endorsed_by'
    ).prefetch_related('evidence_items').order_by('employee__employee_number', 'skill__name')
    serializer_class = EmployeeSkillSerializer
    filterset_fields = ['employee', 'skill', 'proficiency', 'is_endorsed', 'is_self_assessed']
    search_fields = ['employee__employee_number', 'employee__person__legal_name', 'skill__name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_skills', 'endorse']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=True, methods=['post'], permission_classes=[IsInternalUser])
    def endorse(self, request, pk=None):
        emp_skill = self.get_object()
        if emp_skill.endorsed_by == request.user:
            return Response({'detail': 'You have already endorsed this skill.'}, status=400)
        emp_skill.is_endorsed = True
        emp_skill.endorsed_by = request.user
        emp_skill.endorsed_at = timezone.now()
        emp_skill.save(update_fields=['is_endorsed', 'endorsed_by', 'endorsed_at', 'last_updated'])
        log_action(request, 'ENDORSE', 'EmployeeSkill', str(emp_skill.id), module='skills')
        return Response(EmployeeSkillSerializer(emp_skill, context={'request': request}).data)

    @action(detail=False, methods=['get'], permission_classes=[IsInternalUser])
    def my_skills(self, request):
        try:
            employee = request.user.person.employee
        except Exception:
            return Response({'detail': 'No employee record linked to your account.'}, status=400)
        qs = EmployeeSkill.objects.filter(employee=employee).select_related(
            'skill__category', 'proficiency'
        ).prefetch_related('evidence_items')
        return Response(EmployeeSkillSerializer(qs, many=True, context={'request': request}).data)


class SkillEvidenceViewSet(AuditMixin, ModelViewSet):
    queryset = SkillEvidence.objects.select_related('employee_skill', 'verified_by').order_by('-created_at')
    serializer_class = SkillEvidenceSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['employee_skill', 'evidence_type', 'verified']

    @action(detail=True, methods=['post'], permission_classes=[IsHRStaff])
    def verify(self, request, pk=None):
        evidence = self.get_object()
        evidence.verified = True
        evidence.verified_by = request.user
        evidence.save(update_fields=['verified', 'verified_by'])
        return Response(SkillEvidenceSerializer(evidence, context={'request': request}).data)


class SkillGapAnalysisViewSet(AuditMixin, ModelViewSet):
    queryset = SkillGapAnalysis.objects.select_related('employee__person', 'job').order_by('-created_at')
    serializer_class = SkillGapAnalysisSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['employee', 'job']
    http_method_names = ['get', 'post', 'head', 'options']


class SkillGapViewSet(AuditMixin, ModelViewSet):
    queryset = SkillGap.objects.select_related(
        'employee__person', 'skill', 'required_level', 'current_level', 'recommended_course'
    ).order_by('employee__employee_number', 'skill__name')
    serializer_class = SkillGapSerializer
    filterset_fields = ['employee', 'skill', 'status', 'required_level']
    search_fields = ['employee__employee_number', 'skill__name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_gaps', 'run_gap_analysis']:
            return [IsInternalUser()]
        return [IsHRStaff()]

    @action(detail=False, methods=['get'], permission_classes=[IsInternalUser])
    def my_gaps(self, request):
        try:
            employee = request.user.person.employee
        except Exception:
            return Response({'detail': 'No employee record linked to your account.'}, status=400)
        qs = SkillGap.objects.filter(employee=employee).select_related(
            'skill', 'required_level', 'current_level', 'recommended_course'
        )
        return Response(SkillGapSerializer(qs, many=True, context={'request': request}).data)

    @action(detail=False, methods=['post'], permission_classes=[IsHRStaff])
    def run_gap_analysis(self, request):
        from apps.core_hr.models import Employee, Job
        employee_id = request.data.get('employee_id')
        job_id = request.data.get('job_id')
        if not employee_id or not job_id:
            return Response({'detail': 'employee_id and job_id are required.'}, status=400)
        try:
            employee = Employee.objects.get(id=employee_id)
            job = Job.objects.get(id=job_id)
        except (Employee.DoesNotExist, Job.DoesNotExist) as e:
            return Response({'detail': str(e)}, status=404)

        requirements = JobSkillRequirement.objects.filter(job=job).select_related('skill', 'required_level')
        employee_skills = {
            es.skill_id: es for es in EmployeeSkill.objects.filter(employee=employee).select_related('proficiency')
        }

        gaps_summary = []
        gap_objects = []
        total_skills = requirements.count()
        matched = 0

        for req in requirements:
            emp_skill = employee_skills.get(req.skill_id)
            current_level = emp_skill.proficiency if emp_skill else None
            gap = req.required_level.level - (current_level.level if current_level else 0)

            if gap <= 0:
                matched += 1

            gaps_summary.append({
                'skill_id': str(req.skill_id),
                'skill_name': req.skill.name,
                'required_level': req.required_level.name,
                'required_level_num': req.required_level.level,
                'current_level': current_level.name if current_level else None,
                'current_level_num': current_level.level if current_level else 0,
                'gap': gap,
                'is_mandatory': req.is_mandatory,
            })

            if gap > 0:
                gap_obj, _ = SkillGap.objects.update_or_create(
                    employee=employee,
                    skill=req.skill,
                    defaults={
                        'required_level': req.required_level,
                        'current_level': current_level,
                        'gap_size': gap,
                        'status': SkillGap.STATUS_OPEN,
                    }
                )
                gap_objects.append(gap_obj)

        match_pct = (matched / total_skills * 100) if total_skills > 0 else 0

        analysis = SkillGapAnalysis.objects.create(
            employee=employee,
            job=job,
            overall_match_percentage=round(match_pct, 2),
            gaps_summary=gaps_summary,
        )

        return Response({
            'analysis': SkillGapAnalysisSerializer(analysis, context={'request': request}).data,
            'gaps': SkillGapSerializer(gap_objects, many=True, context={'request': request}).data,
        }, status=status.HTTP_201_CREATED)
