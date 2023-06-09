import decimal

from django.db import models


class CurrencyRates(models.Model):
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name_plural = 'Currency rates'

    def __str__(self):
        return 'Currency rates - {}'.format(self.pk)

    def get_rate(self, currency):
        if currency in self.data['data']:
            return decimal.Decimal(str(self.data['data'][currency]['value']))
        else:
            return None

    def get_other_amount(self, currency, kes_amount):
        rate = self.get_rate(currency)

        if rate:
            amount = kes_amount * rate
            return amount.quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_HALF_EVEN)
        else:
            return None

    def get_kes_amount(self, currency, other_amount):
        rate = self.get_rate(currency)

        if rate:
            amount = other_amount / rate
            return amount.quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_HALF_EVEN)
        else:
            return None
