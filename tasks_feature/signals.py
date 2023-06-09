from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import TaskItem
from .tasks import index_tasks_items_task


@receiver(post_save, sender=TaskItem)
def new_task_item(sender, instance, created, **kwargs):
    if created:
        # Index tasks items in the background
        transaction.on_commit(lambda: index_tasks_items_task.apply_async())


@receiver(post_delete, sender=TaskItem)
def delete_task_item(sender, instance, **kwargs):
    # Re-index tasks items in the background
    transaction.on_commit(lambda: index_tasks_items_task.apply_async())
