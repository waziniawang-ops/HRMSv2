from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template import Template, Context

from .models import Notification, NotificationTemplate


def render_template(template_str: str, context: dict) -> str:
    t = Template(template_str)
    return t.render(Context(context))


def send_notification(
    recipient,
    template_code: str,
    context: dict,
    channel: str = Notification.CHANNEL_IN_APP,
    reference_type: str = '',
    reference_id: str = '',
):
    try:
        template = NotificationTemplate.objects.get(code=template_code, channel=channel, is_active=True)
        subject = render_template(template.subject, context)
        body = render_template(template.body_template, context)
    except NotificationTemplate.DoesNotExist:
        subject = context.get('subject', '')
        body = context.get('body', '')
        template = None

    notification = Notification.objects.create(
        recipient=recipient,
        channel=channel,
        subject=subject,
        body=body,
        template=template,
        reference_type=reference_type,
        reference_id=reference_id,
    )

    if channel == Notification.CHANNEL_EMAIL:
        _dispatch_email(notification)
    elif channel == Notification.CHANNEL_IN_APP:
        notification.status = Notification.STATUS_SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])

    return notification


def _dispatch_email(notification: Notification):
    try:
        send_mail(
            subject=notification.subject,
            message=notification.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        notification.status = Notification.STATUS_SENT
        notification.sent_at = timezone.now()
    except Exception as e:
        notification.status = Notification.STATUS_FAILED
        notification.error_message = str(e)
    notification.save(update_fields=['status', 'sent_at', 'error_message'])


def notify_workflow_action(wf_request, action: str, actor):
    """Send in-app and email notification for workflow state changes."""
    maker = wf_request.maker_user
    context = {
        'object_type': wf_request.object_type,
        'object_id': wf_request.object_id,
        'action': action,
        'actor': actor.get_full_name() or actor.username,
        'status': wf_request.status,
    }
    send_notification(
        recipient=maker,
        template_code='WORKFLOW_UPDATE',
        context=context,
        channel=Notification.CHANNEL_IN_APP,
        reference_type='WorkflowRequest',
        reference_id=str(wf_request.id),
    )
    if maker.email:
        send_notification(
            recipient=maker,
            template_code='WORKFLOW_UPDATE',
            context=context,
            channel=Notification.CHANNEL_EMAIL,
            reference_type='WorkflowRequest',
            reference_id=str(wf_request.id),
        )
