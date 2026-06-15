import pytest
from apps.audit.models import AuditLog
from apps.audit.utils import log_action


@pytest.mark.django_db
class TestAuditLog:
    def test_create_audit_log(self, hr_maker):
        from rest_framework.test import APIRequestFactory
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = hr_maker
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'TestAgent'
        request.correlation_id = 'test-correlation-id'

        log = log_action(request, 'CREATE', 'TestModel', 'test-id-123')
        assert log is not None
        assert log.action == 'CREATE'
        assert log.object_type == 'TestModel'
        assert log.actor_user == hr_maker

    def test_audit_log_immutable(self, db, hr_maker):
        log = AuditLog.objects.create(
            actor_user=hr_maker,
            action='CREATE',
            object_type='TestModel',
            object_id='test-id',
        )
        log.action = 'MODIFIED'
        with pytest.raises(PermissionError):
            log.save()

    def test_audit_log_not_deletable(self, db, hr_maker):
        log = AuditLog.objects.create(
            actor_user=hr_maker,
            action='CREATE',
            object_type='TestModel',
            object_id='test-id-2',
        )
        with pytest.raises(PermissionError):
            log.delete()
