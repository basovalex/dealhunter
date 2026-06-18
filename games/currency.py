"""Курс USD->RUB для отображения цен в рублях."""
from decimal import Decimal

import requests
from django.core.cache import cache

CBR_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
CACHE_KEY = 'usd_to_rub_rate'
CACHE_TTL = 6 * 60 * 60


def get_usd_to_rub_rate():
    rate = cache.get(CACHE_KEY)
    if rate is not None:
        return rate
    try:
        response = requests.get(CBR_URL, timeout=5)
        response.raise_for_status()
        rate = Decimal(str(response.json()['Valute']['USD']['Value']))
    except (requests.RequestException, KeyError, ValueError):
        return None
    cache.set(CACHE_KEY, rate, CACHE_TTL)
    return rate


def usd_to_rub(usd_amount):
    if usd_amount is None:
        return None
    rate = get_usd_to_rub_rate()
    if rate is None:
        return None
    return Decimal(str(usd_amount)) * rate
