from accounts.models import Withdrawal
from django.utils import timezone
from django.db import models
import decimal
from django.contrib.auth import get_user_model

UserModel = get_user_model()


def withdrawals_summary():
    now = timezone.now()
    this_month = now.replace(day=1)

    withdrawals = Withdrawal.objects.all()

    total = withdrawals.aggregate(models.Sum('amount'))

    disbursed = withdrawals.filter(is_disbursed=True).aggregate(models.Sum('amount'))

    pending = withdrawals.filter(
        is_disbursed=False, is_cancelled=False
    ).aggregate(models.Sum('amount'))

    this_month = withdrawals.filter(
        requested_at__year=this_month.year, requested_at__month=this_month.month
    ).aggregate(models.Sum('amount'))

    today = withdrawals.filter(
        requested_at__year=now.year, requested_at__month=now.month, requested_at__day=now.day,
    ).aggregate(models.Sum('amount'))

    return {
        'total': total['amount__sum'] if total['amount__sum'] else decimal.Decimal('0.00'),
        'disbursed': disbursed['amount__sum'] if disbursed['amount__sum'] else decimal.Decimal('0.00'),
        'this_month': this_month['amount__sum'] if this_month['amount__sum'] else decimal.Decimal('0.00'),
        'today': today['amount__sum'] if today['amount__sum'] else decimal.Decimal('0.00'),
        'pending': pending['amount__sum'] if pending['amount__sum'] else decimal.Decimal('0.00')
    }
