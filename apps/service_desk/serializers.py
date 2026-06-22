from rest_framework import serializers
from .models import TicketCategory, HRTicket, TicketComment, KnowledgeCategory, KnowledgeArticle, SatisfactionSurvey


class TicketCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = TicketCategory
        fields = [
            'id', 'code', 'name', 'description', 'parent', 'parent_name',
            'sla_hours', 'is_confidential', 'is_active',
        ]
        read_only_fields = ['id', 'parent_name']


class TicketCommentSerializer(serializers.ModelSerializer):
    author_display = serializers.SerializerMethodField()

    class Meta:
        model = TicketComment
        fields = [
            'id', 'ticket', 'author', 'author_display',
            'content', 'is_internal', 'attachment', 'created_at',
        ]
        read_only_fields = ['id', 'author', 'author_display', 'created_at']

    def get_author_display(self, obj):
        return obj.author.get_full_name() or obj.author.username

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class HRTicketSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    raised_by_display = serializers.SerializerMethodField()
    assigned_to_display = serializers.SerializerMethodField()
    comments = TicketCommentSerializer(many=True, read_only=True)

    class Meta:
        model = HRTicket
        fields = [
            'id', 'ticket_number', 'category', 'category_name',
            'subject', 'description',
            'raised_by', 'raised_by_display',
            'on_behalf_of', 'status', 'priority',
            'assigned_to', 'assigned_to_display',
            'due_at', 'resolved_at', 'closed_at',
            'satisfaction_score', 'resolution_notes',
            'comments', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'ticket_number', 'raised_by', 'raised_by_display',
            'assigned_to_display', 'category_name', 'comments',
            'resolved_at', 'closed_at', 'created_at', 'updated_at',
        ]

    def get_raised_by_display(self, obj):
        return obj.raised_by.get_full_name() or obj.raised_by.username

    def get_assigned_to_display(self, obj):
        if not obj.assigned_to:
            return None
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def create(self, validated_data):
        validated_data['raised_by'] = self.context['request'].user
        return super().create(validated_data)


class KnowledgeCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True, default=None)

    class Meta:
        model = KnowledgeCategory
        fields = ['id', 'name', 'parent', 'parent_name', 'is_active']
        read_only_fields = ['id', 'parent_name']


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    author_display = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeArticle
        fields = [
            'id', 'category', 'category_name', 'title', 'slug', 'content',
            'tags', 'helpful_count', 'status', 'author', 'author_display',
            'views_count', 'is_featured', 'published_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'author', 'author_display', 'category_name',
            'helpful_count', 'views_count', 'published_at', 'created_at', 'updated_at',
        ]

    def get_author_display(self, obj):
        return obj.author.get_full_name() or obj.author.username

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class SatisfactionSurveySerializer(serializers.ModelSerializer):
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True, default='')

    class Meta:
        model = SatisfactionSurvey
        fields = ['id', 'ticket', 'ticket_number', 'score', 'feedback', 'submitted_at']
        read_only_fields = ['id', 'ticket_number', 'submitted_at']

    def validate_score(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Score must be between 1 and 5.')
        return value
