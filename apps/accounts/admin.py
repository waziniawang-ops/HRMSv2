from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, EmailVerificationToken, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'display_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code', 'display_name']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'get_all_roles', 'user_type', 'is_active']
    list_filter = ['role', 'user_type', 'is_active', 'is_email_verified']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    filter_horizontal = ['roles', 'groups', 'user_permissions']
    fieldsets = UserAdmin.fieldsets + (
        ('HRMS', {'fields': ('user_type', 'role', 'roles', 'phone', 'is_email_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('HRMS', {'fields': ('user_type', 'role', 'roles', 'phone')}),
    )

    @admin.display(description='All Roles')
    def get_all_roles(self, obj):
        return ', '.join(sorted(r.code for r in obj.roles.all())) or '—'


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used']
    raw_id_fields = ['user']
