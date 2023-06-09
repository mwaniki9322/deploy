from countryinfo import CountryInfo
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View

from accounts.models import Income
from mpesa.utils import mpesa_stk_push
from tasks_feature.forms import TaskSubscribeForm
from tasks_feature.models import TaskItem, TaskTaking
from tasks_feature.utils import user_tasks_summary, next_user_task, user_tasks_today


@login_required
def index_view(request):
    next_task = next_user_task(request.user)
    package_status = request.user.get_tasks_package_status()

    country = request.user.country
    currencies = CountryInfo(country).currencies()
    currency = currencies[0] if currencies else 'KES'

    context = {
        'summary': user_tasks_summary(request.user),
        'package_status': package_status,
        'next_task': next_task,
        'currency': currency
    }

    if package_status == 'active':
        context['income_per_task'] = settings.TASKS_PACKAGES[request.user.tasks_package]['income_per_task']

    return render(request, 'tasks_feature/index.html', context)


@login_required
def subscribe_start(request):
    if request.user.country == 'KE':
        return redirect('tasks_subscribe')
    else:
        return redirect('fw_tasks_subscribe')


class SubscribeView(LoginRequiredMixin, View):

    def get(self, request):
        packages = []

        for key, value in settings.TASKS_PACKAGES.items():
            value['name'] = key.title()
            value['code'] = key
            packages.append(value)

        context = {
            'packages': packages,
            'packages_dict': settings.TASKS_PACKAGES,
            'paybill_number': settings.MPESA_C2B_SHORTCODE,
            'account_number': 'TS{}'.format(self.request.user.pk)
        }

        return render(self.request, 'tasks_feature/subscribe.html', context)

    def post(self, request):
        form = TaskSubscribeForm(data=self.request.POST)

        if form.is_valid():
            package = form.cleaned_data['tasks_package']
            price = settings.TASKS_PACKAGES[package]['price']
            account_number = 'TS{}'.format(self.request.user.pk)

            # Send m-pesa STK push
            stk_push = mpesa_stk_push(
                mpesa_number=int(self.request.user.mpesa_number.replace('+', '')),
                amount=price,
                account_num=account_number,
                description='Ticket purchase',
                callback_url="https://www.easyearn.co.ke{}".format(
                    reverse('mpesa_callback', args=(settings.MPESA_SECRET,))
                )
            )

            if stk_push and stk_push['ResponseCode'] == '0':
                return HttpResponse(status=204)
            else:
                return HttpResponse(status=400)

        else:
            return JsonResponse(data={'errors': form.errors}, status=400)


class TakeTaskView(LoginRequiredMixin, View):

    def get(self, request, pk):

        if request.user.get_tasks_package_status() != 'active':
            # Not subscribed or package expired
            messages.info(self.request, 'Please subscribe or renew your tasks package.')
            return redirect('tasks_subscribe')

        task = get_object_or_404(TaskItem, pk=pk)

        if task != next_user_task(request.user):
            # Not the next task
            messages.info(self.request, 'Task not available for you.')
            return redirect('user_tasks')

        tasks_today = user_tasks_today(self.request.user)

        if tasks_today < settings.TASKS_PACKAGES[self.request.user.tasks_package]['tasks_per_day']:
            # Daily limit not reached
            TaskTaking.objects.get_or_create(
                task_item=task, user=self.request.user
            )

            context = {
                'task': task
            }

            return render(request, 'tasks_feature/take_task.html', context)

        else:
            # User has reached daily limit
            messages.info(self.request, 'Daily tasks limit reached. Take more tasks after 1 day.')
            return redirect('user_tasks')

    def post(self, request, pk):
        user = self.request.user
        task = get_object_or_404(TaskItem, pk=pk)
        task_taking = get_object_or_404(TaskTaking, task_item=task, user=user, finished=False)
        award = settings.TASKS_PACKAGES[user.tasks_package]['income_per_task']

        if task_taking.finish_time() > timezone.now():
            # Not yet finish time
            messages.info(self.request, 'Wait for 30 seconds before marking as finished.')
            return redirect('take_task', task.pk)

        # Top up tasks wallet
        user.tasks_wallet = F('tasks_wallet') + award
        user.save()

        # Mark finished
        task_taking.finished = True
        task_taking.save()

        messages.info(self.request, 'Ksh. {} earned for completing {}.'.format(award, task.__str__()))
        return redirect('user_tasks')


@login_required
def wallet_transfer_view(request):
    user = request.user
    tasks_bal = request.user.tasks_wallet

    if tasks_bal >= settings.MIN_TASKS_WALLET_TRANSFER:

        user.tasks_wallet = 0
        user.save()

        # Create income
        Income.objects.create(
            user=user, amount=tasks_bal,
            source='TS'
        )
        msg = 'Ksh. {} from your tasks wallet has been transferred to the main wallet.'.format(
            tasks_bal
        )

        messages.info(request, msg)

    else:
        msg = 'You need Ksh. {} in your tasks wallet to transfer.'.format(
            settings.MIN_TASKS_WALLET_TRANSFER
        )

        messages.info(request, msg)

    return redirect('user_tasks')
