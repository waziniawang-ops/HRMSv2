from rest_framework import serializers
from .models import WorkflowRule, WorkflowRequest, WorkflowStep, WorkflowComment, WorkflowHistory, WorkflowAttachment, WorkflowActor


class WorkflowRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkflowStepSerializer(serializers.ModelSerializer):
    approver_user_display = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowStep
        fields = [
            'id', 'step_number', 'approver_role', 'approver_user',
            'approver_user_display', 'status', 'action', 'comment',
            'sla_hours', 'acted_at', 'due_at', 'created_at',
        ]
        read_only_fields = fields

    def get_approver_user_display(self, obj):
        if obj.approver_user:
            return obj.approver_user.get_full_name() or obj.approver_user.username
        return None


class WorkflowCommentSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowComment
        fields = ['id', 'step', 'user', 'user_display', 'comment', 'visibility', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def get_user_display(self, obj):
        return obj.user.get_full_name() or obj.user.username


class WorkflowHistorySerializer(serializers.ModelSerializer):
    actor_display = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowHistory
        fields = [
            'id', 'from_status', 'to_status', 'actor', 'actor_display',
            'step_number', 'comment', 'created_at',
        ]
        read_only_fields = fields

    def get_actor_display(self, obj):
        return obj.actor.get_full_name() or obj.actor.username


class WorkflowRequestSerializer(serializers.ModelSerializer):
    steps = WorkflowStepSerializer(many=True, read_only=True)
    comments = WorkflowCommentSerializer(many=True, read_only=True)
    history = WorkflowHistorySerializer(many=True, read_only=True)
    maker_display = serializers.SerializerMethodField()
    workflow_code = serializers.CharField(source='workflow_rule.workflow_code', read_only=True)

    class Meta:
        model = WorkflowRequest
        fields = [
            'id', 'workflow_code', 'module_code', 'object_type', 'object_id',
            'maker_user', 'maker_display', 'status', 'current_step',
            'submitted_at', 'completed_at', 'created_at', 'updated_at',
            'steps', 'comments', 'history',
        ]
        read_only_fields = fields

    def get_maker_display(self, obj):
        return obj.maker_user.get_full_name() or obj.maker_user.username


class WorkflowActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        return data


class WorkflowRejectSerializer(serializers.Serializer):
    comment = serializers.CharField(required=True, min_length=5)


class WorkflowAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_display = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowAttachment
        fields = [
            'id', 'workflow_request', 'file', 'original_filename',
            'description', 'uploaded_by', 'uploaded_by_display', 'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_by_display', 'uploaded_at']

    def get_uploaded_by_display(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        validated_data['original_filename'] = validated_data.get('file').name
        return super().create(validated_data)


class WorkflowActorSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowActor
        fields = [
            'id', 'workflow_request', 'user', 'user_display', 'role', 'assigned_at',
        ]
        read_only_fields = ['id', 'user_display', 'assigned_at']

    def get_user_display(self, obj):
        return obj.user.get_full_name() or obj.user.username
