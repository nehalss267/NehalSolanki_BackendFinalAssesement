from django.contrib import admin

from .models import ExtractedRecord, ExtractionJob


@admin.register(ExtractionJob)
class ExtractionJobAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'source', 'status', 'record_count', 'created_at', 'completed_at']
    list_filter = ['source', 'status']
    search_fields = ['job_id']


@admin.register(ExtractedRecord)
class ExtractedRecordAdmin(admin.ModelAdmin):
    list_display = ['job', 'source_id', 'extracted_at']
    search_fields = ['source_id']
