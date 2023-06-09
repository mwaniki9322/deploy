from django.contrib import admin
from . models import TaskItem, TaskTaking


admin.site.register(TaskItem)
admin.site.register(TaskTaking)
