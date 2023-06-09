import requests
from django.conf import settings
from django.utils import timezone
from django.db import models
from flutterwave.models import FWPayment


def get_fw_trans(trans_id):
    api_url = 'https://api.flutterwave.com/v3/transactions/{}/verify'.format(trans_id)
    headers = {
        "Authorization": "Bearer {}".format(settings.FLUTTERWAVE_SECRET_KEY),
        "Content-Type": "application/json",
    }
    try:
        response = requests.get(url=api_url, headers=headers)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as err:
        return None


def fw_payments_summary():
    now = timezone.now()
    this_month = now.replace(day=1)

    total_payments = FWPayment.objects.filter(data__isnull=False).aggregate(models.Sum('amount'))

    this_month_payments = FWPayment.objects.filter(
        data__isnull=False, created_at__year=this_month.year, created_at__month=this_month.month
    ).aggregate(models.Sum('amount'))

    payments_today = FWPayment.objects.filter(
        data__isnull=False, created_at__year=now.year, created_at__month=now.month, created_at__day=now.day
    ).aggregate(models.Sum('amount'))

    return {
        'total_payments': round(total_payments['amount__sum'], 2) if total_payments['amount__sum'] else 0,
        'payments_today': round(payments_today['amount__sum'], 2) if payments_today['amount__sum'] else 0,
        'this_month_payments': round(this_month_payments['amount__sum'], 2) if this_month_payments['amount__sum'] else 0,
        'payments_count': FWPayment.objects.filter(data__isnull=False).count(),
    }
