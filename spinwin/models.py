from django.conf import settings
from django.db import models


class GivePool(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return 'Give pool - {}'.format(self.pk)


class Segment(models.Model):
    win_amount = models.DecimalField(max_digits=10, decimal_places=2)
    options = models.JSONField(default=dict)
    winning_chance = models.FloatField()

    def __str__(self):
        return '{} - Chance {} - Amount {}'.format(self.options['text'], self.winning_chance, self.win_amount)


class SpinRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    stop_segment = models.ForeignKey(Segment, on_delete=models.CASCADE)
    acknowledged = models.BooleanField(default=False)
    award = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Spin record {} - {}'.format(self.pk, self.user)
