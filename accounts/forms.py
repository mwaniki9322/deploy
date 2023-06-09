from countryinfo import CountryInfo
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from accounts.models import Withdrawal
from utils.files import crop_img, rename_model_file
from utils.misc import utc_to_local_time
from utils.models import CurrencyRates
from utils.phone_utils import validate_phone, validate_mpesa_number, parse_phone_number

UserModel = get_user_model()


class SignUpForm(forms.ModelForm):

    referral_code = forms.CharField(max_length=20, required=False)

    class Meta:
        model = UserModel
        fields = [
            'username', 'email', 'country', 'phone_number', 'mpesa_number', 'password', 'referral_code'
        ]

    def clean(self):
        cleaned_data = super().clean()
        referral_code = cleaned_data.get('referral_code')
        mpesa_number = cleaned_data.get('mpesa_number')
        phone_number = cleaned_data.get('phone_number')
        country = cleaned_data.get('country')

        # Check referral code
        if referral_code and not UserModel.objects.filter(
                id_2=referral_code, is_active=True, is_activated=True
        ).exists():
            self.add_error('referral_code', 'Referral code not found.')

        # Validate phone number
        parsed_phone = parse_phone_number(phone_string=phone_number, country_code=country)
        if parsed_phone:

            if UserModel.objects.filter(phone_number=parsed_phone).exists():
                # Phone number exists
                self.add_error('phone_number', 'Phone number already exists')

        else:
            self.add_error('phone_number', 'Please enter a valid phone number')

        # Validate mpesa number
        if country == 'KE':
            if mpesa_number:
                parsed_mpesa = parse_phone_number(phone_string=mpesa_number, country_code=country)

                if parsed_mpesa and validate_mpesa_number(parsed_mpesa):

                    if UserModel.objects.filter(mpesa_number=parsed_mpesa).exists():
                        # Mpesa number exists
                        self.add_error('mpesa_number', 'Phone number already exists')

                else:
                    self.add_error('mpesa_number', 'Please enter a valid mpesa number')

            else:
                # No mpesa number
                self.add_error('mpesa_number', 'Mpesa number required for users in Kenya')

    def new_user(self):
        cleaned_data = super().clean()
        mpesa_number = cleaned_data.get('mpesa_number')
        phone_number = cleaned_data.get('phone_number')
        referral_code = cleaned_data.get('referral_code')
        country = cleaned_data.get('country')

        if referral_code:
            referrer = UserModel.objects.get(id_2=referral_code)
        else:
            referrer = None

        parsed_mpesa = parse_phone_number(phone_string=mpesa_number, country_code=country) if country == 'KE' else None

        user = UserModel.objects.create_user(
            username=cleaned_data['username'],
            password=cleaned_data['password'],
            referrer=referrer,
            phone_number=parse_phone_number(phone_string=phone_number, country_code=country),
            mpesa_number=parsed_mpesa,
            country=country,
            email=cleaned_data.get('email'),
        )

        return user


class PasswordResetForm(forms.Form):
    mpesa_number = forms.CharField(max_length=50)

    def clean(self):
        cleaned_data = super().clean()
        mpesa_number = cleaned_data.get('mpesa_number')
        validated_mpesa = validate_phone('+254{}'.format(mpesa_number))

        if validated_mpesa:
            if not UserModel.objects.filter(mpesa_number=validated_mpesa).exists():
                self.add_error('mpesa_number', 'A user with this mpesa number does not exist.')
        else:
            self.add_error('mpesa_number', 'Please use 07xxxxxxxx format.')

    def get_user(self):
        cleaned_data = super().clean()
        mpesa_number = cleaned_data.get('mpesa_number')

        return UserModel.objects.get(
            mpesa_number=validate_phone('+254{}'.format(mpesa_number))
        )


