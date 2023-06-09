from django.db.models import F

from .models import GivePool


def change_spinwin_give_pool(amount):
    give_pool = GivePool.objects.last()

    if give_pool:
        # Change amount
        GivePool.objects.filter(pk=give_pool.pk).update(amount=F('amount') + amount)
    else:
        # Create new pool
        GivePool.objects.create(amount=amount)
