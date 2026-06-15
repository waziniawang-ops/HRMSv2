import json
from rest_framework.renderers import JSONRenderer
from .utils import log_action


def _to_json(data):
    if data is None:
        return None
    try:
        return json.loads(JSONRenderer().render(data).decode('utf-8'))
    except Exception:
        return None


class AuditMixin:
    """
    Drop-in mixin for ModelViewSet. Automatically writes an AuditLog entry
    for every CREATE, UPDATE, and DELETE that comes through the API.

    Hooks at the HTTP action level (create/update/destroy) so it fires
    regardless of custom perform_* overrides in subclasses.
    """

    def _audit_snapshot(self, instance):
        try:
            return _to_json(self.get_serializer(instance).data)
        except Exception:
            return {'pk': str(getattr(instance, 'pk', ''))}

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code < 300:
            model = self.get_serializer_class().Meta.model
            data = _to_json(response.data)
            obj_id = str(data.get('id', '')) if data else ''
            log_action(request, 'CREATE', model.__name__, obj_id,
                       after_json=data, module=model._meta.app_label)
        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        before = self._audit_snapshot(instance)
        obj_type = instance.__class__.__name__
        obj_id = str(instance.pk)
        module = instance._meta.app_label
        response = super().update(request, *args, **kwargs)
        if response.status_code < 300:
            log_action(request, 'UPDATE', obj_type, obj_id,
                       before_json=before, after_json=_to_json(response.data),
                       module=module)
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        before = self._audit_snapshot(instance)
        obj_type = instance.__class__.__name__
        obj_id = str(instance.pk)
        module = instance._meta.app_label
        response = super().destroy(request, *args, **kwargs)
        log_action(request, 'DELETE', obj_type, obj_id,
                   before_json=before, module=module)
        return response
