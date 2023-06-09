import datetime

from django.db import models
from django.db.models import UniqueConstraint


class TaskItem(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    index = models.PositiveIntegerField(null=True, editable=False)

    def __str__(self):
        return 'Task {}'.format(self.index)

    def takings_count(self):
        return TaskTaking.objects.filter(task_item=self, finished=True).count()


class TaskTaking(models.Model):
    task_item = models.ForeignKey(TaskItem, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['task_item', 'user'], name='unique_task_taking')
        ]

    def __str__(self):
        return '{} - {}'.format(self.task_item, self.user)

    def finish_time(self):
        return self.created_at + datetime.timedelta(seconds=30)
