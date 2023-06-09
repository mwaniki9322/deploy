from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from . tasks import auto_disburse_withdrawal_task
from accounts.models import Income, Withdrawal

UserModel = get_user_model()


@receiver(post_save, sender=Income)
def new_income(sender, instance, created, **kwargs):
    if created:
        users = UserModel.objects.select_for_update().filter(pk=instance.user_id)
        with transaction.atomic():
            for user in users:
                user.wallet_bal = F('wallet_bal') + instance.amount
                user.save()


@receiver(post_save, sender=Withdrawal)
def new_withdrawal(sender, instance, created, **kwargs):
    if created:
        users = UserModel.objects.select_for_update().filter(pk=instance.user_id)
        with transaction.atomic():
            for user in users:
                user.wallet_bal = F('wallet_bal') - instance.amount
                user.save()

        if instance.user.mpesa_number:
            # Auto disburse in the background with celery
            transaction.on_commit(lambda: auto_disburse_withdrawal_task.apply_async((instance.pk,), ))
