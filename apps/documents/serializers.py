from rest_framework import serializers
from .models import DocCategory, DocTemplate, DocRecord, DocPolicy, DocAcknowledgement, RetentionRule


class DocCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocCategory
        fields = ['id', 'code', 'name', 'description', 'is_confidential', 'retention_years', 'is_active']
        read_only_fields = ['id']


class DocTemplateSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = DocTemplate
        fields = [
            'id', 'code', 'name', 'category', 'category_name', 'description',
            'template_file', 'variables', 'version', 'is_active',
            'created_by', 'created_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DocRecordSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True, default=None, allow_null=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True, default=None, allow_null=True)
    uploaded_by_display = serializers.SerializerMethodField()

    class Meta:
        model = DocRecord
        fields = [
            'id', 'title', 'category', 'category_name',
            'employee', 'employee_name', 'employee_number',
            'template', 'file', 'file_size', 'mime_type', 'version',
            'status', 'expiry_date', 'tags', 'is_confidential',
            'uploaded_by', 'uploaded_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'updated_at']

    def get_uploaded_by_display(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class DocPolicySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_display = serializers.SerializerMethodField()
    published_by_display = serializers.SerializerMethodField()
    acknowledgement_count = serializers.SerializerMethodField()

    class Meta:
        model = DocPolicy
        fields = [
            'id', 'code', 'name', 'category', 'category_name',
            'content', 'version', 'status', 'published_at',
            'effective_date', 'expiry_date', 'requires_acknowledgement',
            'acknowledgement_deadline', 'document_file',
            'created_by', 'created_by_display',
            'published_by', 'published_by_display',
            'acknowledgement_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'published_by', 'published_at', 'created_at', 'updated_at']

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_published_by_display(self, obj):
        if not obj.published_by:
            return None
        return obj.published_by.get_full_name() or obj.published_by.username

    def get_acknowledgement_count(self, obj):
        return obj.acknowledgements.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DocAcknowledgementSerializer(serializers.ModelSerializer):
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    policy_code = serializers.CharField(source='policy.code', read_only=True)
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)

    class Meta:
        model = DocAcknowledgement
        fields = [
            'id', 'policy', 'policy_name', 'policy_code',
            'employee', 'employee_name', 'employee_number',
            'version_acknowledged', 'acknowledged_at', 'ip_address',
        ]
        read_only_fields = ['id', 'acknowledged_at']


class RetentionRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = RetentionRule
        fields = [
            'id', 'category', 'category_name', 'retention_years',
            'disposal_action', 'legal_hold_applicable', 'notes', 'is_active',
        ]
        read_only_fields = ['id']
