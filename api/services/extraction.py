import hashlib
import logging
import threading

from django.db import close_old_connections
from django.utils import timezone

from ..models import ExtractedRecord, ExtractionJob
from .hubspot import DEFAULT_DEAL_PROPERTIES, HubSpotDealsService

logger = logging.getLogger(__name__)

SOURCE_FIELDS = ['createdAt', 'updatedAt', 'archived', 'archivedAt']


def token_fingerprint(access_token):
    return hashlib.sha256((access_token or '').encode('utf-8')).hexdigest()


def transform_deal(deal):
    properties = deal.get('properties') or {}
    data = {'id_from_service': str(deal.get('id', ''))}
    data.update(properties)
    for field in SOURCE_FIELDS:
        if field in deal and deal[field] is not None:
            data[field] = deal[field]
    return data


def run_extraction(job_id, access_token, properties=None, page_size=None, service_factory=None):
    close_old_connections()
    job = ExtractionJob.objects.filter(pk=job_id).first()
    if job is None or job.status == ExtractionJob.Status.CANCELLED:
        return

    job.status = ExtractionJob.Status.IN_PROGRESS
    job.started_at = job.started_at or timezone.now()
    job.save(update_fields=['status', 'started_at'])

    factory = service_factory or HubSpotDealsService

    try:
        service = factory(access_token)
        after = None
        total = 0

        while True:
            job.refresh_from_db(fields=['status'])
            if job.status == ExtractionJob.Status.CANCELLED:
                return

            payload = service.get_deals(
                limit=page_size,
                after=after,
                properties=properties or DEFAULT_DEAL_PROPERTIES,
            )
            results = payload.get('results', [])
            records = [
                ExtractedRecord(
                    job=job,
                    source_id=str(deal.get('id')),
                    data=transform_deal(deal),
                )
                for deal in results
                if deal.get('id') is not None
            ]
            if records:
                ExtractedRecord.objects.bulk_create(records, ignore_conflicts=True)
                total += len(records)

            after = (payload.get('paging') or {}).get('next', {}).get('after')
            if not after or not results:
                break

        job.refresh_from_db(fields=['status'])
        if job.status == ExtractionJob.Status.CANCELLED:
            return

        job.status = ExtractionJob.Status.COMPLETED
        job.record_count = ExtractedRecord.objects.filter(job=job).count()
        job.completed_at = timezone.now()
        job.error_message = ''
        job.save(update_fields=['status', 'record_count', 'completed_at', 'error_message'])
    except Exception as exc:
        logger.exception('Extraction failed for job %s', job_id)
        job.refresh_from_db(fields=['status'])
        if job.status == ExtractionJob.Status.CANCELLED:
            return
        job.status = ExtractionJob.Status.FAILED
        job.error_message = str(exc)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error_message', 'completed_at'])
    finally:
        close_old_connections()


def start_extraction_async(job_id, access_token, properties=None, page_size=None):
    thread = threading.Thread(
        target=run_extraction,
        args=(job_id, access_token),
        kwargs={'properties': properties, 'page_size': page_size},
        daemon=True,
    )
    thread.start()
    return thread
