from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsSystemAdmin, IsHRStaff, IsInternalUser
from .engine import WorkflowEngine
from .models import WorkflowRule, WorkflowRequest, WorkflowComment, WorkflowAttachment, WorkflowActor
from .serializers import (
    WorkflowRuleSerializer, WorkflowRequestSerializer,
    WorkflowCommentSerializer, WorkflowActionSerializer, WorkflowRejectSerializer,
    WorkflowAttachmentSerializer, WorkflowActorSerializer,
)


class WorkflowRuleViewSet(AuditMixin, ModelViewSet):
    queryset = WorkflowRule.objects.all().order_by('module_code', 'workflow_code')
    serializer_class = WorkflowRuleSerializer
    filterset_fields = ['module_code', 'is_active']

    def get_permissions(self):
        # Anyone on HR staff can read; only System Admin can create/edit/delete
        if self.action in ('list', 'retrieve'):
            return [IsHRStaff()]
        return [IsSystemAdmin()]
    search_fields = ['workflow_code', 'description']


class WorkflowRequestListView(generics.ListAPIView):
    serializer_class = WorkflowRequestSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['status', 'module_code', 'object_type']
    search_fields = ['object_id']

    def get_queryset(self):
        user = self.request.user
        qs = WorkflowRequest.objects.select_related('workflow_rule', 'maker_user')
        if not user.is_hr_staff:
            qs = qs.filter(maker_user=user)
        return qs.order_by('-created_at')


class WorkflowRequestDetailView(generics.RetrieveAPIView):
    serializer_class = WorkflowRequestSerializer
    permission_classes = [IsInternalUser]

    def get_queryset(self):
        user = self.request.user
        qs = WorkflowRequest.objects.select_related('workflow_rule', 'maker_user')
        if not user.is_hr_staff:
            qs = qs.filter(maker_user=user)
        return qs


class WorkflowSubmitView(APIView):
    permission_classes = [IsInternalUser]

    def post(self, request, pk):
        wf_request = WorkflowRequest.objects.get(pk=pk)
        engine = WorkflowEngine(wf_request.workflow_rule.workflow_code)
        wf_request = engine.submit(request, wf_request)
        return Response(WorkflowRequestSerializer(wf_request).data)


class WorkflowApproveView(APIView):
    permission_classes = [IsInternalUser]

    def post(self, request, pk):
        serializer = WorkflowActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wf_request = WorkflowRequest.objects.get(pk=pk)
        engine = WorkflowEngine(wf_request.workflow_rule.workflow_code)
        wf_request = engine.approve(request, wf_request, serializer.validated_data.get('comment', ''))
        return Response(WorkflowRequestSerializer(wf_request).data)


class WorkflowRejectView(APIView):
    permission_classes = [IsInternalUser]

    def post(self, request, pk):
        serializer = WorkflowRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wf_request = WorkflowRequest.objects.get(pk=pk)
        engine = WorkflowEngine(wf_request.workflow_rule.workflow_code)
        wf_request = engine.reject(request, wf_request, serializer.validated_data['comment'])
        return Response(WorkflowRequestSerializer(wf_request).data)


class WorkflowReturnView(APIView):
    permission_classes = [IsInternalUser]

    def post(self, request, pk):
        serializer = WorkflowRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wf_request = WorkflowRequest.objects.get(pk=pk)
        engine = WorkflowEngine(wf_request.workflow_rule.workflow_code)
        wf_request = engine.return_for_amendment(request, wf_request, serializer.validated_data['comment'])
        return Response(WorkflowRequestSerializer(wf_request).data)


class WorkflowAddCommentView(generics.CreateAPIView):
    serializer_class = WorkflowCommentSerializer

    def perform_create(self, serializer):
        wf_request = WorkflowRequest.objects.get(pk=self.kwargs['pk'])
        serializer.save(workflow_request=wf_request, user=self.request.user)


class WorkflowAttachmentViewSet(AuditMixin, ModelViewSet):
    queryset = WorkflowAttachment.objects.select_related('workflow_request', 'uploaded_by').order_by('uploaded_at')
    serializer_class = WorkflowAttachmentSerializer
    filterset_fields = ['workflow_request']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        return [IsInternalUser()]


class WorkflowActorViewSet(AuditMixin, ModelViewSet):
    queryset = WorkflowActor.objects.select_related('workflow_request', 'user').order_by('assigned_at')
    serializer_class = WorkflowActorSerializer
    filterset_fields = ['workflow_request', 'role', 'user']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        return [IsHRStaff()]
