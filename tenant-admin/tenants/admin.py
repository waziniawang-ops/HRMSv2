from django.contrib import admin
from django.utils.html import format_html

from .models import Tenant, Plan, Module

STATUS_COLORS = {
    Tenant.STATUS_PENDING: '#8F6110',
    Tenant.STATUS_ACTIVE: '#2B7252',
    Tenant.STATUS_SUSPENDED: '#B0453D',
    Tenant.STATUS_OFFBOARDED: '#6B7280',
}


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'domain_display', 'plan', 'status_badge', 'provisioning_status', 'admin_email', 'created_at')
    list_filter = ('status', 'provisioning_status', 'plan')
    search_fields = ('name', 'slug', 'domain', 'admin_email', 'admin_first_name', 'admin_last_name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'provisioning_status', 'provisioning_error', 'render_backend_service_id', 'render_frontend_service_id', 'backend_url', 'frontend_url', 'provisioned_at', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'plan', 'status')}),
        ('Deployment', {'fields': ('domain', 'provisioning_status', 'provisioning_error', 'render_backend_service_id', 'render_frontend_service_id', 'backend_url', 'frontend_url', 'provisioned_at'), 'description': 'Provisioning runs automatically when a tenant is created; these fields are set by that automation.'}),
        ('Admin user', {
            'fields': ('admin_first_name', 'admin_last_name', 'admin_email', 'admin_phone'),
            'description': "The tenant's primary admin — used to seed their first login when provisioning runs.",
        }),
        ('Notes', {'fields': ('notes',)}),
        ('Metadata', {'fields': ('id', 'created_at', 'updated_at')}),
    )

    @admin.display(description='Domain')
    def domain_display(self, obj):
        return obj.domain or '—'

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, '#6B7280')
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'monthly_price', 'seat_limit', 'module_count', 'tenant_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('modules',)
    readonly_fields = ('id', 'created_at', 'updated_at')

    @admin.display(description='Modules')
    def module_count(self, obj):
        return obj.modules.count()

    @admin.display(description='Tenants')
    def tenant_count(self, obj):
        return obj.tenants.count()


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code')


admin.site.site_header = 'Visionaries Tenant Admin'
admin.site.site_title = 'Tenant Admin'
admin.site.index_title = 'Tenants'
