from rest_framework import serializers

from .crypto import encrypt_secret
from .models import Tenant, Plan, Module


class ModuleSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'code', 'name', 'category', 'category_display', 'description', 'is_active']
        read_only_fields = ['id']


class PlanSerializer(serializers.ModelSerializer):
    modules = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all(), many=True, required=False)
    module_details = ModuleSerializer(source='modules', many=True, read_only=True)
    tenant_count = serializers.IntegerField(source='tenants.count', read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description', 'monthly_price', 'seat_limit',
            'is_active', 'modules', 'module_details', 'tenant_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    plan_detail = PlanSerializer(source='plan', read_only=True)
    provisioning_status_display = serializers.CharField(source='get_provisioning_status_display', read_only=True)
    # Whether TenantViewSet's reveal-password action has anything to decrypt
    # for this tenant — never the ciphertext itself, which this serializer
    # never exposes at all (only the dedicated action does, on demand).
    has_stored_password = serializers.SerializerMethodField()
    # oauth_client_secret is write-only and never round-trips back out —
    # same "never expose the plaintext" rule as the password fields above.
    # Omitting it (or sending '') on an update keeps whatever secret is
    # already stored rather than clearing it, so an operator editing other
    # tenant fields doesn't accidentally break SSO.
    oauth_client_secret = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_oauth_client_secret = serializers.SerializerMethodField()
    # Where this tenant's IdP app registration needs its redirect URI set.
    # Render assigns the backend's URL when the service is created, so this is
    # only known once provisioning has created it.
    oauth_redirect_uri = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'domain', 'plan', 'plan_detail',
            'status', 'status_display',
            'admin_first_name', 'admin_last_name', 'admin_email', 'admin_phone', 'has_stored_password',
            'oauth_enabled', 'oauth_issuer', 'oauth_client_id', 'oauth_client_secret',
            'has_oauth_client_secret', 'oauth_button_label', 'oauth_redirect_uri',
            'provisioning_status', 'provisioning_status_display', 'provisioning_error', 'provisioning_log',
            'backend_url', 'frontend_url', 'provisioned_at',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'provisioning_status', 'provisioning_error', 'provisioning_log', 'backend_url', 'frontend_url', 'provisioned_at',
        ]

    def get_has_stored_password(self, obj):
        return bool(obj.admin_password_encrypted)

    def get_has_oauth_client_secret(self, obj):
        return bool(obj.oauth_client_secret_encrypted)

    def get_oauth_redirect_uri(self, obj):
        if not obj.backend_url:
            return None
        return f'{obj.backend_url}/api/v1/auth/oauth/callback/'

    def _encrypt_oauth_secret(self, validated_data):
        secret = validated_data.pop('oauth_client_secret', None)
        if secret:
            try:
                validated_data['oauth_client_secret_encrypted'] = encrypt_secret(secret)
            except Exception as e:
                raise serializers.ValidationError({
                    'oauth_client_secret': f'Could not encrypt this secret — {e}. '
                                            'Is TENANT_ADMIN_PASSWORD_ENCRYPTION_KEY configured on this deployment?',
                })
        return validated_data

    def create(self, validated_data):
        validated_data = self._encrypt_oauth_secret(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._encrypt_oauth_secret(validated_data)
        return super().update(instance, validated_data)
