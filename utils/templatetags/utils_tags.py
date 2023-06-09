import math

from django import template

from django.conf import settings

from utils.models import CurrencyRates

register = template.Library()


@register.simple_tag()
def site_name():
    return settings.SITE_NAME


@register.simple_tag()
def activation_amount():
    return settings.ACTIVATION_AMOUNT


@register.simple_tag()
def referral_bonus():
    return settings.REFERRAL_BONUS


@register.simple_tag()
def min_withdrawal():
    return settings.MIN_WITHDRAWAL


@register.simple_tag()
def withdrawal_charge():
    return settings.WITHDRAWAL_CHARGE


@register.filter(name='get_kes_amount')
def get_kes_amount_tag(currency, other_amount):
    currency_rates = CurrencyRates.objects.last()
    if currency_rates:
        return math.ceil(currency_rates.get_kes_amount(currency, other_amount))
    else:
        return None


@register.filter(name='get_other_amount')
def get_other_amount_tag(currency, kes_amount):
    currency_rates = CurrencyRates.objects.last()
    if currency_rates:
        return math.ceil(currency_rates.get_other_amount(currency, kes_amount))
    else:
        return None
