from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/workflow/', include('apps.workflow.urls')),
    path('api/v1/core/', include('apps.core_hr.urls')),
    path('api/v1/recruitment/', include('apps.recruitment.urls')),
    path('api/v1/onboarding/', include('apps.onboarding.urls')),
    path('api/v1/workforce/', include('apps.workforce.urls')),
    path('api/v1/succession/', include('apps.succession.urls')),
    path('api/v1/performance/', include('apps.performance.urls')),
    path('api/v1/learning/', include('apps.learning.urls')),
    path('api/v1/notifications/', include('apps.notification.urls')),
    path('api/v1/reports/', include('apps.reporting.urls')),
    path('api/v1/attendance/', include('apps.attendance.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),

    # New modules
    path('api/v1/payroll/', include('apps.payroll.urls')),
    path('api/v1/compensation/', include('apps.compensation.urls')),
    path('api/v1/benefits/', include('apps.benefits.urls')),
    path('api/v1/ess/', include('apps.ess.urls')),
    path('api/v1/service-desk/', include('apps.service_desk.urls')),
    path('api/v1/er/', include('apps.employee_relations.urls')),
    path('api/v1/documents/', include('apps.documents.urls')),
    path('api/v1/offboarding/', include('apps.offboarding.urls')),
    path('api/v1/engagement/', include('apps.engagement.urls')),
    path('api/v1/hse/', include('apps.hse.urls')),
    path('api/v1/claims/', include('apps.claims.urls')),
    path('api/v1/skills/', include('apps.skills.urls')),

    # OpenAPI docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
