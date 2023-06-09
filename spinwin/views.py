import decimal
import json
import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import SafeString
from django.views.decorators.http import require_POST

from accounts.models import Income
from mpesa.utils import mpesa_stk_push
from spinwin.forms import TopUpSpinsForm
from spinwin.models import Segment, GivePool, SpinRecord
from spinwin.utils import change_spinwin_give_pool

UserModel = get_user_model()


@login_required
def index_view(request):
    segments_list = Segment.objects.order_by('win_amount')
    segments_options = []

    for segment in segments_list:
        segments_options.append(segment.options)

    context = {
        'segments_options':  SafeString(json.dumps(segments_options)),
        'min_top_up': settings.MIN_SPINWIN_TOP_UP,
        'paybill_number': settings.MPESA_C2B_SHORTCODE,
        'account_number': 'SW{}'.format(request.user.pk)
    }

    return render(request, 'spinwin/index.html', context)


@login_required
@require_POST
def top_up_spins_view(request):

    if not request.user.mpesa_number:
        messages.info(request, 'M-pesa number is required to top up spins.')
        return JsonResponse({'next_url': reverse('account_settings')}, status=400)

    form = TopUpSpinsForm(request.POST)

    if form.is_valid():

        amount = form.cleaned_data['amount']

        # Send m-pesa STK push
        stk_push = mpesa_stk_push(
            mpesa_number=int(request.user.mpesa_number.replace('+', '')),
            amount=amount,
            account_num='SW{}'.format(request.user.pk),
            description='Spins top up',
            callback_url="https://www.easyearn.co.ke{}".format(
                reverse('mpesa_callback', args=(settings.MPESA_SECRET,))
            )
        )

        if stk_push and stk_push['ResponseCode'] == '0':
            return HttpResponse(status=204)
        else:
            return HttpResponse(status=500)

    else:
        return JsonResponse({'errors': form.errors}, status=400)


@login_required
@require_POST
def spin_view(request):

    now = timezone.now()
    user = request.user

    if user.spinwin_bal < settings.SPINWIN_CHARGE:
        return JsonResponse({'message': 'less_spin_amount'}, status=400)

    # Check last spin
    last_spin = cache.get('last_spin_{}'.format(user.pk))

    if last_spin:
        spin_time_diff = (now - last_spin)
        seconds_diff = spin_time_diff.total_seconds()

        if seconds_diff < 10:
            # Spin too fast
            return JsonResponse({'message': 'spin_fast'}, status=400)

    # Set new last spin
    cache.set('last_spin_{}'.format(user.pk), now, 20)

    # Deduct SpinWin bal
    UserModel.objects.filter(pk=user.pk).update(spinwin_bal=F('spinwin_bal') - settings.SPINWIN_CHARGE)
    user.refresh_from_db()

    # Send 75% of spin charge to give pool
    to_give = decimal.Decimal(settings.SPINWIN_CHARGE * 75 / 100).quantize(
        decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN
    )
    change_spinwin_give_pool(amount=to_give)

    # Give pool
    give_pool = GivePool.objects.last()
    give_pool_bal = give_pool.amount

    segments = Segment.objects.order_by('win_amount')
    to_stop_segments = segments.filter(win_amount__lte=give_pool_bal)
    to_stop_weights = [x.winning_chance for x in to_stop_segments]

    stop_segment = random.choices(list(to_stop_segments), weights=to_stop_weights, k=1)

    # Create spin record
    spin_record = SpinRecord.objects.create(
        user=user, stop_segment=stop_segment[0],
    )

    context = {
        'stop_segment': list(segments).index(stop_segment[0]) + 1,
        'spinwin_bal': user.spinwin_bal,
        'acknowledge_url': reverse('spinwin_acknowledge', kwargs={'pk': spin_record.pk})
    }

    return JsonResponse(context, status=200)


@login_required
@require_POST
def acknowledge_spin_record(request, pk):
    spin_record = get_object_or_404(SpinRecord, pk=pk, user=request.user)

    # Prevent multiple acknowledge
    if spin_record.acknowledged:
        raise PermissionDenied

    award = spin_record.stop_segment.win_amount

    if award > 0:
        # Create income
        Income.objects.create(
            user=spin_record.user,
            amount=award,
            source='SP'
        )

    # Update spin record
    SpinRecord.objects.filter(pk=pk).update(
        acknowledged=True, award=award
    )

    return JsonResponse(data={'award': award}, status=200)
