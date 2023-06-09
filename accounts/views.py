import pycountry
from countryinfo import CountryInfo
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.views.decorators.http import require_POST

from accounts.forms import SignUpForm, PasswordResetForm, WithdrawalForm, ProfileDetailsForm, ProfilePicForm, \
    BillingDetailsForm
from accounts.models import Income, Withdrawal
from accounts.utils import income_trend_chart_data
from mpesa.utils import mpesa_stk_push
from utils.elphways import send_sms
from utils.models import CurrencyRates

UserModel = get_user_model()


@login_required
@require_POST
def change_utc_offset(request):
    """
    Change user's utc-offset. Used to localize time.
    """
    user = request.user
    user.utc_offset = request.POST['utc_offset']
    user.save()
    return HttpResponse(status=204)


class SignUpView(View):

    template_name = 'accounts/registration/signup.html'

    def get(self, request):

        initial_data = {'country': 'KE'}
        referral_code = self.request.GET.get('rc')

        # Check for referral code and make sure it exists
        if referral_code and UserModel.objects.filter(
                id_2=referral_code, is_active=True, is_activated=True
        ).exists():
            initial_data['referral_code'] = referral_code

        form = SignUpForm(initial=initial_data)

        context = {
            'countries': list(pycountry.countries),
            'form': form
        }

        return render(request, self.template_name, context)

    def post(self, request):
        form = SignUpForm(data=self.request.POST)

        if form.is_valid():

            user = form.new_user()
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(self.request, 'Account created successfully.')

            return redirect('activate_start')

        else:
            context = {
                'countries': list(pycountry.countries),
                'form': form
            }
            messages.error(self.request, 'Please confirm the details you provided then try again.')
            return render(request, self.template_name, context)


