from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.audit.utils import log_action
from .models import WorkflowRule, WorkflowRequest, WorkflowStep, WorkflowHistory


def _notify(wf_request, action: str, actor):
    try:
        from apps.notification.services import notify_workflow_action
        notify_workflow_action(wf_request, action, actor)
    except Exception:
        pass


class WorkflowEngine:
    """
    Generic maker-checker workflow engine.
    Handles submit, approve, reject, return_for_amendment for any domain object.
    Enforces SoD: maker_user != approver_user.
    """

    def __init__(self, workflow_code: str):
        try:
            self.rule = WorkflowRule.objects.get(
                workflow_code=workflow_code, is_active=True
            )
        except WorkflowRule.DoesNotExist:
            raise ValidationError(f"No active workflow rule found for code: {workflow_code}")

    @transaction.atomic
    def create_request(self, maker_user, object_type: str, object_id) -> WorkflowRequest:
        wf_request = WorkflowRequest.objects.create(
            workflow_rule=self.rule,
            module_code=self.rule.module_code,
            object_type=object_type,
            object_id=object_id,
            maker_user=maker_user,
            status=WorkflowRequest.STATUS_DRAFT,
        )
        self._create_pending_steps(wf_request)
        return wf_request

    def _create_pending_steps(self, wf_request: WorkflowRequest):
        for step_config in self.rule.steps:
            sla_hours = step_config.get('sla_hours')
            due_at = None
            if sla_hours:
                due_at = timezone.now() + timezone.timedelta(hours=sla_hours)
            WorkflowStep.objects.create(
                workflow_request=wf_request,
                step_number=step_config['step'],
                approver_role=step_config['role'],
                sla_hours=sla_hours,
                due_at=due_at,
            )

    @transaction.atomic
    def submit(self, request, wf_request: WorkflowRequest) -> WorkflowRequest:
        if wf_request.status not in [
            WorkflowRequest.STATUS_DRAFT,
            WorkflowRequest.STATUS_RETURNED,
        ]:
            raise ValidationError("Only draft or returned requests can be submitted.")

        old_status = wf_request.status
        wf_request.status = (
            WorkflowRequest.STATUS_RESUBMITTED
            if old_status == WorkflowRequest.STATUS_RETURNED
            else WorkflowRequest.STATUS_SUBMITTED
        )
        wf_request.submitted_at = timezone.now()
        wf_request.current_step = 1
        wf_request.save()

        # Reset all steps to pending on resubmit
        wf_request.steps.all().update(
            status=WorkflowStep.STATUS_PENDING,
            action='',
            comment='',
            acted_at=None,
        )

        self._record_history(wf_request, old_status, wf_request.status, request.user)
        log_action(
            request, 'SUBMIT', wf_request.object_type, str(wf_request.object_id),
            module=self.rule.module_code,
        )
        _notify(wf_request, 'submitted', request.user)
        return wf_request

    @transaction.atomic
    def approve(self, request, wf_request: WorkflowRequest, comment: str = '') -> WorkflowRequest:
        self._check_approver_eligibility(request.user, wf_request)

        current_step = self._get_current_step(wf_request)
        self._validate_role(request.user, current_step.approver_role)

        old_status = wf_request.status
        current_step.status = WorkflowStep.STATUS_APPROVED
        current_step.action = WorkflowStep.ACTION_APPROVE
        current_step.comment = comment
        current_step.approver_user = request.user
        current_step.acted_at = timezone.now()
        current_step.save()

        # Check if there are more steps
        next_step = wf_request.steps.filter(
            step_number__gt=current_step.step_number,
            status=WorkflowStep.STATUS_PENDING,
        ).order_by('step_number').first()

        if next_step:
            wf_request.current_step = next_step.step_number
            wf_request.status = WorkflowRequest.STATUS_IN_REVIEW
        else:
            wf_request.status = WorkflowRequest.STATUS_APPROVED
            wf_request.completed_at = timezone.now()

        wf_request.save()
        self._record_history(wf_request, old_status, wf_request.status, request.user, comment=comment)
        log_action(
            request, 'APPROVE', wf_request.object_type, str(wf_request.object_id),
            module=self.rule.module_code,
            extra={'step': current_step.step_number, 'comment': comment},
        )
        action_label = 'approved' if wf_request.status == WorkflowRequest.STATUS_APPROVED else f'step {current_step.step_number} approved'
        _notify(wf_request, action_label, request.user)
        return wf_request

    @transaction.atomic
    def reject(self, request, wf_request: WorkflowRequest, comment: str) -> WorkflowRequest:
        if not comment:
            raise ValidationError("A rejection reason is required.")
        self._check_approver_eligibility(request.user, wf_request)

        current_step = self._get_current_step(wf_request)
        self._validate_role(request.user, current_step.approver_role)

        old_status = wf_request.status
        current_step.status = WorkflowStep.STATUS_REJECTED
        current_step.action = WorkflowStep.ACTION_REJECT
        current_step.comment = comment
        current_step.approver_user = request.user
        current_step.acted_at = timezone.now()
        current_step.save()

        wf_request.status = WorkflowRequest.STATUS_REJECTED
        wf_request.completed_at = timezone.now()
        wf_request.save()

        self._record_history(wf_request, old_status, WorkflowRequest.STATUS_REJECTED, request.user, comment=comment)
        log_action(
            request, 'REJECT', wf_request.object_type, str(wf_request.object_id),
            module=self.rule.module_code,
            extra={'step': current_step.step_number, 'comment': comment},
        )
        _notify(wf_request, 'rejected', request.user)
        return wf_request

    @transaction.atomic
    def return_for_amendment(self, request, wf_request: WorkflowRequest, comment: str) -> WorkflowRequest:
        if not comment:
            raise ValidationError("A return reason is required.")
        self._check_approver_eligibility(request.user, wf_request)

        current_step = self._get_current_step(wf_request)
        self._validate_role(request.user, current_step.approver_role)

        old_status = wf_request.status
        current_step.status = WorkflowStep.STATUS_RETURNED
        current_step.action = WorkflowStep.ACTION_RETURN
        current_step.comment = comment
        current_step.approver_user = request.user
        current_step.acted_at = timezone.now()
        current_step.save()

        wf_request.status = WorkflowRequest.STATUS_RETURNED
        wf_request.save()

        self._record_history(wf_request, old_status, WorkflowRequest.STATUS_RETURNED, request.user, comment=comment)
        log_action(
            request, 'RETURN', wf_request.object_type, str(wf_request.object_id),
            module=self.rule.module_code,
            extra={'step': current_step.step_number, 'comment': comment},
        )
        _notify(wf_request, 'returned for amendment', request.user)
        return wf_request

    def _get_current_step(self, wf_request: WorkflowRequest) -> WorkflowStep:
        if wf_request.status not in [
            WorkflowRequest.STATUS_SUBMITTED,
            WorkflowRequest.STATUS_IN_REVIEW,
            WorkflowRequest.STATUS_RESUBMITTED,
        ]:
            raise ValidationError(f"Workflow is not awaiting review (status: {wf_request.status}).")
        step = wf_request.steps.filter(
            step_number=wf_request.current_step
        ).first()
        if not step:
            raise ValidationError("No current step found for this workflow request.")
        return step

    def _check_approver_eligibility(self, user, wf_request: WorkflowRequest):
        if self.rule.maker_cannot_approve and str(user.id) == str(wf_request.maker_user_id):
            raise PermissionDenied("Maker cannot approve their own workflow request (SoD violation).")

    def _validate_role(self, user, required_role: str):
        if user.role != required_role and user.role not in ['SYSTEM_ADMIN', 'HR_ADMIN']:
            raise PermissionDenied(
                f"Your role '{user.role}' is not authorized for this step. Required: '{required_role}'."
            )

    def _record_history(self, wf_request, from_status, to_status, actor, comment=''):
        WorkflowHistory.objects.create(
            workflow_request=wf_request,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
            step_number=wf_request.current_step,
            comment=comment,
        )


def get_or_create_workflow_request(workflow_code, maker_user, object_type, object_id):
    existing = WorkflowRequest.objects.filter(
        workflow_rule__workflow_code=workflow_code,
        object_type=object_type,
        object_id=object_id,
    ).exclude(status__in=WorkflowRequest.TERMINAL_STATUSES).first()
    if existing:
        return existing, False
    engine = WorkflowEngine(workflow_code)
    return engine.create_request(maker_user, object_type, str(object_id)), True
