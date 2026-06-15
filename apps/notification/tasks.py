from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, notification_id: str):
    from .models import Notification
    from .services import _dispatch_email
    try:
        notification = Notification.objects.get(id=notification_id)
        if notification.status == Notification.STATUS_SENT:
            return
        _dispatch_email(notification)
    except Notification.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def send_pending_notifications():
    """Celery beat task: retry FAILED notifications."""
    from .models import Notification
    from .services import _dispatch_email
    failed = Notification.objects.filter(
        status=Notification.STATUS_FAILED,
        channel=Notification.CHANNEL_EMAIL,
    ).select_related('recipient')[:50]
    for notif in failed:
        _dispatch_email(notif)


@shared_task
def mark_overdue_learning_assignments():
    """Celery beat task: mark overdue learning assignments."""
    from apps.learning.models import LearningAssignment
    today = timezone.localdate()
    overdue = LearningAssignment.objects.filter(
        status=LearningAssignment.STATUS_ASSIGNED,
        due_date__lt=today,
    )
    count = overdue.update(status=LearningAssignment.STATUS_OVERDUE)
    return f"Marked {count} assignments as overdue"


@shared_task
def send_upcoming_review_reminders():
    """Celery beat task: remind employees of upcoming reviews."""
    from datetime import timedelta
    from apps.performance.models import ReviewForm, PerformanceCycle
    from .services import send_notification
    from .models import Notification
    from apps.accounts.models import CustomUser

    reminder_date = timezone.localdate() + timedelta(days=7)
    pending_forms = ReviewForm.objects.filter(
        status=ReviewForm.STATUS_IN_PROGRESS,
        cycle__year_end_end=reminder_date,
    ).select_related('employee__person__user', 'cycle')

    for form in pending_forms:
        try:
            user = form.employee.person.user
            send_notification(
                recipient=user,
                template_code='REVIEW_REMINDER',
                context={
                    'cycle': str(form.cycle),
                    'review_type': form.get_review_type_display(),
                    'due_date': str(reminder_date),
                },
                channel=Notification.CHANNEL_IN_APP,
                reference_type='ReviewForm',
                reference_id=str(form.id),
            )
        except Exception:
            pass
