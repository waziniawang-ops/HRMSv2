import math
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class FaceDescriptor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.OneToOneField(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='face_descriptor'
    )
    descriptor = models.JSONField()  # 128-element float list
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='enrolled_faces'
    )

    class Meta:
        db_table = 'attendance_face_descriptor'

    def __str__(self):
        return f"Face({self.employee})"

    @staticmethod
    def euclidean(a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    @classmethod
    def find_best_match(cls, descriptor, threshold=0.55):
        """Return (FaceDescriptor, distance) or (None, None) if no match below threshold."""
        best, best_dist = None, float('inf')
        for fd in cls.objects.select_related('employee__person').all():
            dist = cls.euclidean(descriptor, fd.descriptor)
            if dist < best_dist:
                best_dist = dist
                best = fd
        if best and best_dist <= threshold:
            return best, best_dist
        return None, None


class AttendanceRecord(models.Model):
    METHOD_FACE = 'FACE'
    METHOD_MANUAL = 'MANUAL'
    METHOD_CHOICES = [
        (METHOD_FACE, 'Face Recognition'),
        (METHOD_MANUAL, 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'core_hr.Employee', on_delete=models.CASCADE, related_name='attendance_records'
    )
    date = models.DateField(default=timezone.localdate)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default=METHOD_FACE)
    notes = models.TextField(blank=True)
    workflow_request = models.ForeignKey(
        'workflow.WorkflowRequest', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_record'
        ordering = ['-date', '-check_in']
        unique_together = ['employee', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['employee', 'date']),
        ]

    def __str__(self):
        return f"{self.employee} — {self.date}"

    @property
    def hours_worked(self):
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            return round(delta.total_seconds() / 3600, 2)
        return None
