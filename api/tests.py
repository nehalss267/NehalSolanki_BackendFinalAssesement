import os
import time
import uuid
from datetime import timedelta
from unittest import skipUnless
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from .models import ExtractedRecord, ExtractionJob
from .services import run_extraction, token_fingerprint
from .services.hubspot import (
    HubSpotAPIError,
    HubSpotDealsService,
    InvalidTokenError,
    RateLimitError,
)

VALID_TOKEN = 'pat-na1-' + ('a' * 40)
COMPLETED = ExtractionJob.Status.COMPLETED
PENDING = ExtractionJob.Status.PENDING
FAILED = ExtractionJob.Status.FAILED
CANCELLED = ExtractionJob.Status.CANCELLED
IN_PROGRESS = ExtractionJob.Status.IN_PROGRESS


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}
        self.text = str(self._payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({'url': url, 'headers': headers, 'params': params})
        return self.responses.pop(0)


class FailingService:
    def __init__(self, access_token):
        self.access_token = access_token

    def get_deals(self, **kwargs):
        raise HubSpotAPIError('HubSpot API is unreachable')


class APIDocumentationTests(TestCase):
    def test_swagger_ui_is_available(self):
        self.assertEqual(self.client.get('/docs/').status_code, 200)
        self.assertEqual(self.client.get('/swagger/').status_code, 200)

    def test_redoc_is_available(self):
        self.assertEqual(self.client.get('/redoc/').status_code, 200)

    def test_schema_is_available_as_json_and_yaml(self):
        json_response = self.client.get('/swagger.json')
        yaml_response = self.client.get('/swagger.yaml')

        self.assertEqual(json_response.status_code, 200)
        self.assertTrue(json_response['Content-Type'].startswith('application/json'))
        self.assertEqual(yaml_response.status_code, 200)
        self.assertTrue(yaml_response['Content-Type'].startswith('application/yaml'))


class SeededDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.pending_job = ExtractionJob.objects.create(status=PENDING)
        cls.completed_job = ExtractionJob.objects.create(
            status=COMPLETED,
            record_count=2,
            started_at=now - timedelta(seconds=10),
            completed_at=now - timedelta(seconds=4),
        )
        cls.cancelled_job = ExtractionJob.objects.create(
            status=CANCELLED,
            cancelled_at=now,
        )
        cls.failed_job = ExtractionJob.objects.create(
            status=FAILED,
            error_message='Upstream service unavailable',
            completed_at=now,
        )
        ExtractedRecord.objects.create(
            job=cls.completed_job,
            source_id='deal-1',
            data={'id_from_service': 'deal-1', 'dealname': 'First deal', 'amount': '5000'},
        )
        ExtractedRecord.objects.create(
            job=cls.completed_job,
            source_id='deal-2',
            data={'id_from_service': 'deal-2', 'dealname': 'Second deal', 'amount': '25000'},
        )

    def test_health_reports_ok(self):
        response = self.client.get('/api/v1/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_status_returns_seeded_state(self):
        response = self.client.get(f'/api/v1/scan/status/{self.pending_job.job_id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], PENDING)
        self.assertEqual(response.json()['record_count'], 0)
        self.assertIsNotNone(response.json()['created_at'])

    def test_result_returns_records_for_completed_job(self):
        response = self.client.get(f'/api/v1/scan/result/{self.completed_job.job_id}')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['count'], 2)
        self.assertEqual(len(body['results']), 2)
        self.assertEqual(body['results'][0]['data']['id_from_service'], 'deal-1')
        self.assertEqual(body['next_offset'], None)

    def test_result_supports_pagination(self):
        job = ExtractionJob.objects.create(status=COMPLETED, record_count=5)
        ExtractedRecord.objects.bulk_create([
            ExtractedRecord(job=job, source_id=f'deal-{index}', data={'id_from_service': index})
            for index in range(5)
        ])

        response = self.client.get(f'/api/v1/scan/result/{job.job_id}?limit=2&offset=1')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['count'], 5)
        self.assertEqual(len(body['results']), 2)
        self.assertEqual(body['next_offset'], 3)

    def test_jobs_list_contains_all_seeded_jobs(self):
        response = self.client.get('/api/v1/jobs/jobs')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['count'], 4)
        statuses = {job['status'] for job in body['results']}
        self.assertEqual(statuses, {PENDING, COMPLETED, CANCELLED, FAILED})

    def test_jobs_list_filters_by_status(self):
        response = self.client.get('/api/v1/jobs/jobs?status=cancelled')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['results'][0]['job_id'], str(self.cancelled_job.job_id))

    def test_statistics_reflect_seeded_data(self):
        response = self.client.get('/api/v1/jobs/statistics')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['total_jobs'], 4)
        self.assertEqual(body['completed_jobs'], 1)
        self.assertEqual(body['cancelled_jobs'], 1)
        self.assertEqual(body['failed_jobs'], 1)
        self.assertEqual(body['total_records'], 2)
        self.assertIsNotNone(body['average_extraction_time_seconds'])

    def test_cancel_pending_job(self):
        response = self.client.post(f'/api/v1/scan/cancel/{self.pending_job.job_id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], CANCELLED)
        self.pending_job.refresh_from_db()
        self.assertEqual(self.pending_job.status, CANCELLED)

        status_response = self.client.get(f'/api/v1/scan/status/{self.pending_job.job_id}')
        self.assertEqual(status_response.json()['status'], CANCELLED)

    def test_remove_job_deletes_extraction_data(self):
        response = self.client.delete(f'/api/v1/scan/remove/{self.completed_job.job_id}')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(ExtractionJob.objects.filter(pk=self.completed_job.job_id).exists())
        self.assertEqual(ExtractedRecord.objects.filter(job_id=self.completed_job.job_id).count(), 0)
        self.assertEqual(
            self.client.get(f'/api/v1/scan/status/{self.completed_job.job_id}').status_code,
            404,
        )
        self.assertEqual(
            self.client.get(f'/api/v1/scan/result/{self.completed_job.job_id}').status_code,
            404,
        )


class EdgeCaseTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.pending_job = ExtractionJob.objects.create(status=PENDING)
        self.in_progress_job = ExtractionJob.objects.create(status=IN_PROGRESS)
        self.completed_job = ExtractionJob.objects.create(
            status=COMPLETED,
            started_at=now,
            completed_at=now,
        )
        self.failed_job = ExtractionJob.objects.create(
            status=FAILED,
            error_message='Invalid API token provided',
        )

    def test_start_requires_token(self):
        response = self.client.post('/api/v1/scan/start', {}, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('api_token', response.json())

    def test_start_rejects_malformed_token(self):
        response = self.client.post(
            '/api/v1/scan/start',
            {'api_token': 'short'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('api_token', response.json())

    def test_start_rejects_malformed_json(self):
        response = self.client.post(
            '/api/v1/scan/start',
            data='{"api_token": ',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)

    def test_start_rejects_non_object_json_body(self):
        response = self.client.post(
            '/api/v1/scan/start',
            data='["not", "an", "object"]',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    @override_settings(HUBSPOT_VALIDATE_TOKEN_ON_START=True)
    @patch('api.views.HubSpotDealsService')
    def test_start_rejects_unauthorized_token(self, service_class):
        service_class.return_value.validate_token.side_effect = InvalidTokenError(
            'Invalid API token provided'
        )

        response = self.client.post(
            '/api/v1/scan/start',
            {'api_token': VALID_TOKEN},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid API token', response.json()['error'])

    @override_settings(HUBSPOT_VALIDATE_TOKEN_ON_START=True)
    @patch('api.views.HubSpotDealsService')
    def test_start_reports_upstream_validation_failure(self, service_class):
        service_class.return_value.validate_token.side_effect = HubSpotAPIError(
            'HubSpot API is unreachable'
        )

        response = self.client.post(
            '/api/v1/scan/start',
            {'api_token': VALID_TOKEN},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn('Unable to validate API token', response.json()['error'])

    @override_settings(HUBSPOT_VALIDATE_TOKEN_ON_START=False)
    @patch('api.views.start_extraction_async')
    def test_start_accepts_token_from_header_without_storing_it(self, start_async):
        response = self.client.post(
            '/api/v1/scan/start',
            {},
            content_type='application/json',
            HTTP_X_API_TOKEN=VALID_TOKEN,
        )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body['status'], PENDING)
        job = ExtractionJob.objects.get(pk=body['job_id'])
        self.assertEqual(job.token_fingerprint, token_fingerprint(VALID_TOKEN))
        self.assertNotIn(VALID_TOKEN, str(job.__dict__))
        start_async.assert_called_once()

    @override_settings(HUBSPOT_VALIDATE_TOKEN_ON_START=False)
    @patch('api.views.start_extraction_async')
    def test_duplicate_active_job_is_rejected(self, start_async):
        first = self.client.post(
            '/api/v1/scan/start',
            {'api_token': VALID_TOKEN},
            content_type='application/json',
        )
        second = self.client.post(
            '/api/v1/scan/start',
            {'api_token': VALID_TOKEN},
            content_type='application/json',
        )

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()['job_id'], first.json()['job_id'])
        self.assertEqual(ExtractionJob.objects.count(), 5)

    def test_non_existent_job_returns_404(self):
        missing_id = uuid.uuid4()

        self.assertEqual(self.client.get(f'/api/v1/scan/status/{missing_id}').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/scan/result/{missing_id}').status_code, 404)
        self.assertEqual(self.client.post(f'/api/v1/scan/cancel/{missing_id}').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/v1/scan/remove/{missing_id}').status_code, 404)

    def test_invalid_job_id_format_returns_404(self):
        response = self.client.get('/api/v1/scan/status/not-a-uuid')

        self.assertEqual(response.status_code, 404)

    def test_id_injection_attempt_returns_404(self):
        response = self.client.get('/api/v1/scan/status/1%20OR%201=1')

        self.assertEqual(response.status_code, 404)

    def test_result_for_incomplete_job_returns_conflict(self):
        for job in [self.pending_job, self.in_progress_job]:
            response = self.client.get(f'/api/v1/scan/result/{job.job_id}')

            self.assertEqual(response.status_code, 409)
            self.assertIn('not completed', response.json()['error'])
            self.assertEqual(response.json()['status'], job.status)

    def test_cancel_completed_or_failed_job_returns_conflict(self):
        for job in [self.completed_job, self.failed_job]:
            response = self.client.post(f'/api/v1/scan/cancel/{job.job_id}')

            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()['status'], job.status)
            self.assertIn('cannot be cancelled', response.json()['error'])

    def test_jobs_list_rejects_invalid_status_filter(self):
        response = self.client.get('/api/v1/jobs/jobs?status=unknown')

        self.assertEqual(response.status_code, 400)
        self.assertIn('status', response.json())

    def test_pagination_rejects_invalid_values(self):
        for query in ['limit=abc', 'limit=0', 'limit=501', 'offset=-1', 'offset=abc']:
            response = self.client.get(f'/api/v1/jobs/jobs?{query}')

            self.assertEqual(response.status_code, 400)
            self.assertIn('pagination', response.json())

    def test_large_result_set_paginates_consistently(self):
        job = ExtractionJob.objects.create(status=COMPLETED, record_count=250)
        ExtractedRecord.objects.bulk_create([
            ExtractedRecord(job=job, source_id=f'deal-{index}', data={'id_from_service': index})
            for index in range(250)
        ])

        seen = []
        offset = 0
        while True:
            response = self.client.get(
                f'/api/v1/scan/result/{job.job_id}?limit=100&offset={offset}'
            )
            self.assertEqual(response.status_code, 200)
            body = response.json()
            seen.extend(record['source_id'] for record in body['results'])
            if body['next_offset'] is None:
                break
            offset = body['next_offset']

        self.assertEqual(len(seen), 250)
        self.assertEqual(len(set(seen)), 250)
        self.assertEqual(seen[0], 'deal-0')
        self.assertEqual(seen[-1], 'deal-249')

    def test_extraction_failure_marks_job_failed(self):
        job = ExtractionJob.objects.create(status=PENDING)

        run_extraction(job.job_id, VALID_TOKEN, service_factory=FailingService)

        job.refresh_from_db()
        self.assertEqual(job.status, FAILED)
        self.assertIn('unreachable', job.error_message)
        self.assertIsNotNone(job.completed_at)

    @patch('api.services.hubspot.time.sleep')
    def test_rate_limit_is_retried(self, sleep):
        session = FakeSession([
            FakeResponse(429, headers={'Retry-After': '0'}),
            FakeResponse(200, {'results': [{'id': 'deal-1', 'properties': {}}]}),
        ])
        service = HubSpotDealsService(VALID_TOKEN, session=session)

        payload = service.get_deals(limit=1)

        self.assertEqual(payload['results'][0]['id'], 'deal-1')
        self.assertEqual(len(session.calls), 2)
        sleep.assert_called_once()

    @patch('api.services.hubspot.time.sleep')
    def test_rate_limit_raises_after_retries(self, sleep):
        session = FakeSession([
            FakeResponse(429, headers={'Retry-After': '0'}),
            FakeResponse(429, headers={'Retry-After': '0'}),
        ])
        service = HubSpotDealsService(VALID_TOKEN, session=session, max_retries=1)

        with self.assertRaises(RateLimitError):
            service.get_deals(limit=1)

    def test_invalid_token_response_raises(self):
        session = FakeSession([FakeResponse(401)])
        service = HubSpotDealsService(VALID_TOKEN, session=session)

        with self.assertRaises(InvalidTokenError):
            service.get_deals(limit=1)


@skipUnless(
    os.getenv('HUBSPOT_TEST_TOKEN'),
    'Set HUBSPOT_TEST_TOKEN to run live HubSpot extraction tests.',
)
class RealExtractionTests(TransactionTestCase):
    reset_sequences = True

    def test_real_extraction_pipeline(self):
        token = os.getenv('HUBSPOT_TEST_TOKEN')

        start_response = self.client.post(
            '/api/v1/scan/start',
            {'api_token': token, 'limit': 10},
            content_type='application/json',
        )
        self.assertEqual(start_response.status_code, 202)
        job_id = start_response.json()['job_id']

        deadline = time.time() + 60
        status_body = {}
        while time.time() < deadline:
            status_response = self.client.get(f'/api/v1/scan/status/{job_id}')
            status_body = status_response.json()
            if status_body['status'] in {COMPLETED, FAILED}:
                break
            time.sleep(2)

        self.assertEqual(status_body.get('status'), COMPLETED, status_body)

        result_response = self.client.get(f'/api/v1/scan/result/{job_id}?limit=10')
        self.assertEqual(result_response.status_code, 200)
        results = result_response.json()['results']
        self.assertGreaterEqual(len(results), 1)
        self.assertIn('id_from_service', results[0]['data'])

        remove_response = self.client.delete(f'/api/v1/scan/remove/{job_id}')
        self.assertEqual(remove_response.status_code, 204)
        self.assertEqual(self.client.get(f'/api/v1/scan/status/{job_id}').status_code, 404)
