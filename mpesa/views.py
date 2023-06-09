import json

from django.conf import settings
from django.http import Http404
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Withdrawal
from .models import MpesaCallback, MpesaConfirmation, MpesaB2CResult


@csrf_exempt
def validation(request, mpesa_secret):

    if mpesa_secret == settings.MPESA_SECRET:

        context = {
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        }
        return JsonResponse(dict(context))

    else:
        raise Http404()


@csrf_exempt
def confirmation_view(request, mpesa_secret):

    if mpesa_secret == settings.MPESA_SECRET:

        request_body = request.body.decode('utf-8')
        request_data = json.loads(request_body)

        # Create confirmation
        confirmation = MpesaConfirmation(
            data=request_data
        )
        confirmation.save()

        context = {
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        }
        return JsonResponse(dict(context))

    else:
        raise Http404()


@csrf_exempt
def callback_view(request, mpesa_secret):

    if mpesa_secret == settings.MPESA_SECRET:

        request_body = request.body.decode('utf-8')
        request_data = json.loads(request_body)

        # Create callback
        callback = MpesaCallback(
            data=request_data
        )
        callback.save()

        return HttpResponse(status=204)

    else:
        raise Http404()


@csrf_exempt
def b2c_result_view(request, mpesa_secret, withdrawal_pk):

    if mpesa_secret == settings.MPESA_SECRET:

        withdrawal = get_object_or_404(Withdrawal, pk=withdrawal_pk)

        if not (withdrawal.is_disbursed or withdrawal.is_cancelled):
            request_body = request.body.decode('utf-8')
            request_data = json.loads(request_body)

            # Create mpesa b2c result
            b2c_result = MpesaB2CResult(
                data=request_data, withdrawal=withdrawal
            )
            b2c_result.save()

        return HttpResponse(status=204)

    else:
        return Http404()


@csrf_exempt
def b2c_queue_time_out_view(request, mpesa_secret, withdrawal_pk):

    if mpesa_secret == settings.MPESA_SECRET:

        withdrawal = get_object_or_404(Withdrawal, pk=withdrawal_pk)

        if not (withdrawal.is_disbursed or withdrawal.is_cancelled):
            # Do staff here
            pass

        return HttpResponse(status=204)

    else:
        return Http404()