class WithdrawalForm(forms.ModelForm):

    id_2 = forms.CharField(max_length=50)

    class Meta:
        model = Withdrawal
        fields = [
            'amount', 'id_2'
        ]

    def clean(self):
        cleaned_data = super(WithdrawalForm, self).clean()
        amount = cleaned_data.get('amount')
        id_2 = cleaned_data.get('id_2')

        user = UserModel.objects.filter(id_2=id_2).first()

        if user:
            if utc_to_local_time().weekday() not in [0, 4]:
                # Withdrawals restricted to only Monday and Friday
                raise forms.ValidationError('Withdrawals restricted to only Monday and Friday')

            # Block if user has pending withdrawal
            if Withdrawal.objects.filter(
                    user=user, is_disbursed=False, is_cancelled=False
            ).exists():
                msg = 'You have another pending withdrawal. Please wait for it to get disbursed.'
                raise forms.ValidationError(msg)

            if user.country != 'KE':
                # Convert to kes if not Kenyan
                currency_rates = CurrencyRates.objects.last()
                currencies = CountryInfo(user.country).currencies()

                if currency_rates and currencies:
                    amount = int(currency_rates.get_kes_amount(currencies[0], amount))
                else:
                    # No currency rates and currencies
                    forms.ValidationError('An unexpected error occurred')

            # Block if amount is less than min withdraw
            if amount < settings.MIN_WITHDRAWAL:
                msg = 'Amount is less than minimum withdrawal'
                self.add_error('amount', msg)

            # Block if amount is more than wallet bal
            if amount > user.wallet_bal:
                self.add_error('amount', 'Amount is more than wallet balance.')

        else:
            forms.ValidationError('An unexpected error occurred')

    def get_user(self):
        cleaned_data = super().clean()
        id_2 = cleaned_data.get('id_2')
        return UserModel.objects.get(id_2=id_2)

    def gross_amount(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        user = self.get_user()

        if user.country != 'KE':
            # Convert to kes if not Kenyan
            currency_rates = CurrencyRates.objects.last()
            currencies = CountryInfo(user.country).currencies()
            amount = int(currency_rates.get_kes_amount(currencies[0], amount))

        return amount

    def net_amount(self):
        return self.gross_amount() - settings.WITHDRAWAL_CHARGE


class ProfileDetailsForm(forms.ModelForm):

    class Meta:
        model = UserModel
        fields = ['username', 'email', 'first_name', 'last_name']


class BillingDetailsForm(forms.ModelForm):
    user_id = forms.IntegerField(min_value=1)

    class Meta:
        model = UserModel
        fields = ['country', 'phone_number', 'mpesa_number', 'user_id']

    def clean(self):
        cleaned_data = super(BillingDetailsForm, self).clean()
        country = cleaned_data.get('country')
        phone_number = cleaned_data.get('phone_number')
        mpesa_number = cleaned_data.get('mpesa_number')
        user_id = cleaned_data.get('user_id')

        # Validate phone number
        parsed_phone = parse_phone_number(phone_string=phone_number, country_code=country)
        if parsed_phone:

            if UserModel.objects.filter(phone_number=parsed_phone).exclude(pk=user_id).exists():
                # Phone number exists
                self.add_error('phone_number', 'Phone number already exists')

        else:
            self.add_error('phone_number', 'Please enter a valid phone number')

        # Validate mpesa number
        if country == 'KE':
            if mpesa_number:
                parsed_mpesa = parse_phone_number(phone_string=mpesa_number, country_code=country)

                if parsed_mpesa and validate_mpesa_number(parsed_mpesa):

                    if UserModel.objects.filter(mpesa_number=parsed_mpesa).exclude(pk=user_id).exists():
                        # Mpesa number exists
                        self.add_error('mpesa_number', 'Phone number already exists')

                else:
                    self.add_error('mpesa_number', 'Please enter a valid mpesa number')

            else:
                # No mpesa number
                self.add_error('mpesa_number', 'Mpesa number required for users in Kenya')

    def clean_user_id(self):
        user_id = self.cleaned_data.get('user_id')

        if not UserModel.objects.filter(pk=user_id, is_active=True).exists():
            raise ValidationError('User does not exist')

        return user_id

    def parsed_phone(self):
        cleaned_data = super(BillingDetailsForm, self).clean()
        country = cleaned_data.get('country')
        phone_number = cleaned_data.get('phone_number')
        return parse_phone_number(phone_string=phone_number, country_code=country)

    def parsed_mpesa(self):
        cleaned_data = super(BillingDetailsForm, self).clean()
        country = cleaned_data.get('country')
        mpesa_number = cleaned_data.get('mpesa_number')
        return parse_phone_number(phone_string=mpesa_number, country_code=country) if country == 'KE' else None


class ProfilePicForm(forms.ModelForm):

    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    w = forms.FloatField(widget=forms.HiddenInput())
    h = forms.FloatField(widget=forms.HiddenInput())

    class Meta:
        model = get_user_model()
        fields = ['pic', 'x', 'y', 'w', 'h']

    def save(self, *args, **kwargs):
        user_obj = super(ProfilePicForm, self).save()

        data = {
            'image_field': user_obj.pic,
            'x': self.cleaned_data['x'],
            'y': self.cleaned_data['y'],
            'w': self.cleaned_data['w'],
            'h': self.cleaned_data['h'],
            'width': 400, 'height': 400
        }

        resized_img = crop_img(data)
        resized_img.save(user_obj.pic.path)

        # Rename profile pic
        rename_model_file(file=user_obj.pic, instance=user_obj)

        return user_obj
