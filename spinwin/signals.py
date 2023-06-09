from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SpinRecord
from .utils import change_spinwin_give_pool


@receiver(post_save, sender=SpinRecord)
def new_spin_record(sender, instance, created, **kwargs):
    if created:
        award = instance.stop_segment.win_amount
        if award > 0:
            # Deduct from give pool
            change_spinwin_give_pool(amount=-award)
