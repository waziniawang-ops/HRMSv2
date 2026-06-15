from rest_framework import serializers
from .models import FaceDescriptor, AttendanceRecord


class FaceDescriptorSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    enrolled_by_display = serializers.CharField(source='enrolled_by.get_full_name', read_only=True)

    class Meta:
        model = FaceDescriptor
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'descriptor', 'enrolled_at', 'enrolled_by', 'enrolled_by_display',
        ]
        read_only_fields = ['id', 'enrolled_at', 'enrolled_by']
        extra_kwargs = {'descriptor': {'write_only': True}}

    def validate_descriptor(self, value):
        if not isinstance(value, list) or len(value) != 128:
            raise serializers.ValidationError('Descriptor must be a list of 128 floats.')
        if not all(isinstance(v, (int, float)) for v in value):
            raise serializers.ValidationError('Descriptor values must be numeric.')
        return value

    def create(self, validated_data):
        validated_data['enrolled_by'] = self.context['request'].user
        instance, _ = FaceDescriptor.objects.update_or_create(
            employee=validated_data['employee'],
            defaults=validated_data,
        )
        return instance


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_number = serializers.CharField(source='employee.employee_number', read_only=True)
    hours_worked = serializers.FloatField(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'employee', 'employee_name', 'employee_number',
            'date', 'check_in', 'check_out', 'hours_worked', 'method', 'notes',
        ]
        read_only_fields = ['id']
