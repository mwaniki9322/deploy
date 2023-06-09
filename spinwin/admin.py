from django.contrib import admin
from . models import SpinRecord, Segment, GivePool


admin.site.register(GivePool)
admin.site.register(Segment)
admin.site.register(SpinRecord)
