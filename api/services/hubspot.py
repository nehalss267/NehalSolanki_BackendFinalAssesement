import logging
import time

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_DEAL_PROPERTIES = [
    'dealname',
    'amount',
    'dealstage',
    'pipeline',
    'closedate',
    'dealtype',
    'description',
    'hubspot_owner_id',
    'createdate',
    'hs_lastmodifieddate',
]


class HubSpotError(Exception):
    pass


class InvalidTokenError(HubSpotError):
    pass


class RateLimitError(HubSpotError):
    pass


class HubSpotAPIError(HubSpotError):
    pass


class HubSpotDealsService:
    def __init__(self, access_token, base_url=None, timeout=None, max_retries=None, session=None):
        if not access_token:
            raise InvalidTokenError('Invalid API token provided')
        self.access_token = access_token
        self.base_url = (base_url or getattr(
            settings, 'HUBSPOT_API_BASE_URL', 'https://api.hubapi.com'
        )).rstrip('/')
        self.timeout = timeout or getattr(settings, 'HUBSPOT_API_TIMEOUT', 30)
        self.max_retries = (
            getattr(settings, 'HUBSPOT_MAX_RETRIES', 3)
            if max_retries is None
            else max_retries
        )
        self.session = session or requests.Session()

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

    def get_deals(self, limit=None, after=None, properties=None, archived=False):
        page_size = limit or getattr(settings, 'HUBSPOT_PAGE_SIZE', 100)
        params = {
            'limit': page_size,
            'archived': str(bool(archived)).lower(),
            'properties': ','.join(properties or DEFAULT_DEAL_PROPERTIES),
        }
        if after:
            params['after'] = after

        url = f'{self.base_url}/crm/v3/objects/deals'
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    url, headers=self.headers, params=params, timeout=self.timeout
                )
            except requests.RequestException as exc:
                last_error = exc
                logger.warning('HubSpot request failed (attempt %s): %s', attempt + 1, exc)
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 10))
                    continue
                raise HubSpotAPIError(f'HubSpot API is unreachable: {exc}') from exc

            if response.status_code in (401, 403):
                raise InvalidTokenError('Invalid API token provided')

            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '1')
                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    delay = 1.0
                last_error = RateLimitError('HubSpot rate limit exceeded')
                if attempt < self.max_retries:
                    logger.warning('HubSpot rate limit hit, retrying in %ss', delay)
                    time.sleep(delay)
                    continue
                raise RateLimitError('HubSpot rate limit exceeded') from last_error

            if response.status_code >= 400:
                message = response.text[:500]
                raise HubSpotAPIError(
                    f'HubSpot API error {response.status_code}: {message}'
                )

            return response.json()

    def validate_token(self):
        self.get_deals(limit=1)
        return True

    def iter_deals(self, limit=None, properties=None, archived=False):
        after = None
        while True:
            payload = self.get_deals(
                limit=limit, after=after, properties=properties, archived=archived
            )
            for deal in payload.get('results', []):
                yield deal

            after = (payload.get('paging') or {}).get('next', {}).get('after')
            if not after:
                break
