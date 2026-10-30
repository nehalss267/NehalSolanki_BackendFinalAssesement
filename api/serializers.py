import re

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import ExtractedRecord, ExtractionJob

TOKEN_PATTERN = re.compile(r'^[A-Za-z0-9._-]{20,}$')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()


class ScanStartSerializer(serializers.Serializer):
    api_token = serializers.CharField(write_only=True, trim_whitespace=True)
    properties = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=False
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)
    archived = serializers.BooleanField(required=False, default=False)

    def validate_api_token(self, value):
        if not value or not TOKEN_PATTERN.match(value):
            raise serializers.ValidationError(
                'Invalid API token provided. Provide a valid private app access token.'
            )
        return value


class JobStatusSerializer(serializers.ModelSerializer):
    status = serializers.CharField()
    error_message = serializers.CharField(allow_blank=True)

    class Meta:
        model = ExtractionJob
        fields = [
            'job_id',
            'source',
            'status',
            'record_count',
            'error_message',
            'created_at',
            'started_at',
            'completed_at',
            'cancelled_at',
        ]


class ExtractedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedRecord
        fields = ['source_id', 'data', 'extracted_at']


class ExtractedResultSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    next_offset = serializers.IntegerField(allow_null=True)
    results = ExtractedRecordSerializer(many=True)


class JobSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractionJob
        fields = [
            'job_id',
            'source',
            'status',
            'record_count',
            'error_message',
            'created_at',
            'started_at',
            'completed_at',
            'cancelled_at',
        ]


class JobListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    next_offset = serializers.IntegerField(allow_null=True)
    results = JobSummarySerializer(many=True)


class JobStatisticsSerializer(serializers.Serializer):
    total_jobs = serializers.IntegerField()
    pending_jobs = serializers.IntegerField()
    in_progress_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    cancelled_jobs = serializers.IntegerField()
    total_records = serializers.IntegerField()
    average_extraction_time_seconds = serializers.FloatField(allow_null=True)


class ActionMessageSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()
    message = serializers.CharField()


class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
