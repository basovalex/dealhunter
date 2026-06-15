"""Thin wrapper around the IsThereAnyDeal API v2 (https://docs.isthereanydeal.com/).

Only handles request/response plumbing; no business logic and no
modification of the data it returns, per TZ.md section 7.
"""
import requests
from django.conf import settings

BASE_URL = 'https://api.isthereanydeal.com'
DEFAULT_COUNTRY = 'US'


class ITADError(Exception):
    pass


class ITADClient:
    def __init__(self, api_key=None, country=DEFAULT_COUNTRY):
        self.api_key = api_key or settings.ITAD_API_KEY
        if not self.api_key:
            raise ITADError('ITAD_API_KEY is not set. Add it to your .env file.')
        self.country = country
        self.session = requests.Session()

    def _get(self, path, params=None):
        params = dict(params or {})
        params['key'] = self.api_key
        response = self.session.get(f'{BASE_URL}{path}', params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def _post(self, path, json_body, params=None):
        params = dict(params or {})
        params['key'] = self.api_key
        response = self.session.post(f'{BASE_URL}{path}', params=params, json=json_body, timeout=15)
        response.raise_for_status()
        return response.json()

    def lookup_game(self, title=None, appid=None):
        """GET /games/lookup/v1 - resolve a title or Steam appid to an ITAD game id."""
        if not title and not appid:
            raise ValueError('lookup_game requires either title or appid')
        params = {'title': title} if title else {'appid': appid}
        return self._get('/games/lookup/v1', params)

    def get_shops(self, country=None):
        """GET /shops/v1 - active shops for a country."""
        return self._get('/shops/v1', {'country': country or self.country})

    def get_prices(self, game_ids, country=None, shops=None):
        """POST /games/prices/v3 - current prices for a list of ITAD game ids."""
        params = {'country': country or self.country}
        if shops:
            params['shops'] = ','.join(shops)
        return self._post('/games/prices/v3', list(game_ids), params)

    def get_historical_low(self, game_ids, country=None):
        """POST /games/historylow/v1 - historical low price for a list of ITAD game ids."""
        params = {'country': country or self.country}
        return self._post('/games/historylow/v1', list(game_ids), params)

    def get_history(self, game_id, country=None, shops=None, since=None):
        """GET /games/history/v2 - price history log for a single ITAD game id."""
        params = {'id': game_id, 'country': country or self.country}
        if shops:
            params['shops'] = ','.join(shops)
        if since:
            params['since'] = since
        return self._get('/games/history/v2', params)
