from rest_framework import serializers
from .models import (
    JobRequisition, JobPosting, Applicant, ApplicantProfile,
    Application, Interview, InterviewFeedback, Offer, ApplicantDocument,
)


class JobRequisitionSerializer(serializers.ModelSerializer):
    position_display = serializers.CharField(source='position.title', read_only=True)
    requested_by_display = serializers.SerializerMethodField()

    class Meta:
        model = JobRequisition
        fields = [
            'id', 'requisition_number', 'position', 'position_display',
            'hiring_reason', 'justification', 'requested_by', 'requested_by_display',
            'status', 'target_start_date', 'budget_confirmed', 'headcount',
            'workflow_request', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'requisition_number', 'requested_by', 'workflow_request', 'created_at', 'updated_at']

    def get_requested_by_display(self, obj):
        return obj.requested_by.get_full_name() or obj.requested_by.username

    def create(self, validated_data):
        validated_data['requested_by'] = self.context['request'].user
        return super().create(validated_data)


class JobPostingSerializer(serializers.ModelSerializer):
    requisition_display = serializers.SerializerMethodField()

    class Meta:
        model = JobPosting
        fields = [
            'id', 'requisition', 'requisition_display', 'title', 'description',
            'requirements', 'responsibilities', 'visibility', 'status',
            'opening_date', 'closing_date', 'screening_questions', 'eligibility_criteria',
            'workflow_request', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'workflow_request', 'created_at', 'updated_at']

    def get_requisition_display(self, obj):
        return str(obj.requisition)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class JobPostingPublicSerializer(serializers.ModelSerializer):
    """Stripped-down serializer for public applicant portal."""
    position_title = serializers.CharField(source='requisition.position.title', read_only=True)
    department = serializers.CharField(source='requisition.position.org_unit.name', read_only=True)
    grade = serializers.CharField(source='requisition.position.grade.grade_name', read_only=True)

    class Meta:
        model = JobPosting
        fields = [
            'id', 'title', 'description', 'requirements', 'responsibilities',
            'position_title', 'department', 'grade',
            'opening_date', 'closing_date', 'screening_questions',
        ]


class ApplicantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicantProfile
        fields = ['id', 'summary', 'education', 'experience', 'skills', 'certifications', 'languages', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class ApplicantSerializer(serializers.ModelSerializer):
    profile = ApplicantProfileSerializer(read_only=True)

    class Meta:
        model = Applicant
        fields = [
            'id', 'email', 'full_name', 'phone', 'profile_status',
            'consent_version', 'resume', 'linkedin_url', 'profile', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'email', 'created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    applicant_display = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job_posting.title', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job_posting', 'job_title', 'applicant', 'applicant_display',
            'stage', 'cover_letter', 'screening_answers', 'score',
            'notes', 'rejection_reason', 'applied_at', 'updated_at',
        ]
        read_only_fields = ['id', 'applicant', 'applied_at', 'updated_at']

    def get_applicant_display(self, obj):
        return obj.applicant.full_name

    def create(self, validated_data):
        user = self.context['request'].user
        try:
            applicant = user.applicant
        except Exception:
            raise serializers.ValidationError("No applicant profile found for this user.")
        validated_data['applicant'] = applicant
        return super().create(validated_data)


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    interviewer_display = serializers.SerializerMethodField()

    class Meta:
        model = InterviewFeedback
        fields = [
            'id', 'interview', 'interviewer', 'interviewer_display',
            'overall_score', 'section_scores', 'strengths',
            'areas_for_improvement', 'recommendation', 'comments',
            'submitted_at', 'is_locked',
        ]
        read_only_fields = ['id', 'interviewer', 'submitted_at', 'is_locked']

    def get_interviewer_display(self, obj):
        return obj.interviewer.get_full_name() or obj.interviewer.username

    def create(self, validated_data):
        validated_data['interviewer'] = self.context['request'].user
        return super().create(validated_data)


class InterviewSerializer(serializers.ModelSerializer):
    feedbacks = InterviewFeedbackSerializer(many=True, read_only=True)
    panel_display = serializers.SerializerMethodField()
    application_display = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'application_display', 'interview_type', 'status',
            'scheduled_at', 'location_or_link', 'panel', 'panel_display',
            'round_number', 'notes', 'created_by', 'created_at', 'feedbacks',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_panel_display(self, obj):
        return [u.get_full_name() or u.username for u in obj.panel.all()]

    def get_application_display(self, obj):
        try:
            return f"{obj.application.applicant.full_name} — {obj.application.job_posting.title}"
        except Exception:
            return str(obj.application_id)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class OfferSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(
        source='application.applicant.full_name', read_only=True
    )
    position_display = serializers.CharField(source='position.title', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'offer_number', 'application', 'applicant_name',
            'position', 'position_display', 'grade', 'basic_salary', 'allowances', 'total_package',
            'employment_type', 'start_date', 'status', 'expiry_date',
            'offer_letter', 'negotiation_notes', 'accepted_at', 'declined_reason',
            'workflow_request', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'offer_number', 'created_by', 'workflow_request', 'accepted_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ApplicantDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ApplicantDocument
        fields = ['id', 'doc_type', 'name', 'file', 'file_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
