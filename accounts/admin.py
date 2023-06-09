from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Income, Withdrawal


admin.site.register(User, UserAdmin)
admin.site.register(Income)
admin.site.register(Withdrawal)
