from rest_framework import serializers
from .models import OnboardingTemplate, OnboardingCase, OnboardingTask, OnboardingDocument


class OnboardingTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingTemplate
        fields = ['id', 'code', 'name', 'description', 'tasks', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class OnboardingDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_display = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingDocument
        fields = [
            'id', 'document_type', 'name', 'file',
            'uploaded_by', 'uploaded_by_display',
            'is_verified', 'verified_by', 'verified_at', 'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'is_verified', 'verified_by', 'verified_at', 'uploaded_at']

    def get_uploaded_by_display(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class OnboardingTaskSerializer(serializers.ModelSerializer):
    documents = OnboardingDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = OnboardingTask
        fields = [
            'id', 'task_code', 'title', 'description', 'is_required', 'order',
            'status', 'completed_by', 'completed_at', 'hr_verified', 'notes',
            'created_at', 'documents',
        ]
        read_only_fields = ['id', 'completed_by', 'completed_at', 'hr_verified', 'created_at']


class OnboardingCaseSerializer(serializers.ModelSerializer):
    tasks = OnboardingTaskSerializer(many=True, read_only=True)
    completion_percentage = serializers.IntegerField(read_only=True)
    applicant_name = serializers.CharField(
        source='offer.application.applicant.full_name', read_only=True
    )
    position_title = serializers.CharField(
        source='offer.position.title', read_only=True
    )
    assigned_hr_display = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingCase
        fields = [
            'id', 'offer', 'applicant_name', 'position_title',
            'candidate_person', 'template', 'status', 'target_start_date',
            'assigned_hr', 'assigned_hr_display', 'hr_verified_at', 'completed_at', 'notes',
            'completion_percentage', 'created_at', 'updated_at', 'tasks',
        ]

    def get_assigned_hr_display(self, obj):
        if obj.assigned_hr:
            return obj.assigned_hr.get_full_name() or obj.assigned_hr.username
        return None
        read_only_fields = [
            'id', 'hr_verified_at', 'hr_verified_by', 'completed_at', 'created_at', 'updated_at'
        ]
