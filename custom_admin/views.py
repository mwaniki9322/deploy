import datetime
import decimal

import pycountry
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.db.models import Sum
from accounts.models import Income, Withdrawal
from accounts.tasks import auto_disburse_withdrawal_task
from accounts.utils import users_summary, search_user, income_trend_chart_data, activate_user, income_trend_chart_data2
from custom_admin.forms import AdminWalletTopUpForm, AdminChangePasswordForm, AdminTopUpSpinsForm
from custom_admin.utils import withdrawals_summary
from flutterwave.models import FWPayment
from flutterwave.utils import fw_payments_summary
from mpesa.models import MpesaConfirmation, MpesaB2CResult
from mpesa.utils import mpesa_confirmations_summary, search_mpesa_confirmation, mpesa_b2c_results_summary, \
    search_mpesa_b2c_results
from tasks_feature.forms import TaskItemForm
from tasks_feature.models import TaskItem
from tasks_feature.utils import tasks_subscribe_user

UserModel = get_user_model()


def superuser_check(user):
    return user.is_superuser


@login_required
@user_passes_test(superuser_check)
def index_view(request):
    now = timezone.now()
    users_cash = UserModel.objects.aggregate(Sum('wallet_bal'))
    ready_to_withdraw = UserModel.objects.filter(wallet_bal__gte=500).aggregate(Sum('wallet_bal'))
    ready_to_withdraw = ready_to_withdraw['wallet_bal__sum'] if ready_to_withdraw['wallet_bal__sum'] else 0

    context = {
        'total_users': UserModel.objects.count(),
        'staff_users': UserModel.objects.filter(is_staff=True).count(),
        'joined_today': UserModel.objects.filter(
            date_joined__year=now.year, date_joined__month=now.month, date_joined__day=now.day
        ).count(),
        'income_trend_chart_data': income_trend_chart_data2(now),
        'users': UserModel.objects.order_by('-date_joined')[:4],
        'users_cash': users_cash['wallet_bal__sum'] if users_cash['wallet_bal__sum'] else decimal.Decimal('0.00'),
        'ready_to_withdraw': ready_to_withdraw,
    }
    return render(request, 'custom_admin/index.html', context)


