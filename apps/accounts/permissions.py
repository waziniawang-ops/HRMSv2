from django.conf import settings
from rest_framework.permissions import BasePermission
from .models import CustomUser


def _module_label(view):
    """Derives the owning app's Module.code from a view's module path, e.g.
    'apps.payroll.views' -> 'payroll'. Not URL-prefix-based, because several
    URL prefixes don't match their app label (core vs core_hr, er vs
    employee_relations, ...)."""
    parts = type(view).__module__.split('.')
    return parts[1] if len(parts) >= 2 and parts[0] == 'apps' else None


class IsModuleEnabled(BasePermission):
    """Secondary DEFAULT_PERMISSION_CLASSES layer blocking plan-gated modules
    this tenant's plan doesn't include. Most views set their own
    permission_classes, which replaces the defaults, so the real enforcement
    is apps.accounts.middleware.ModuleGateMiddleware."""

    message = "This module isn't included in your organization's plan."

    def has_permission(self, request, view):
        if not settings.ENABLED_MODULES:
            return True
        module = _module_label(view)
        if module is None or module not in settings.GATEABLE_MODULES:
            return True
        return module in settings.ENABLED_MODULES


class IsInternalUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_internal


class IsHRMaker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_HR_MAKER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsHRChecker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_HR_CHECKER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsHRStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_hr_staff


class IsRecruiter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_RECRUITER, CustomUser.ROLE_HR_MAKER,
            CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsHiringManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_HIRING_MANAGER, CustomUser.ROLE_MANAGER,
            CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsInterviewer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_INTERVIEWER, CustomUser.ROLE_HIRING_MANAGER,
            CustomUser.ROLE_MANAGER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsFinanceChecker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_FINANCE_CHECKER, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsTalentCommittee(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_TALENT_COMMITTEE, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(CustomUser.ROLE_SYSTEM_ADMIN)


class IsApplicant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_applicant_user


class IsLDOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_LD_OFFICER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsLDChecker(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_LD_CHECKER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsHRPerformance(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_HR_PERFORMANCE, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsManagerOrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_MANAGER, CustomUser.ROLE_HIRING_MANAGER,
            CustomUser.ROLE_HR_MAKER, CustomUser.ROLE_HR_CHECKER,
            CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsPayrollOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_PAYROLL_OFFICER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsHSEOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_HSE_OFFICER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsServiceDeskAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_SERVICE_DESK_AGENT, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsERStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_ER_OFFICER, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )


class IsBenefitsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            CustomUser.ROLE_BENEFITS_ADMIN, CustomUser.ROLE_HR_ADMIN, CustomUser.ROLE_SYSTEM_ADMIN
        )
