from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'code', 'display_name', 'description', 'is_active']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'phone',
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.user_type = CustomUser.USER_TYPE_EXTERNAL
        user.role = CustomUser.ROLE_APPLICANT
        user.set_password(password)
        user.save()
        # Auto-assign the primary role to the M2M set
        role_obj = Role.objects.filter(code=CustomUser.ROLE_APPLICANT).first()
        if role_obj:
            user.roles.add(role_obj)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled.')
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'role', 'roles', 'phone', 'is_active',
            'is_email_verified', 'date_joined', 'last_login',
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'user_type', 'role', 'roles',
        ]

    def get_roles(self, obj) -> list[str]:
        """All effective role codes: M2M roles + primary role."""
        codes = set(r.code for r in obj.roles.all())
        if obj.role:
            codes.add(obj.role)
        return sorted(codes)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    role_codes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True,
        help_text='List of role codes to assign (replaces existing M2M roles)',
    )
    roles = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'user_type', 'role', 'role_codes', 'roles',
            'phone', 'is_active',
        ]

    def get_roles(self, obj) -> list[str]:
        codes = set(r.code for r in obj.roles.all())
        if obj.role:
            codes.add(obj.role)
        return sorted(codes)

    def _sync_roles(self, user, role_codes):
        """Set the M2M roles from a list of codes. Always includes primary role."""
        codes_to_set = set(role_codes) if role_codes else set()
        if user.role:
            codes_to_set.add(user.role)
        role_objs = Role.objects.filter(code__in=codes_to_set)
        user.roles.set(role_objs)

    def create(self, validated_data):
        role_codes = validated_data.pop('role_codes', [])
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        self._sync_roles(user, role_codes)
        return user

    def update(self, instance, validated_data):
        role_codes = validated_data.pop('role_codes', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if role_codes is not None:
            self._sync_roles(instance, role_codes)
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
