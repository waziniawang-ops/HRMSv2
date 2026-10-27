import threading

from django.contrib.auth import authenticate
from django.db.models import ProtectedError
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Tenant, Plan, Module
from .serializers import TenantSerializer, PlanSerializer, ModuleSerializer
from . import provisioning
from .crypto import decrypt_secret, EncryptionNotConfigured, InvalidToken

# Short-lived, process-local holder for each tenant's generated admin
# password — provisioning.provision_tenant() writes to this when it
# succeeds; the API pops (reads-and-deletes) it the first time any response
# includes that tenant, so it's shown to the operator exactly once and never
# written to the database. Acceptable only because provisioning itself is
# also a single-process, in-memory background thread for this v1 (see
# provisioning.py's module docstring) — neither survives a container
# restart, and that trade-off was made together, not independently here.
_provisioning_results = {}


class TenantViewSet(viewsets.ModelViewSet):
    """
    Platform-operator CRUD for tenant metadata. Every action requires an
    authenticated platform-operator login — there is no tenant-scoped access
    here at all, unlike everything else in this codebase; this app has
    exactly one audience.
    """
    queryset = Tenant.objects.all().order_by('name')
    serializer_class = TenantSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        plan_param = self.request.query_params.get('plan')
        search = self.request.query_params.get('search')
        if status_param:
            qs = qs.filter(status=status_param)
        if plan_param:
            qs = qs.filter(plan_id=plan_param)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search) | Q(slug__icontains=search) |
                Q(domain__icontains=search) | Q(admin_email__icontains=search) |
                Q(admin_first_name__icontains=search) | Q(admin_last_name__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        # Set PROVISIONING synchronously, before the background thread even
        # starts, so the create response itself already reflects it — the
        # thread races the response otherwise, and the response would still
        # show the just-created row's NOT_PROVISIONED default.
        tenant = serializer.save(provisioning_status=Tenant.PROVISIONING_IN_PROGRESS)
        threading.Thread(
            target=provisioning.provision_tenant,
            # str() because the registry is keyed to match serialized `id`
            # values (always strings) — provision_tenant() itself re-fetches
            # the Tenant by this id, which works fine as a string too.
            args=(str(tenant.id), _provisioning_results),
            daemon=True,
        ).start()

    # Fields that change what provisioning.sync_backend_config() pushes to
    # the tenant's running backend service — a write that touches any of
    # these needs a resync; anything else (name, notes, admin contact
    # details, ...) doesn't.
    _RESYNC_FIELDS = (
        'plan_id', 'domain', 'oauth_enabled', 'oauth_issuer', 'oauth_client_id',
        'oauth_client_secret_encrypted', 'oauth_button_label',
    )

    def perform_update(self, serializer):
        instance = serializer.instance
        before = {f: getattr(instance, f) for f in self._RESYNC_FIELDS}
        old_status = instance.status
        tenant = serializer.save()
        # Only an ACTIVE tenant has running Render services to act on — a
        # change on a PENDING/FAILED/not-yet-provisioned tenant just takes
        # effect whenever it does eventually get (re)provisioned.
        if tenant.provisioning_status != Tenant.PROVISIONING_ACTIVE:
            return
        if any(getattr(tenant, f) != before[f] for f in self._RESYNC_FIELDS):
            threading.Thread(
                target=provisioning.sync_tenant_modules,
                args=(str(tenant.id),),
                daemon=True,
            ).start()
        # Moving into or out of SUSPENDED really stops/starts the tenant's
        # services, so a suspended tenant's users are actually locked out.
        is_suspended = tenant.status == Tenant.STATUS_SUSPENDED
        if is_suspended != (old_status == Tenant.STATUS_SUSPENDED):
            threading.Thread(
                target=provisioning.set_tenant_suspended,
                args=(str(tenant.id), is_suspended),
                daemon=True,
            ).start()

    def _pop_password(self, data):
        result = _provisioning_results.pop(str(data['id']), None)
        if result:
            data['initial_admin_password'] = result['initial_admin_password']
        return data

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if _provisioning_results:
            for row in response.data.get('results', []):
                self._pop_password(row)
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if _provisioning_results:
            self._pop_password(response.data)
        return response

    def destroy(self, request, *args, **kwargs):
        tenant = self.get_object()
        if tenant.provisioning_status == Tenant.PROVISIONING_IN_PROGRESS:
            return Response(
                {'detail': 'This tenant is still being provisioned — wait for it to finish before deleting it.'},
                status=status.HTTP_409_CONFLICT,
            )
        if tenant.provisioning_status == Tenant.PROVISIONING_DEPROVISIONING:
            return Response(
                {'detail': 'Already deleting this tenant\'s Render services.'},
                status=status.HTTP_409_CONFLICT,
            )
        # Deletion tears down real Render resources (both services + the
        # tenant's database) before the tracking row itself goes away, so it
        # runs in a background thread the same way provisioning does — see
        # provisioning.deprovision_tenant. The row is intentionally NOT
        # deleted here; deprovision_tenant deletes it once teardown actually
        # succeeds, or marks it DEPROVISION_FAILED if it doesn't.
        tenant.provisioning_status = Tenant.PROVISIONING_DEPROVISIONING
        tenant.save(update_fields=['provisioning_status'])
        threading.Thread(
            target=provisioning.deprovision_tenant,
            args=(str(tenant.id),),
            daemon=True,
        ).start()
        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'], url_path='reveal-password')
    def reveal_password(self, request, pk=None):
        """Decrypts and returns this tenant's stored admin password. POST
        (not GET) so it's never triggered by prefetching, caching, or a
        browser preloading a link — this is a deliberate, logged-worthy read
        of a credential, not an idempotent resource fetch."""
        tenant = self.get_object()
        if not tenant.admin_password_encrypted:
            return Response(
                {'detail': 'No stored password for this tenant — it was provisioned before this '
                            'feature existed, or provisioning never completed successfully.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            password = decrypt_secret(tenant.admin_password_encrypted)
        except EncryptionNotConfigured:
            return Response(
                {'detail': 'Password decryption is not configured on this server.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except InvalidToken:
            return Response(
                {'detail': 'Stored password could not be decrypted — the encryption key may have changed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({'admin_password': password})


class ModuleViewSet(viewsets.ModelViewSet):
    """Catalog of gateable HRMSv2 feature areas that plans can include."""
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer


class PlanViewSet(viewsets.ModelViewSet):
    """Subscription tiers and the module sets they unlock."""
    queryset = Plan.objects.all().prefetch_related('modules')
    serializer_class = PlanSerializer

    def perform_update(self, serializer):
        old_module_ids = set(serializer.instance.modules.values_list('id', flat=True))
        old_seat_limit = serializer.instance.seat_limit
        plan = serializer.save()
        new_module_ids = set(plan.modules.values_list('id', flat=True))
        if new_module_ids == old_module_ids and plan.seat_limit == old_seat_limit:
            return
        # Every ACTIVE tenant on this plan needs its deployed backend's
        # ENABLED_MODULES and/or SEAT_LIMIT pushed to match — one background
        # thread per tenant so a plan with many tenants doesn't serialize on
        # Render round-trips.
        tenant_ids = plan.tenants.filter(provisioning_status=Tenant.PROVISIONING_ACTIVE).values_list('id', flat=True)
        for tenant_id in tenant_ids:
            threading.Thread(
                target=provisioning.sync_tenant_modules,
                args=(str(tenant_id),),
                daemon=True,
            ).start()

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            plan = self.get_object()
            count = plan.tenants.count()
            return Response(
                {'detail': f'Cannot delete "{plan.name}" — {count} tenant(s) are still assigned to it. Move them to a different plan first.'},
                status=status.HTTP_409_CONFLICT,
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_staff:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        'username': user.username,
        'email': user.email,
        'is_superuser': user.is_superuser,
    })
