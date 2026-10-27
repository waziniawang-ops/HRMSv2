from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse, HttpResponse, Http404
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from tenants.api import TenantViewSet, PlanViewSet, ModuleViewSet, LoginView, me


def healthz(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    return JsonResponse({'status': 'ok'})


def spa_index(request, *args, **kwargs):
    """Serves the built React app's index.html for any client-side route."""
    index_path = Path(settings.WHITENOISE_ROOT) / 'index.html'
    if not index_path.exists():
        raise Http404(
            'Frontend build not found — run `npm run build` in tenant-admin/frontend/ first.'
        )
    return HttpResponse(index_path.read_text(), content_type='text/html')


router = DefaultRouter()
router.register('tenants', TenantViewSet, basename='tenant')
router.register('plans', PlanViewSet, basename='plan')
router.register('modules', ModuleViewSet, basename='module')

urlpatterns = [
    path('healthz/', healthz, name='healthz'),
    path('admin/', admin.site.urls),
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('api/auth/me/', me, name='api-me'),
    path('api/', include(router.urls)),
    # SPA catch-all — must stay last. Anything not matched above (i.e. every
    # client-side route the React app owns: /, /tenants, /login, etc.) falls
    # through to index.html and React Router takes it from there.
    re_path(r'^(?!admin/|api/|healthz/|static/).*$', spa_index),
]
