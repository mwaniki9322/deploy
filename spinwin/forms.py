from django import forms
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class TopUpSpinsForm(forms.Form):
    amount = forms.IntegerField(min_value=20)
