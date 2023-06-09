from django import forms
from django.contrib.auth import get_user_model

from . models import TaskItem


UserModel = get_user_model()


class TaskItemForm(forms.ModelForm):
    class Meta:
        model = TaskItem
        fields = ['content']


class TaskSubscribeForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['tasks_package']
