import requests
from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from utils.models import CurrencyRates


@db_periodic_task(crontab(hour='*/1', minute='0'))
def get_currency_rates_task():
    url = 'https://api.currencyapi.com/v3/latest?apikey={}&base_currency=KES'.format(settings.FREE_CURRENCY_API_KEY)
    try:
        response = requests.get(url)
        response.raise_for_status()

        r = response.json()

        CurrencyRates.objects.create(
            data=r
        )

        return 'Currency rates fetched and saved'

    except requests.exceptions.HTTPError as err:
        return 'Unable to fetch currency rates'
