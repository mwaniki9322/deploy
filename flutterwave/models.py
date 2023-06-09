from django.db import models
from accounts.models import User
from utils.misc import secrets_unique_id_2
from utils.models import CurrencyRates


class FWPayment(models.Model):
    event = models.JSONField()  # Data for specific event like
    data = models.JSONField(null=True)
    id_2 = models.CharField(max_length=150, editable=False, unique=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return 'Flutterwave payment - {}'.format(self.pk)

    def save(self, *args, **kwargs):
        # Save id_2 on create
        if not self.id_2:
            self.id_2 = secrets_unique_id_2(model_name=FWPayment, length=16)

        # Save amount on create
        if not self.amount:
            currency_rates = CurrencyRates.objects.last()
            if currency_rates:
                self.amount = currency_rates.get_kes_amount(self.event['currency'], self.event['amount'])

        super(FWPayment, self).save()

    def get_trans_id(self):
        return self.data['data']['id'] if self.data else None

    def get_amount(self):
        if self.data:
            return self.data['data']['amount']
        else:
            return None

    def get_full_name(self):
        return self.data['data']['customer']['name'] if self.data else None

    def get_status(self):
        if self.data:
            return self.data['data']['status']
        else:
            return None

    def get_currency(self):
        if self.data:
            return self.data['data']['currency']
        else:
            return None

    def get_email(self):
        return self.data['data']['customer']['email'] if self.data else None

    def get_payment_type(self):
        return self.data['data']['payment_type'] if self.data else None

    def is_verified(self):
        if self.data:
            status = self.get_status()
            amount = self.get_amount()
            currency = self.get_currency()

            if status == 'successful' and currency == self.event['currency'] and amount == self.event['amount']:
                return True
            else:
                return False

        else:
            return False
