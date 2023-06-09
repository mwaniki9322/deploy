from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MpesaConfirmation, MpesaB2CResult
from .tasks import mpesa_confirmation_process, mpesa_b2c_result_process


@receiver(post_save, sender=MpesaConfirmation)
def new_mpesa_confirmation(sender, instance, created, **kwargs):
    if created:
        # Process confirmation
        transaction.on_commit(lambda: mpesa_confirmation_process.apply_async((instance.pk, ), ))


@receiver(post_save, sender=MpesaB2CResult)
def new_mpesa_b2c_result(sender, instance, created, **kwargs):
    if created:
        # Process b2c result
        transaction.on_commit(lambda: mpesa_b2c_result_process.apply_async((instance.pk,), ))
