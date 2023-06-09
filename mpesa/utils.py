import base64
import decimal

import requests
from django.conf import settings
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from django.db.models import Sum, Q

from mpesa.models import MpesaConfirmation, MpesaB2CResult


def mpesa_c2b_access_token():
    url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(
                settings.MPESA_C2B_CONSUMER_KEY,
                settings.MPESA_C2B_CONSUMER_SECRET
            )
        )
        response.raise_for_status()

        r = response.json()

        return r.get('access_token')

    except requests.exceptions.HTTPError as err:
        return None


def lipa_na_mpesa_password(current_time):
    data_to_encode = settings.MPESA_C2B_SHORTCODE + settings.LIPA_NA_MPESA_PASSKEY + current_time
    online_password = base64.b64encode(data_to_encode.encode())
    return online_password.decode('utf-8')


def mpesa_stk_push(mpesa_number, amount, account_num, description, callback_url):
    access_token = mpesa_c2b_access_token()

    if not access_token:
        # There was an error with access token
        return None

    current_time = timezone.now().strftime('%Y%m%d%H%M%S')
    password = lipa_na_mpesa_password(current_time)

    api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": "Bearer %s" % access_token}
    request = {
        "BusinessShortCode": settings.MPESA_C2B_SHORTCODE,
        "Password": password,
        "Timestamp": current_time,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": mpesa_number,
        "PartyB": settings.MPESA_C2B_SHORTCODE,
        "PhoneNumber": mpesa_number,
        "CallBackURL": callback_url,
        "AccountReference": account_num,
        "TransactionDesc": description
    }

    try:
        response = requests.post(api_url, json=request, headers=headers)
        response.raise_for_status()

        r = response.json()

        return r

    except requests.exceptions.HTTPError as err:
        return None


def get_mpesa_b2c_access_token():
    url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(url, auth=HTTPBasicAuth(
        settings.MPESA_B2C_CONSUMER_KEY, settings.MPESA_B2C_CONSUMER_SECRET
    )).json()

    return r['access_token']


def mpesa_b2c_request(data):
    access_token = get_mpesa_b2c_access_token()
    api_url = "https://api.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"
    headers = {"Authorization": "Bearer %s" % access_token}
    request = {
        "InitiatorName": settings.MPESA_B2C_INITIATOR_NAME,
        "SecurityCredential": settings.MPESA_B2C_INITIATOR_CREDENTIAL,
        "CommandID": "BusinessPayment",
        "Amount": data['amount'],
        "PartyA": settings.MPESA_B2C_SHORTCODE,
        "PartyB": data['mpesa_number'],
        "Remarks": "Income withdrawal",
        "QueueTimeOutURL": data['queue_timeout_url'],
        "ResultURL": data['result_url'],
        "Occasion": data['occasion']
    }

    # Send request.
    try:

        response = requests.post(api_url, json=request, headers=headers)
        response.raise_for_status()

        data = response.json()

        if data['ResponseCode'] == '0':
            return True
        else:
            return False

    except requests.exceptions.HTTPError as err:
        return False


def extract_mpesa_confirmation(pk, data):
    MpesaConfirmation.objects.filter(pk=pk).update(
        transaction_id=data['TransID'],
        account_number=data['BillRefNumber'],
        amount=decimal.Decimal(data['TransAmount']),
        phone_number=data['MSISDN'],
        organisation_bal=decimal.Decimal(data['OrgAccountBalance']),
        first_name=data['FirstName'],
        middle_name=data['MiddleName'],
        last_name=data['LastName'],
        is_extracted=True
    )


def mpesa_confirmations_summary():
    now = timezone.now()
    this_month = now.replace(day=1)

    total_received = MpesaConfirmation.objects.aggregate(Sum('amount'))
    total_received = total_received['amount__sum'] if total_received['amount__sum'] else decimal.Decimal('0.00')

    processed = MpesaConfirmation.objects.filter(is_processed=True).aggregate(Sum('amount'))
    processed = processed['amount__sum'] if processed['amount__sum'] else decimal.Decimal('0.00')

    this_month_received = MpesaConfirmation.objects.filter(
        created_at__year=this_month.year, created_at__month=this_month.month
    ).aggregate(Sum('amount'))
    this_month_received = this_month_received['amount__sum'] if this_month_received['amount__sum'] else \
        decimal.Decimal('0.00')

    received_today = MpesaConfirmation.objects.filter(
        created_at__year=now.year, created_at__month=now.month, created_at__day=now.day
    ).aggregate(Sum('amount'))
    received_today = received_today['amount__sum'] if received_today['amount__sum'] else decimal.Decimal('0.00')

    # Breakdown
    accounts_activation = MpesaConfirmation.objects.filter(
        account_number__istartswith='AA'
    ).aggregate(Sum('amount'))
    accounts_activation = accounts_activation['amount__sum'] if accounts_activation['amount__sum'] else \
        decimal.Decimal('0.00')

    spin = MpesaConfirmation.objects.filter(
        account_number__istartswith='SW'
    ).aggregate(Sum('amount'))
    spin = spin['amount__sum'] if spin['amount__sum'] else decimal.Decimal('0.00')

    return {
        'total_received': total_received,
        'processed': processed,
        'this_month_received': this_month_received,
        'received_today': received_today,
        'breakdown': {
            'accounts_activation': {
                'amount': accounts_activation,
                'percentage': round((accounts_activation / total_received) * 100, 2) if total_received > 0 else '0.00'
            },
            'spin': {
                'amount': spin,
                'percentage': round((spin / total_received) * 100, 2) if total_received > 0 else '0.00'
            },
        }
    }


def search_mpesa_confirmation(confirmations_q, query):
    lookups = Q(data__TransID__icontains=query) | Q(data__BillRefNumber__icontains=query) | \
              Q(data__MSISDN__icontains=query)
    return confirmations_q.filter(lookups).distinct()


def search_mpesa_b2c_results(b2c_results_q, query):
    lookups = Q(data__Result__TransactionID__icontains=query) | \
              Q(data__Result__ResultParameters__ResultParameter__2__Value__icontains=query)
    return b2c_results_q.filter(lookups).distinct()


def mpesa_b2c_results_summary():
    now = timezone.now()
    this_month = now.replace(day=1)
    total_sent = decimal.Decimal('0.00')
    sent_today = decimal.Decimal('0.00')
    this_month_sent = decimal.Decimal('0.00')

    b2c_results = MpesaB2CResult.objects.all()

    for result in b2c_results:
        total_sent += result.get_amount()

        if result.created_at.year == this_month.year and result.created_at.month == this_month.month:
            this_month_sent += result.get_amount()

        if result.created_at.year == now.year and result.created_at.month == now.month and \
                result.created_at.day == now.day:
            sent_today += result.get_amount()

    return {
        'total_sent': total_sent,
        'total_transactions': b2c_results.count(),
        'this_month_sent': this_month_sent,
        'sent_today': sent_today
    }