@login_required
@user_passes_test(superuser_check)
def users_view(request):

    users_q = UserModel.objects.all()

    context = {
        'summary': users_summary()
    }

    query = request.GET.get('q')
    filter_q = request.GET.get('filter')

    if filter_q:
        user_type = filter_q.split('|')[0]
        from_date = filter_q.split('|')[1]
        to_date = filter_q.split('|')[2]

        if user_type:
            user_type_filter_choices = {
                'AC': users_q.filter(is_activated=True),
                'NA': users_q.filter(is_activated=False),
            }
            users_q = user_type_filter_choices[user_type]

            context['user_type'] = user_type

        if from_date:
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            users_q = users_q.filter(date_joined__gte=from_date)
            context['from_date'] = from_date.strftime('%Y-%m-%d %H:%M:%S')

        if to_date:
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            users_q = users_q.filter(date_joined__lte=to_date)
            context['to_date'] = to_date.strftime('%Y-%m-%d %H:%M:%S')

    if query:
        users_q = search_user(
            users_q, query
        ).order_by('-date_joined')
    else:
        users_q = users_q.order_by('-date_joined')

    paginator = Paginator(users_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    context['users'] = users

    return render(request, 'custom_admin/users.html', context)


@login_required
@user_passes_test(superuser_check)
def single_user_view(request, pk):
    user_obj = get_object_or_404(UserModel, pk=pk)
    tasks_packages = []

    for key, value in settings.TASKS_PACKAGES.items():
        value['name'] = key.title()
        value['code'] = key
        tasks_packages.append(value)

    context = {
        'income_trend_chart_data': income_trend_chart_data(user_obj),
        'referrals': UserModel.objects.filter(referrer=user_obj).order_by('-date_joined')[:4],
        'user': user_obj,
        'tasks_packages': tasks_packages
    }

    return render(request, 'custom_admin/single_user.html', context)


@login_required
@user_passes_test(superuser_check)
def user_earnings_view(request, pk):
    user_obj = get_object_or_404(UserModel, pk=pk)

    income_list = Income.objects.filter(user=user_obj).order_by('-created_at')
    paginator = Paginator(income_list, 10)  # Show 10 per page.
    page_number = request.GET.get('page')
    incomes = paginator.get_page(page_number)

    context = {
        'incomes': incomes
    }

    html = render_to_string('custom_admin/user_earnings.html', context)
    return HttpResponse(html)


@login_required
@user_passes_test(superuser_check)
def user_withdrawals_view(request, pk):
    user_obj = get_object_or_404(UserModel, pk=pk)

    withdrawals_list = Withdrawal.objects.filter(user=user_obj).order_by('-requested_at')
    paginator = Paginator(withdrawals_list, 10)  # Show 10 per page.
    page_number = request.GET.get('page')
    withdrawals = paginator.get_page(page_number)

    context = {
        'withdrawals': withdrawals
    }

    html = render_to_string('custom_admin/user_withdrawals.html', context)
    return HttpResponse(html)


@login_required
@user_passes_test(superuser_check)
def user_referrals_view(request, pk):
    user_obj = get_object_or_404(UserModel, pk=pk)

    now = timezone.now()
    referrals_q = UserModel.objects.filter(referrer=user_obj).order_by('-date_joined')
    referred_today = referrals_q.filter(
        date_joined__year=now.year, date_joined__month=now.month,
        date_joined__day=now.day
    ).count()

    paginator = Paginator(referrals_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    referrals = paginator.get_page(page_number)

    context = {
        'referred_today': referred_today,
        'activated': UserModel.objects.filter(referrer=user_obj, is_activated=True).count(),
        'referrals': referrals,
        'user': user_obj
    }

    return render(request, 'custom_admin/user_referrals.html', context)


@login_required
@user_passes_test(superuser_check)
@require_POST
def award_cash_view(request, pk):

    user = get_object_or_404(UserModel, pk=pk)

    form = AdminWalletTopUpForm(request.POST)

    if form.is_valid():

        amount = form.cleaned_data['amount']

        # Create income
        Income.objects.create(
            user=user,
            amount=amount,
            source='AW'
        )

        return HttpResponse(status=200)

    else:
        return JsonResponse({'errors': form.errors}, status=400)


@login_required
@user_passes_test(superuser_check)
@require_POST
def user_activation_view(request, pk):

    user = get_object_or_404(UserModel, pk=pk)

    if user.is_activated:
        # Deactivate user
        UserModel.objects.filter(pk=pk).update(
            is_activated=False
        )
        msg = '{} successfully deactivated.'.format(user.username)
    else:
        activate_user(user)
        msg = '{} successfully activated.'.format(user.username)

    messages.success(request, msg)

    return redirect('admin_single_user', pk)


@login_required
@user_passes_test(superuser_check)
@require_POST
def user_freezing_view(request, pk):
    user = get_object_or_404(UserModel, pk=pk)

    if user.is_active:
        user.is_active = False
        msg = '{} successfully frozen.'.format(user.username)
    else:
        user.is_active = True
        msg = '{} successfully unfrozen.'.format(user.username)

    user.save()

    messages.success(request, msg)

    return redirect('admin_single_user', pk)


@login_required
@user_passes_test(superuser_check)
@require_POST
def change_user_password_view(request, pk):
    user = get_object_or_404(UserModel, pk=pk)
    form = AdminChangePasswordForm(data=request.POST)
    if form.is_valid():
        user.set_password(form.cleaned_data['new_password1'])
        user.save()
        return HttpResponse(status=204)
    else:
        return JsonResponse({'errors': form.errors}, status=400)


@login_required
@user_passes_test(superuser_check)
@require_POST
def delete_user_view(request, pk):
    UserModel.objects.filter(pk=pk).delete()
    messages.success(request, 'Account successfully deleted.')
    return redirect('admin_users')


@login_required
@user_passes_test(superuser_check)
@require_POST
def spinwin_top_up_view(request, pk):
    user = get_object_or_404(UserModel, pk=pk)
    form = AdminTopUpSpinsForm(request.POST)

    if form.is_valid():
        amount = form.cleaned_data['amount']

        # Top up spins
        UserModel.objects.filter(pk=pk).update(spinwin_bal=F('spinwin_bal') + amount)

        return HttpResponse(status=204)

    else:
        return JsonResponse({'errors': form.errors}, status=400)


@login_required
@user_passes_test(superuser_check)
def mpesa_received_view(request):

    mpesa_confirmations_q = MpesaConfirmation.objects.all()

    context = {
        'summary': mpesa_confirmations_summary(),
    }

    query = request.GET.get('q')
    filter_q = request.GET.get('filter')

    if filter_q:
        from_date = filter_q.split('|')[0]
        to_date = filter_q.split('|')[1]

        if from_date:
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            mpesa_confirmations_q = mpesa_confirmations_q.filter(created_at__gte=from_date)
            context['from_date'] = from_date.strftime('%Y-%m-%d %H:%M:%S')

        if to_date:
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            mpesa_confirmations_q = mpesa_confirmations_q.filter(created_at__lte=to_date)
            context['to_date'] = to_date.strftime('%Y-%m-%d %H:%M:%S')

    if query:
        mpesa_confirmations_q = search_mpesa_confirmation(
            mpesa_confirmations_q, query
        ).order_by('-created_at')
    else:
        mpesa_confirmations_q = mpesa_confirmations_q.order_by('-created_at')

    paginator = Paginator(mpesa_confirmations_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    mpesa_confirmations = paginator.get_page(page_number)

    context['mpesa_confirmations'] = mpesa_confirmations

    return render(request, 'custom_admin/mpesa_received.html', context)


@login_required
@user_passes_test(superuser_check)
def mpesa_sent_view(request):

    mpesa_sent_q = MpesaB2CResult.objects.all()

    context = {
        'summary': mpesa_b2c_results_summary(),
    }

    query = request.GET.get('q')
    filter_q = request.GET.get('filter')

    if filter_q:
        from_date = filter_q.split('|')[0]
        to_date = filter_q.split('|')[1]

        if from_date:
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            mpesa_sent_q = mpesa_sent_q.filter(created_at__gte=from_date)
            context['from_date'] = from_date.strftime('%Y-%m-%d %H:%M:%S')

        if to_date:
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            mpesa_sent_q = mpesa_sent_q.filter(created_at__lte=to_date)
            context['to_date'] = to_date.strftime('%Y-%m-%d %H:%M:%S')

    if query:
        mpesa_sent_q = search_mpesa_b2c_results(
            mpesa_sent_q, query
        ).order_by('-created_at')
    else:
        mpesa_sent_q = mpesa_sent_q.order_by('-created_at')

    paginator = Paginator(mpesa_sent_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    mpesa_sent = paginator.get_page(page_number)

    context['mpesa_sent'] = mpesa_sent

    return render(request, 'custom_admin/mpesa_sent.html', context)


@login_required
@user_passes_test(superuser_check)
def withdrawals_view(request):

    query = request.GET.get('q')
    filter_q = request.GET.get('filter')

    if filter_q:
        country = filter_q.split('|')[2]
    else:
        country = 'KE'

    context = {
        'summary': withdrawals_summary(),
        'country': country,
        'countries': list(pycountry.countries),
    }

    withdrawals_q = Withdrawal.objects.filter(user__country=country)

    if filter_q:
        from_date = filter_q.split('|')[0]
        to_date = filter_q.split('|')[1]

        if from_date:
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            withdrawals_q = withdrawals_q.filter(requested_at__gte=from_date)
            context['from_date'] = from_date.strftime('%Y-%m-%d %H:%M:%S')

        if to_date:
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            withdrawals_q = withdrawals_q.filter(requested_at__lte=to_date)
            context['to_date'] = to_date.strftime('%Y-%m-%d %H:%M:%S')

    if query:
        lookups = Q(user__username__icontains=query) | Q(user__mpesa_number__icontains=query)
        withdrawals_q = withdrawals_q.filter(lookups).distinct().order_by('-requested_at')
    else:
        withdrawals_q = withdrawals_q.order_by('-requested_at')

    paginator = Paginator(withdrawals_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    withdrawals = paginator.get_page(page_number)

    context['withdrawals'] = withdrawals

    return render(request, 'custom_admin/withdrawals.html', context)


@login_required
@user_passes_test(superuser_check)
@require_POST
def cancel_withdrawal_view(request):

    withdrawal = get_object_or_404(
        Withdrawal, pk=request.POST['withdrawal'], is_disbursed=False
    )

    # Update
    withdrawal.is_cancelled = True
    withdrawal.cancelled_at = timezone.now()
    withdrawal.save()

    msg = 'Withdrawal of Ksh. {} by {} has been cancelled.'.format(
        withdrawal.amount, withdrawal.user.username
    )

    # Send alert
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'admin_alert',
        {
            'type': 'send.alert',
            'alert': {
                'message': 'withdrawal_alert',
                'status': 'cancelled',
                'id': request.POST['withdrawal'],
                'msg': msg,
            },
        }
    )

    return HttpResponse(status=204)


@login_required
@user_passes_test(superuser_check)
@require_POST
def disburse_withdrawal_view(request):

    withdrawal = get_object_or_404(
        Withdrawal, pk=request.POST['withdrawal'], is_cancelled=False
    )

    # Update
    withdrawal.is_disbursed = True
    withdrawal.disbursed_at = timezone.now()
    withdrawal.save()

    msg = 'Withdrawal of Ksh. {} by {} has been disbursed.'.format(
        withdrawal.amount, withdrawal.user.username
    )

    # Send alert
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'admin_alert',
        {
            'type': 'send.alert',
            'alert': {
                'message': 'withdrawal_alert',
                'status': 'disbursed',
                'id': request.POST['withdrawal'],
                'msg': msg,
            },
        }
    )

    return HttpResponse(status=204)


@login_required
@user_passes_test(superuser_check)
@require_POST
def auto_disburse_withdrawal_view(request):

    withdrawal = get_object_or_404(
        Withdrawal, pk=request.POST['withdrawal'], is_cancelled=False,
        user__mpesa_number__isnull=False
    )

    if withdrawal.user.mpesa_number:
        # Auto disburse in the background with celery
        auto_disburse_withdrawal_task.apply_async((withdrawal.pk,), )

    msg = 'Withdrawal of Ksh. {} by {} is being disbursed. Please wait.'.format(
        withdrawal.amount, withdrawal.user.username
    )
    return JsonResponse({'message': msg}, status=200)


@login_required
@user_passes_test(superuser_check)
def tasks_view(request):
    items_q = TaskItem.objects.all()
    query = request.GET.get('q')

    if query and query.isdigit():
        # Search by index
        items_q = items_q.filter(index=query)

    items_q = items_q.order_by('id')
    paginator = Paginator(items_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    items = paginator.get_page(page_number)

    ready_to_redeem = UserModel.objects.filter(
        tasks_wallet__gte=settings.MIN_TASKS_WALLET_TRANSFER
    ).aggregate(Sum('tasks_wallet'))
    tasks_wallets = UserModel.objects.aggregate(Sum('tasks_wallet'))

    context = {
        'items': items,
        'ready_to_redeem': ready_to_redeem['tasks_wallet__sum'] if ready_to_redeem['tasks_wallet__sum'] else 0,
        'tasks_wallets': tasks_wallets['tasks_wallet__sum'] if tasks_wallets['tasks_wallet__sum'] else 0,
    }

    return render(request, 'custom_admin/tasks.html', context)


class NewTaskView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_superuser

    template_name = 'custom_admin/new_task.html'

    def get(self, request):
        return render(self.request, self.template_name)

    def post(self, request):
        form = TaskItemForm(data=self.request.POST)

        if form.is_valid():
            form.save()
            return HttpResponse(status=200)
        else:
            return JsonResponse(data={'errors': form.errors}, status=400)


class EditTaskView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return self.request.user.is_superuser

    template_name = 'custom_admin/edit_task.html'

    def get(self, request, pk):
        task_item = get_object_or_404(TaskItem, pk=pk)
        context = {
            'item': task_item
        }
        return render(self.request, self.template_name, context)

    def post(self, request, pk):
        task_item = get_object_or_404(TaskItem, pk=pk)
        form = TaskItemForm(data=self.request.POST, instance=task_item)

        if form.is_valid():
            form.save()
            messages.success(self.request, 'Task updated.')
            return HttpResponse(status=200)
        else:
            return JsonResponse(data={'errors': form.errors}, status=400)


@login_required
@user_passes_test(superuser_check)
@require_POST
def delete_task_view(request):
    TaskItem.objects.filter(pk=request.POST['id']).delete()
    messages.success(request, 'Task deleted')
    return HttpResponse(status=200)


@login_required
@user_passes_test(superuser_check)
@require_POST
def tasks_user_subscribing_view(request):
    user = get_object_or_404(UserModel, pk=request.POST['user'])
    package = request.POST.get('package')

    if user.tasks_package:
        # Unsubscribe
        user.tasks_package = None
        user.tasks_package_expire = None
        user.save()

        msg = 'User successfully unsubscribed from tasks.'
    else:
        # Subscribe
        tasks_subscribe_user(user=user, package=package)

        msg = 'User successfully subscribed to tasks.'

    messages.success(request, msg)
    return redirect('admin_single_user', user.pk)


@login_required
@user_passes_test(superuser_check)
def fw_payments_view(request):
    payments_q = FWPayment.objects.filter(data__isnull=False)

    context = {
        'summary': fw_payments_summary(),
    }

    query = request.GET.get('q')
    filter_q = request.GET.get('filter')

    if filter_q:
        from_date = filter_q.split('|')[0]
        to_date = filter_q.split('|')[1]

        if from_date:
            from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            payments_q = payments_q.filter(created_at__gte=from_date)
            context['from_date'] = from_date.strftime('%Y-%m-%d %H:%M:%S')

        if to_date:
            to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d %H:%M').replace(tzinfo=datetime.timezone.utc)
            payments_q = payments_q.filter(created_at__lte=to_date)
            context['to_date'] = to_date.strftime('%Y-%m-%d %H:%M:%S')

    if query:
        lookups = Q(data__data__id__icontains=query) | Q(data__data__customer__email__icontains=query)
        payments_q = payments_q.filter(lookups).distinct().order_by('-created_at')
    else:
        payments_q = payments_q.order_by('-created_at')

    paginator = Paginator(payments_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    payments = paginator.get_page(page_number)

    context['payments'] = payments

    return render(request, 'custom_admin/fw_payments.html', context)
