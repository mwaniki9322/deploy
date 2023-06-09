from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
import datetime
from . models import TaskItem, TaskTaking
from django.utils import timezone


def user_tasks_today(user):
    # Return number of tasks taken by user in current day
    now = timezone.now()
    return TaskTaking.objects.filter(
        user=user, finished=True, created_at__year=now.year, created_at__month=now.month,
        created_at__day=now.day
    ).count()


def user_tasks_summary(user):
    total_taken = TaskTaking.objects.filter(user=user, finished=True).count()
    taken_today = user_tasks_today(user)

    if user.tasks_package:
        taken_today = '{}/{}'.format(taken_today, settings.TASKS_PACKAGES[user.tasks_package]['tasks_per_day'])

    return {
        'total_taken': total_taken,
        'taken_today': taken_today,
    }


def tasks_subscribe_user(user, package):
    validity = settings.TASKS_PACKAGES[package]['validity']

    expiry_date = timezone.now() + datetime.timedelta(days=validity)

    # Save
    user.tasks_package = package
    user.tasks_package_expire = expiry_date
    user.save()

    # Delete task takings
    TaskTaking.objects.filter(user=user).delete()

    # Send alert to websocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'user_alert_{}'.format(user.id_2),
        {
            'type': 'send.alert',
            'alert': {
                'message': 'tasks_subscribed'
            },
        }
    )


def next_user_task(user):
    """
    Find next task for user
    """
    last_taking = TaskTaking.objects.filter(
        user=user, finished=True
    ).order_by('-created_at').first()

    if last_taking:
        # Has started. Return next task
        return TaskItem.objects.filter(id__gt=last_taking.task_item.id).order_by('id').first()
    else:
        # First time. Return task 1
        return TaskItem.objects.order_by('id').first()
