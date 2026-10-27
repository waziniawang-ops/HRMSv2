from django.conf import settings
from django.http import JsonResponse
from django.urls import Resolver404, resolve


class ModuleGateMiddleware:
    """Blocks any request to a plan-gated module this tenant's plan doesn't
    include, before it reaches the view at all.

    apps.accounts.permissions.IsModuleEnabled (in DEFAULT_PERMISSION_CLASSES)
    is NOT sufficient on its own: DRF's default permission classes only apply
    to a view that doesn't set its own `permission_classes`, and the vast
    majority of views in this codebase do (role checks like
    `permission_classes = [IsHRPerformance]`) — that assignment REPLACES the
    defaults rather than adding to them, so IsModuleEnabled would silently
    never run for almost any real endpoint. Middleware wraps the entire view
    dispatch, including its own permission_classes, and can't be bypassed
    that way. Kept IsModuleEnabled anyway as a harmless second layer for the
    few views that do rely on the defaults.

    A no-op whenever settings.ENABLED_MODULES is empty (the flagship
    single-tenant deployment, or local/dev)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.ENABLED_MODULES:
            module = self._module_label(request)
            if module is not None and module in settings.GATEABLE_MODULES and module not in settings.ENABLED_MODULES:
                return JsonResponse(
                    {'detail': "This module isn't included in your organization's plan."},
                    status=403,
                )
        return self.get_response(request)

    def _module_label(self, request):
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return None
        view_func = match.func
        # DRF's View.as_view()/ViewSet.as_view() both set `.cls` on the
        # returned function to the original view class — plain Django
        # function-based views (rare in this codebase) have neither.
        view_class = getattr(view_func, 'cls', None) or getattr(view_func, 'view_class', None)
        module_path = (view_class or view_func).__module__
        parts = module_path.split('.')
        return parts[1] if len(parts) >= 2 and parts[0] == 'apps' else None
