import math

from countryinfo import CountryInfo
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from flutterwave.models import FWPayment
from flutterwave.tasks import process_fw_payment
from utils.models import CurrencyRates

redirect_urls = {
    'ACCOUNT_ACTIVATION': reverse_lazy('user_dashboard'),
    'BUY_SPINS': reverse_lazy('spinwin'),
    'TASKS_SUBSCRIBE': reverse_lazy('user_tasks'),
}


@csrf_exempt
def payment_redirect_view(request):
    payment = get_object_or_404(FWPayment, id_2=request.GET['tx_ref'])
    event = payment.event
    event['fw_trans_id'] = request.GET.get('transaction_id')

    payment.event = event
    payment.save()

    # Process in the background with Huey
    process_fw_payment(payment.pk)

    messages.info(request, 'Payment received. Just a moment as it gets processed.')

    if payment.event['intent'] in redirect_urls:
        next_url = redirect_urls[payment.event['intent']]
    else:
        next_url = reverse_lazy('user_dashboard')

    return redirect(next_url)


@login_required
def activate_view(request):
    if not request.user.phone_number or not request.user.email:
        messages.info(request, 'Phone number and email address is required to activate account.')
        return redirect('account_settings')

    country = request.user.country
    currencies = CountryInfo(country).currencies()
    currency_rates = CurrencyRates.objects.last()
    amount = settings.ACTIVATION_AMOUNT
    currency = 'KES'

    if country != 'KE' and currencies and currency_rates:
        currency = currencies[0]
        amount = math.ceil(currency_rates.get_other_amount(currency, amount))

    context = {
        'amount': amount,
        'currency': currency,
        'country': country
    }

    return render(request, 'flutterwave/activate.html', context)


@login_required
def buy_spins_view(request):
    if not request.user.phone_number or not request.user.email:
        messages.info(request, 'Phone number and email address is required to buy spins.')
        return redirect('account_settings')

    country = request.user.country
    currencies = CountryInfo(country).currencies()
    currency_rates = CurrencyRates.objects.last()

    if country != 'KE' and currencies and currency_rates:
        currency = currencies[0]
    else:
        currency = 'KES'

    min_top_up = math.ceil(currency_rates.get_other_amount(currency, settings.MIN_SPINWIN_TOP_UP))

    context = {
        'min_top_up': min_top_up,
        'currency': currency,
    }

    return render(request, 'flutterwave/buy_spins.html', context)


@login_required
def tasks_subscribe_view(request):
    if not request.user.phone_number or not request.user.email:
        messages.info(request, 'Phone number and email address required to subscribe to tasks.')
        return redirect('account_settings')

    country = request.user.country
    currencies = CountryInfo(country).currencies()
    currency_rates = CurrencyRates.objects.last()

    if country != 'KE' and currencies and currency_rates:
        currency = currencies[0]
    else:
        currency = 'KES'

    packages = []

    for key, value in settings.TASKS_PACKAGES.items():
        price = math.ceil(currency_rates.get_other_amount(currency, value['price']))
        packages.append({
            'name': key.title(), 'code': key, 'price': price
        })

    context = {
        'packages': packages,
        'currency': currency
    }

    return render(request, 'flutterwave/tasks_subscribe.html', context)


@login_required
@require_POST
def init_payment_view(request):

    intent = request.POST['intent']

    if intent not in ['ACCOUNT_ACTIVATION', 'BUY_SPINS', 'TASKS_SUBSCRIBE']:
        # Invalid intent
        return HttpResponse(status=400)

    currency_rates = CurrencyRates.objects.last()
    country = request.user.country
    currencies = CountryInfo(country).currencies()

    if country != 'KE' and currencies and currency_rates:
        currency = currencies[0]
    else:
        currency = 'KES'

    event = {
        'intent': intent,
        'user_id': request.user.pk,
        'phone_number': request.user.get_local_phone_number(),
        'currency': currency,
        'country': country,
        'email': request.user.email,
        'fw_trans_id': '',
    }

    if intent == 'ACCOUNT_ACTIVATION':
        # Account activation
        amount = math.ceil(currency_rates.get_other_amount(currency, settings.ACTIVATION_AMOUNT))
        event['amount'] = amount
        fw_payment = FWPayment.objects.create(event=event)

    elif intent == 'BUY_SPINS':
        # Buy spins
        amount = request.POST['amount']
        min_top_up = math.ceil(currency_rates.get_other_amount(currency, settings.MIN_SPINWIN_TOP_UP))

        if not amount.isdigit() or int(amount) < min_top_up:
            # Amount not digit or less than min top up
            return HttpResponse(status=400)

        event['amount'] = int(amount)
        fw_payment = FWPayment.objects.create(event=event)

    elif intent == 'TASKS_SUBSCRIBE':
        # Tasks subscribe
        package = request.POST['tasks_package']

        if package not in ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM']:
            # Invalid package
            return HttpResponse(status=400)

        price = math.ceil(currency_rates.get_other_amount(currency, settings.TASKS_PACKAGES[package]['price']))
        event['amount'] = price
        event['package'] = package
        fw_payment = FWPayment.objects.create(event=event)

    data = {
        'redirect_url': 'https://www.easyearn.co.ke{}'.format(reverse('fw_redirect')),
        'public_key': settings.FLUTTERWAVE_PUBLIC_KEY,
        'amount': event['amount'],
        'phone_number': event['phone_number'],
        'trans_id': fw_payment.id_2,
        'email': event['email'],
        'currency': event['currency'],
        'country': event['country'],
        'site_name': settings.SITE_NAME
    }

    return JsonResponse(data=data, status=200)
