from rest_framework.permissions import BasePermission
from .models import CustomUser


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
