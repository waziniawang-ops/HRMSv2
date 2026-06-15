from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.audit.mixins import AuditMixin

from apps.accounts.permissions import IsSystemAdmin, IsInternalUser
from .models import Notification, NotificationTemplate, NotificationPreference
from .serializers import NotificationSerializer, NotificationTemplateSerializer, NotificationPreferenceSerializer


class NotificationTemplateViewSet(AuditMixin, ModelViewSet):
    queryset = NotificationTemplate.objects.all().order_by('code')
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsSystemAdmin]
    filterset_fields = ['channel', 'is_active']


class NotificationViewSet(AuditMixin, ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsInternalUser]
    filterset_fields = ['channel', 'status']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        if notif.status in [Notification.STATUS_SENT, Notification.STATUS_PENDING]:
            notif.status = Notification.STATUS_READ
            notif.read_at = timezone.now()
            notif.save(update_fields=['status', 'read_at'])
        return Response(NotificationSerializer(notif).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(
            recipient=request.user,
            status__in=[Notification.STATUS_SENT, Notification.STATUS_PENDING],
        ).update(status=Notification.STATUS_READ, read_at=timezone.now())
        return Response({'detail': 'All notifications marked as read.'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            status__in=[Notification.STATUS_SENT, Notification.STATUS_PENDING],
        ).count()
        return Response({'unread_count': count})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsInternalUser]

    def get_object(self):
        pref, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return pref
