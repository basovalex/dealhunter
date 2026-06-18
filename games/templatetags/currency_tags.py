from django import template

from ..currency import usd_to_rub

register = template.Library()


@register.filter
def to_rub(usd_amount):
    return usd_to_rub(usd_amount)
