import pytest
from apps.workflow.models import WorkflowRule, WorkflowRequest
from apps.workflow.engine import WorkflowEngine


@pytest.mark.django_db
class TestWorkflowEngine:
    @pytest.fixture(autouse=True)
    def setup_rule(self, db):
        self.rule = WorkflowRule.objects.create(
            workflow_code='TEST_APPROVAL',
            module_code='test',
            applies_to='TestObject',
            name='Test Approval',
            steps=[
                {'step_number': 1, 'approver_role': 'HR_CHECKER', 'name': 'HR Checker'},
            ],
            segregation_of_duties=True,
            maker_cannot_approve=True,
            is_active=True,
        )

    def test_create_request(self, hr_maker):
        engine = WorkflowEngine('TEST_APPROVAL')
        wf_request = engine.create_request(hr_maker, 'TestObject', 'test-123')
        assert wf_request.status == WorkflowRequest.STATUS_DRAFT
        assert wf_request.steps.count() == 1

    def test_submit_request(self, hr_maker):
        from rest_framework.test import APIRequestFactory
        engine = WorkflowEngine('TEST_APPROVAL')
        wf_request = engine.create_request(hr_maker, 'TestObject', 'test-123')
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = hr_maker
        engine.submit(request, wf_request)
        wf_request.refresh_from_db()
        assert wf_request.status == WorkflowRequest.STATUS_SUBMITTED

    def test_sod_prevents_self_approval(self, hr_maker, hr_checker):
        from rest_framework.test import APIRequestFactory
        from rest_framework.exceptions import PermissionDenied
        engine = WorkflowEngine('TEST_APPROVAL')
        wf_request = engine.create_request(hr_maker, 'TestObject', 'test-456')
        factory = APIRequestFactory()
        submit_req = factory.post('/')
        submit_req.user = hr_maker
        engine.submit(submit_req, wf_request)
        approve_req = factory.post('/')
        approve_req.user = hr_maker
        with pytest.raises(PermissionDenied):
            engine.approve(approve_req, wf_request, comment='approving my own')

    def test_approve_by_checker(self, hr_maker, hr_checker):
        from rest_framework.test import APIRequestFactory
        engine = WorkflowEngine('TEST_APPROVAL')
        wf_request = engine.create_request(hr_maker, 'TestObject', 'test-789')
        factory = APIRequestFactory()
        submit_req = factory.post('/')
        submit_req.user = hr_maker
        engine.submit(submit_req, wf_request)
        approve_req = factory.post('/')
        approve_req.user = hr_checker
        engine.approve(approve_req, wf_request, comment='Approved')
        wf_request.refresh_from_db()
        assert wf_request.status == WorkflowRequest.STATUS_APPROVED
