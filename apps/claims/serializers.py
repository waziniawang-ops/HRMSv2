from rest_framework import serializers
from .models import ClaimType, ExpensePolicy, ClaimRequest, ClaimLine, ClaimReceipt, TravelRequest


class ClaimTypeSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ClaimType
        fields = [
            'id', 'code', 'name', 'category', 'category_display',
            'max_amount_per_claim', 'max_amount_per_year',
            'requires_receipt', 'requires_approval', 'description', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ExpensePolicySerializer(serializers.ModelSerializer):
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = ExpensePolicy
        fields = [
            'id', 'name', 'description', 'effective_date', 'is_active',
            'mileage_rate_per_km', 'per_diem_domestic', 'per_diem_international',
            'meal_allowance_breakfast', 'meal_allowance_lunch', 'meal_allowance_dinner',
            'rules', 'created_by', 'created_by_display', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_created_by_display(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ClaimLineSerializer(serializers.ModelSerializer):
    claim_type_name = serializers.CharField(source='claim_type.name', read_only=True)

    class Meta:
        model = ClaimLine
        fields = [
            'id', 'claim', 'claim_type', 'claim_type_name', 'description',
            'expense_date', 'quantity', 'unit_price', 'amount', 'currency',
            'is_approved', 'remarks',
        ]
        read_only_fields = ['id']


class ClaimReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimReceipt
        fields = ['id', 'claim', 'line', 'file', 'receipt_date', 'amount', 'description', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class ClaimRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_display = serializers.SerializerMethodField()
    lines_count = serializers.SerializerMethodField()

    class Meta:
        model = ClaimRequest
        fields = [
            'id', 'claim_number', 'employee', 'employee_name', 'employee_number',
            'claim_title', 'period_start', 'period_end', 'total_amount', 'currency',
            'notes', 'status', 'status_display', 'workflow_request',
            'submitted_at', 'approved_by', 'approved_by_display', 'approved_at',
            'paid_at', 'lines_count', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'claim_number', 'workflow_request', 'submitted_at',
            'approved_by', 'approved_at', 'paid_at', 'created_at', 'updated_at',
        ]

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username

    def get_lines_count(self, obj):
        return obj.lines.count()


class TravelRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.person.legal_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    travel_type_display = serializers.CharField(source='get_travel_type_display', read_only=True)
    approved_by_display = serializers.SerializerMethodField()

    class Meta:
        model = TravelRequest
        fields = [
            'id', 'request_number', 'employee', 'employee_name', 'employee_number',
            'title', 'destination', 'country_of_travel', 'purpose',
            'departure_date', 'return_date', 'travel_type', 'travel_type_display',
            'estimated_cost', 'currency', 'advance_requested', 'advance_amount',
            'advance_settled', 'itinerary', 'status', 'status_display',
            'workflow_request', 'approved_by', 'approved_by_display', 'approved_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'request_number', 'workflow_request', 'approved_by',
            'approved_at', 'created_at', 'updated_at',
        ]

    def get_approved_by_display(self, obj):
        if not obj.approved_by:
            return None
        return obj.approved_by.get_full_name() or obj.approved_by.username
