from django import forms
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class AdminWalletTopUpForm(forms.Form):
    amount = forms.IntegerField(min_value=1)


class AdminTopUpSpinsForm(forms.Form):
    users_q = UserModel.objects.all()
    amount = forms.DecimalField(decimal_places=2, max_digits=7)


class AdminChangePasswordForm(forms.Form):
    new_password1 = forms.CharField(max_length=254)
    new_password2 = forms.CharField(max_length=254)

    def clean(self):
        cleaned_data = super(AdminChangePasswordForm, self).clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 != new_password2:
            self.add_error('new_password2', 'Passwords do not match.')
