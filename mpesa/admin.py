from django.contrib import admin
from . models import MpesaConfirmation, MpesaCallback, MpesaB2CResult


admin.site.register(MpesaConfirmation)
admin.site.register(MpesaCallback)
admin.site.register(MpesaB2CResult)
