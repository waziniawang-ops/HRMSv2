import logging
from .models import AuditLog

logger = logging.getLogger('apps.audit')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(
    request,
    action,
    object_type,
    object_id='',
    before_json=None,
    after_json=None,
    module='',
    extra=None,
):
    user = None
    ip = None
    user_agent = ''
    correlation_id = ''

    if request:
        user = request.user if request.user.is_authenticated else None
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        correlation_id = request.headers.get('X-Correlation-ID', '')[:100]

    try:
        AuditLog.objects.create(
            actor_user=user,
            action=action,
            object_type=object_type,
            object_id=str(object_id),
            before_json=before_json,
            after_json=after_json,
            ip_address=ip,
            user_agent=user_agent,
            correlation_id=correlation_id,
            module=module,
            extra=extra or {},
        )
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


def log_model_action(request, action, instance, before_data=None, after_data=None):
    model_name = instance.__class__.__name__
    log_action(
        request=request,
        action=action,
        object_type=model_name,
        object_id=str(instance.pk),
        before_json=before_data,
        after_json=after_data,
        module=instance._meta.app_label,
    )
