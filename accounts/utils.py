import datetime
import decimal
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.safestring import SafeString

from accounts.models import Income, Withdrawal
from utils.misc import utc_local_eq
from utils.models import CurrencyRates

UserModel = get_user_model()


def activate_user(user):

    # If already activated
    if user.is_activated:
        return 'User {} already activated'.format(user.pk)

    # Activate user
    UserModel.objects.filter(pk=user.pk).update(
        is_activated=True
    )

    # Referral bonus
    if user.referrer:
        Income.objects.create(
            user=user.referrer,
            amount=settings.REFERRAL_BONUS,
            source='RB',
        )

    # Send alert to websocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'user_alert_{}'.format(user.id_2),
        {
            'type': 'send.alert',
            'alert': {
                'message': 'account_activated'
            },
        }
    )


def income_source_trend_chart_data(user, utc_time, lookups, source_name, currency):
    """Return income trend for particular source in 7 days"""
    data = []

    # Convert currency
    currency_rates = CurrencyRates.objects.last()

    for i in range(7):

        income = Income.objects.filter(
            user=user, created_at__year=utc_time.year,
            created_at__month=utc_time.month,
            created_at__day=utc_time.day,
        ).filter(lookups).aggregate(Sum('amount'))

        income = round(income['amount__sum'], 2) if income['amount__sum'] else decimal.Decimal('0.00')
        income = currency_rates.get_other_amount(currency, income)
        data.append(float(income))

        # Previous day
        utc_time -= datetime.timedelta(days=1)

    return {'name': source_name, 'type': 'column', 'data': data[::-1]}


def income_trend_chart_data(user, currency='KES'):
    now = timezone.now()

    series = [
        income_source_trend_chart_data(
            user, now, Q(source='RB'), 'Referrals', currency
        ),
        income_source_trend_chart_data(
            user, now, Q(source='TS'), 'Tasks', currency
        ),
        income_source_trend_chart_data(
            user, now, Q(source='SP'), 'SpinWin', currency
        ),
        income_source_trend_chart_data(
            user, now, Q(source='AW'), 'Awards', currency
        )
    ]

    labels = []
    for i in range(7):
        local_time = utc_local_eq(now)
        labels.append(local_time.strftime('%b %d'))
        now -= datetime.timedelta(days=1)

    return SafeString(json.dumps({'labels': labels[::-1], 'series': series}))


def income_trend_chart_data2(now):
    data = []

    for i in range(7):
        income = Income.objects.filter(
            created_at__year=now.year,
            created_at__month=now.month,
            created_at__day=now.day,
        ).aggregate(Sum('amount'))

        income = round(income['amount__sum'], 2) if income['amount__sum'] else decimal.Decimal('0.00')

        local_time = utc_local_eq(now)
        data.append({'x': local_time.strftime('%b %d'), 'y': float(income)})

        # Previous day
        now -= datetime.timedelta(days=1)

    return SafeString(json.dumps(data[::-1]))


def users_summary():
    now = timezone.now()
    this_month = now.replace(day=1)

    total_users = UserModel.objects.count()

    # Users cash = total main bal + pending withdrawals
    users_cash = UserModel.objects.aggregate(Sum('wallet_bal'))
    users_cash = users_cash['wallet_bal__sum'] if users_cash['wallet_bal__sum'] else decimal.Decimal('0.00')
    pending_withdrawals = Withdrawal.objects.filter(is_disbursed=False, is_cancelled=False).aggregate(
        Sum('amount')
    )
    pending_withdrawals = pending_withdrawals['amount__sum'] if pending_withdrawals['amount__sum'] else \
        decimal.Decimal('0.00')
    users_cash = users_cash + pending_withdrawals

    activated = UserModel.objects.filter(is_activated=True).count()

    joined_this_month = UserModel.objects.filter(
        date_joined__year=this_month.year, date_joined__month=this_month.month
    ).count()

    joined_today = UserModel.objects.filter(
        date_joined__year=now.year, date_joined__month=now.month, date_joined__day=now.day
    ).count()

    return {
        'total_users': total_users,
        'users_cash': round(users_cash, 2),
        'activated': activated,
        'joined_this_month': joined_this_month,
        'joined_today': joined_today,
    }


def search_user(users_q, query):
    lookups = Q(username__icontains=query) | Q(first_name__icontains=query) | \
              Q(last_name__icontains=query) | Q(email__icontains=query) | \
              Q(mpesa_number__icontains=query)
    return users_q.filter(lookups).distinct()
