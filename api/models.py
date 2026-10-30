import uuid

from django.db import models


class ExtractionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=50, default='hubspot')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    token_fingerprint = models.CharField(max_length=64, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    record_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.job_id} ({self.status})'


class ExtractedRecord(models.Model):
    job = models.ForeignKey(ExtractionJob, related_name='records', on_delete=models.CASCADE)
    source_id = models.CharField(max_length=128)
    data = models.JSONField()
    extracted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['job', 'source_id'], name='unique_job_source_record'),
        ]

    def __str__(self):
        return f'{self.job_id}:{self.source_id}'
