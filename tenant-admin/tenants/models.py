import uuid
from django.db import models


class Module(models.Model):
    """
    A gateable HRMSv2 feature area (e.g. Payroll, Succession Planning).
    `code` matches the corresponding Django app label in the main HRMSv2
    codebase (apps/<code>), so a tenant's own deployment can read its
    plan's module list and enforce it directly — that enforcement is a
    later phase; this is the catalog + assignment side.
    """

    CATEGORY_CORE = 'CORE'
    CATEGORY_TALENT = 'TALENT'
    CATEGORY_FINANCE = 'FINANCE'
    CATEGORY_OPERATIONS = 'OPERATIONS'
    CATEGORY_CHOICES = [
        (CATEGORY_CORE, 'Core'),
        (CATEGORY_TALENT, 'Talent'),
        (CATEGORY_FINANCE, 'Finance & Rewards'),
        (CATEGORY_OPERATIONS, 'Operations'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=50, unique=True, help_text='Matches the HRMSv2 app label, e.g. "payroll"')
    name = models.CharField(max_length=100, help_text='Display name, e.g. "Payroll"')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_CORE)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True, help_text='Inactive modules are hidden from the plan editor, not deleted.')

    class Meta:
        db_table = 'module'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class Plan(models.Model):
    """
    A subscription tier tenants are assigned to. Fully operator-configurable
    — unlike the fixed TRIAL/STARTER/PRO/ENTERPRISE strings this replaced,
    new plans can be created without a code change.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text='e.g. "Professional"')
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    monthly_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Leave blank for custom/quote-based pricing (typical for Enterprise).',
    )
    seat_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Leave blank for unlimited seats.')
    modules = models.ManyToManyField(Module, blank=True, related_name='plans')
    is_active = models.BooleanField(default=True, help_text='Inactive plans stay assigned to any tenant already on them, but can\'t be picked for new ones.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plan'
        ordering = ['monthly_price', 'name']

    def __str__(self):
        return self.name


class Tenant(models.Model):
    """
    A customer's HRMSv2 deployment. This row is metadata only — name, domain,
    plan, lifecycle status. It never gains a foreign key into any tenant's
    own HR data (employees, payroll, performance reviews); each tenant's
    data lives in its own separate deployment, by design (see the Silo
    isolation model in the integration plan this app implements).
    """

    STATUS_PENDING = 'PENDING'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_OFFBOARDED = 'OFFBOARDED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending — not yet provisioned'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_OFFBOARDED, 'Offboarded'),
    ]

    PROVISIONING_NOT_PROVISIONED = 'NOT_PROVISIONED'
    PROVISIONING_IN_PROGRESS = 'PROVISIONING'
    PROVISIONING_ACTIVE = 'ACTIVE'
    PROVISIONING_FAILED = 'FAILED'
    PROVISIONING_DEPROVISIONING = 'DEPROVISIONING'
    PROVISIONING_DEPROVISION_FAILED = 'DEPROVISION_FAILED'
    PROVISIONING_STATUS_CHOICES = [
        (PROVISIONING_NOT_PROVISIONED, 'Not provisioned'),
        (PROVISIONING_IN_PROGRESS, 'Provisioning…'),
        (PROVISIONING_ACTIVE, 'Provisioned'),
        (PROVISIONING_FAILED, 'Provisioning failed'),
        (PROVISIONING_DEPROVISIONING, 'Deleting Render services…'),
        (PROVISIONING_DEPROVISION_FAILED, 'Failed to delete Render services'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Customer's company name, e.g. \"Acme Sdn Bhd\"")
    slug = models.SlugField(max_length=100, unique=True, help_text='URL-safe identifier, e.g. "acme"')
    domain = models.CharField(
        max_length=255, blank=True, unique=False, null=True,
        help_text='Custom domain once provisioned, e.g. "acme-hr.com". Blank until Phase 2 automation assigns one.',
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='tenants')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_first_name = models.CharField(max_length=100, blank=True, help_text="Tenant's primary admin user")
    admin_last_name = models.CharField(max_length=100, blank=True, help_text="Tenant's primary admin user")
    admin_email = models.EmailField(blank=True, help_text="Login email for the tenant's admin user once provisioned")
    admin_phone = models.CharField(max_length=30, blank=True, help_text='Optional — for onboarding contact')
    admin_password_encrypted = models.TextField(
        blank=True,
        help_text=(
            "The admin user's generated login password, Fernet-encrypted "
            '(tenants/crypto.py) — set once by provisioning, decrypted on '
            "demand via TenantViewSet's reveal-password action. Never "
            'exposed in plaintext through the normal serializer.'
        ),
    )
    backend_db_url_encrypted = models.TextField(
        blank=True,
        help_text=(
            "The deployed backend service's own DATABASE_URL, "
            'Fernet-encrypted — persisted so provisioning.sync_backend_config '
            "can safely rebuild that app's full config (e.g. after a plan "
            'change alters ENABLED_MODULES) without needing to regenerate it.'
        ),
    )
    backend_secret_key_encrypted = models.TextField(
        blank=True,
        help_text=(
            "The deployed backend service's own Django SECRET_KEY, "
            "Fernet-encrypted — persisted for the same reason as "
            'backend_db_url_encrypted. Regenerating this on every resync '
            'would invalidate every active session/JWT for the tenant, so it '
            'must stay stable across resyncs.'
        ),
    )
    # Generic OpenID Connect SSO for this tenant's own login page — see
    # apps.accounts.oauth in the main app for the client-side flow these
    # fields get pushed into (as OAUTH_* env vars/secrets, by
    # provisioning.create_backend_container_app). One tenant = at most one
    # IdP; this is deliberately NOT a per-provider (Google/Microsoft/...)
    # set of fields — any OIDC-compliant IdP (Entra ID, Google Workspace,
    # Okta, Auth0, a customer's own IdP, ...) works through the same issuer
    # + client id/secret shape.
    oauth_enabled = models.BooleanField(
        default=False,
        help_text='Offer SSO login on this tenant\'s login page, in addition to username/password.',
    )
    oauth_issuer = models.URLField(
        blank=True,
        help_text=(
            "The IdP's OIDC issuer URL, e.g. https://login.microsoftonline.com/<tenant-id>/v2.0 "
            'or https://accounts.google.com — must serve /.well-known/openid-configuration.'
        ),
    )
    oauth_client_id = models.CharField(max_length=255, blank=True, help_text="This tenant's OAuth client ID, from the IdP's app registration.")
    oauth_client_secret_encrypted = models.TextField(
        blank=True,
        help_text=(
            "The OAuth client secret, Fernet-encrypted (tenants/crypto.py) — like the other "
            'encrypted fields on this model, never exposed in plaintext through the normal '
            'serializer. Set via the write-only oauth_client_secret field; leaving that blank '
            'on an update keeps the existing secret rather than clearing it.'
        ),
    )
    oauth_button_label = models.CharField(
        max_length=100, blank=True,
        help_text='Login button text, e.g. "Sign in with Acme Corp SSO". Defaults to "Sign in with SSO" if left blank.',
    )
    notes = models.TextField(blank=True, help_text='Internal notes — provisioning steps done, contract details, etc.')
    provisioning_status = models.CharField(
        max_length=20, choices=PROVISIONING_STATUS_CHOICES, default=PROVISIONING_NOT_PROVISIONED,
        help_text='Set by the automated provisioning flow — not editable by hand.',
    )
    provisioning_error = models.TextField(blank=True, help_text='Set when provisioning_status is FAILED.')
    provisioning_log = models.TextField(
        blank=True,
        help_text=(
            'Timestamped step-by-step progress from the current/most recent provisioning, '
            'deprovisioning, or resync run — reset at the start of each new run. Lets an '
            "operator watch what's happening while provisioning_status is PROVISIONING/"
            'DEPROVISIONING, not just the final status.'
        ),
    )
    render_backend_service_id = models.CharField(
        max_length=64, blank=True,
        help_text="Render service id (srv-…) of this tenant's backend web service — set by provisioning.",
    )
    render_frontend_service_id = models.CharField(
        max_length=64, blank=True,
        help_text="Render service id (srv-…) of this tenant's frontend static site — set by provisioning.",
    )
    backend_url = models.URLField(blank=True, help_text="This tenant's own backend API, once provisioned.")
    frontend_url = models.URLField(blank=True, help_text="This tenant's own frontend app, once provisioned.")
    provisioned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenant'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['domain'],
                condition=models.Q(domain__isnull=False) & ~models.Q(domain=''),
                name='unique_domain_when_set',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.slug})'