class PasswordResetView(View):
    template_name = 'accounts/password_reset/password_reset.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        form = PasswordResetForm(self.request.POST)

        if form.is_valid():

            user = form.get_user()
            current_site = get_current_site(self.request)

            password_reset_token = PasswordResetTokenGenerator()

            token = password_reset_token.make_token(user=user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            url_path = 'http://{}{}'.format(
                current_site.domain,
                reverse_lazy('password_reset_confirm', args=(uid, token,))
            )

            msg = 'Reset your account password here: {}. Your username in case you forgot is {}.'.format(
                url_path, user.username
            )

            sms_response = send_sms(msg, [user.mpesa_number])

            if sms_response['sent']:
                # SMS sent
                return redirect('password_reset_done')
            else:
                # SMS failed
                messages.error(self.request, 'An error has occurred. Please try again later.')

        return render(request, self.template_name, {'form': form})


@login_required
def activate_start(request):
    # If user is already activated
    if request.user.is_activated:
        messages.info(request, 'Your account is already activated.')
        return redirect('user_dashboard')

    if request.user.country == 'KE':
        return redirect('activate_account')
    else:
        return redirect('fw_activate')


class ActivateAccountView(LoginRequiredMixin, View):

    template_name = 'accounts/profile/activate_account.html'

    def get(self, request):

        # If account is already activated
        if self.request.user.is_activated:
            messages.info(self.request, 'Your account is already activated.')
            return redirect('user_dashboard')

        # If mpesa number is not set
        if not self.request.user.mpesa_number:
            messages.info(self.request, 'Kindly set up your Mpesa number to activate your account.')
            return redirect('account_settings')

        context = {
            'amount': settings.ACTIVATION_AMOUNT,
            'account_number': 'AA{}'.format(self.request.user.pk),
            'paybill_number': settings.MPESA_C2B_SHORTCODE,
        }

        return render(self.request, self.template_name, context)

    def post(self, request):
        # Send m-pesa STK push
        stk_push = mpesa_stk_push(
            mpesa_number=int(self.request.user.mpesa_number.replace('+', '')),
            amount=settings.ACTIVATION_AMOUNT,
            account_num='AA{}'.format(self.request.user.pk),
            description='Membership activation',
            callback_url="https://www.easyearn.co.ke{}".format(
                reverse('mpesa_callback', args=(settings.MPESA_SECRET,))
            )
        )

        if stk_push and stk_push['ResponseCode'] == '0':
            return HttpResponse(status=204)
        else:
            return HttpResponse(status=400)


@login_required
def dashboard_view(request):
    country = request.user.country
    currencies = CountryInfo(country).currencies()

    if country != 'KE' and currencies:
        currency = currencies[0]
    else:
        currency = 'KES'

    context = {
        'income_trend_chart_data': income_trend_chart_data(request.user, currency=currency),
        'referrals': UserModel.objects.filter(referrer=request.user).order_by('-date_joined')[:4],
        'currency': currency
    }
    return render(request, 'accounts/profile/dashboard.html', context)


@login_required
def referrals_view(request):
    now = timezone.now()
    referrals_q = UserModel.objects.filter(referrer=request.user).order_by('-date_joined')
    referred_today = referrals_q.filter(
        date_joined__year=now.year, date_joined__month=now.month,
        date_joined__day=now.day
    ).count()

    paginator = Paginator(referrals_q, 20)  # Show 20 per page.
    page_number = request.GET.get('page')
    referrals = paginator.get_page(page_number)

    context = {
        'referred_today': referred_today,
        'activated': UserModel.objects.filter(referrer=request.user, is_activated=True).count(),
        'referrals': referrals
    }

    return render(request, 'accounts/profile/referrals.html', context)


@login_required
def earnings_view(request):
    income_list = Income.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(income_list, 10)  # Show 10 per page.
    page_number = request.GET.get('page')
    incomes = paginator.get_page(page_number)

    country = request.user.country
    currencies = CountryInfo(country).currencies()
    currency_rates = CurrencyRates.objects.last()

    if country != 'KE' and currencies and currency_rates:
        currency = currencies[0]
    else:
        currency = 'KES'

    context = {
        'incomes': incomes, 'currency': currency
    }

    html = render_to_string('accounts/profile/earnings.html', context)
    return HttpResponse(html)


@login_required
def withdrawals_view(request):
    withdrawals_list = Withdrawal.objects.filter(user=request.user).order_by('-requested_at')
    paginator = Paginator(withdrawals_list, 10)  # Show 10 per page.
    page_number = request.GET.get('page')
    withdrawals = paginator.get_page(page_number)

    country = request.user.country
    currencies = CountryInfo(country).currencies()
    currency_rates = CurrencyRates.objects.last()

    if country != 'KE' and currencies and currency_rates:
        currency = currencies[0]
    else:
        currency = 'KES'

    context = {
        'withdrawals': withdrawals, 'currency': currency
    }

    html = render_to_string('accounts/profile/withdrawals.html', context)
    return HttpResponse(html)


@login_required
@require_POST
def withdraw_view(request):

    form = WithdrawalForm(data=request.POST)

    if form.is_valid():

        user = form.get_user()

        if user == request.user:

            net_amount = form.net_amount()
            gross_amount = form.gross_amount()

            withdrawal = form.save(commit=False)
            withdrawal.user = request.user
            withdrawal.amount = gross_amount
            withdrawal.net_amount = net_amount
            withdrawal.save()

            msg = 'Withdrawal request received and will be processed within 24 hours.'
            return JsonResponse({'message': msg}, status=200)

        else:
            raise PermissionDenied

    else:
        return JsonResponse({'errors': form.errors}, status=400)


class AccountSettingsView(LoginRequiredMixin, View):

    def get(self, request):
        context = {
            'countries': list(pycountry.countries)
        }
        return render(self.request, 'accounts/profile/settings.html', context)

    def post(self, request):
        form_class = self.request.POST['form_class']

        form_classes = {
            'profile_details': ProfileDetailsForm(instance=self.request.user, data=self.request.POST),
            'billing_details': BillingDetailsForm(instance=self.request.user, data=self.request.POST),
            'profile_pic': ProfilePicForm(instance=self.request.user, data=self.request.POST, files=self.request.FILES),
            'change_password': PasswordChangeForm(user=self.request.user, data=self.request.POST),
        }

        form = form_classes[form_class]

        if form.is_valid():

            # For billing details
            if form_class == 'billing_details':

                if form.cleaned_data['user_id'] != self.request.user.pk:
                    # User didn't match
                    raise PermissionDenied

                mpesa_number = form.parsed_mpesa()
                phone_number = form.parsed_phone()
                form = form.save(commit=False)
                form.mpesa_number = mpesa_number
                form.phone_number = phone_number

            # Save form
            form.save()

            # Update session if password is changed
            if form_class == 'change_password':
                update_session_auth_hash(request, form.user)

            data = {
                'pic_url': request.user.get_pic()
            }

            return JsonResponse(data=data, status=200)

        else:
            return JsonResponse({'errors': form.errors}, status=400)
