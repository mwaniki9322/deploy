import decimal

from django.db import models


class MpesaCallback(models.Model):
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'M-pesa callback-{}'.format(self.pk)


class MpesaConfirmation(models.Model):
    data = models.JSONField()
    is_extracted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    # Cleaned data
    first_name = models.CharField(max_length=150, null=True, blank=True)
    middle_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    transaction_id = models.CharField(max_length=150, null=True, blank=True)
    account_number = models.CharField(max_length=150, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    phone_number = models.CharField(max_length=150, null=True, blank=True)
    organisation_bal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):

        if self.is_extracted:
            return '{} - {} - Ksh. {}'.format(
                self.transaction_id, self.get_full_name(), self.amount
            )
        else:
            return '{} - {} - Ksh. {}'.format(
                self.data['TransID'], self.get_full_name(), decimal.Decimal(self.data['TransAmount'])
            )

    def get_full_name(self):
        if self.is_extracted:
            return '{} {} {}'.format(
                self.first_name, self.middle_name, self.last_name
            ).lower()
        else:
            return '{} {} {}'.format(
                self.data['FirstName'], self.data['MiddleName'], self.data['LastName']
            ).lower()

    def get_purpose(self):
        ac_prefix = self.account_number[:2].upper()
        purposes = {
            'AA': 'Account activation',
            'SW': 'SpinWin',
            'TS': 'Tasks subscribe'
        }
        if ac_prefix in purposes:
            return purposes[ac_prefix]
        else:
            return 'N/A'


class MpesaB2CResult(models.Model):
    data = models.JSONField()
    withdrawal = models.ForeignKey(
        'accounts.Withdrawal', null=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'M-pesa b2c result-{}'.format(self.pk)

    def get_transaction_id(self):
        return self.data['Result']['TransactionID']

    def get_amount(self):
        if self.is_success():
            return decimal.Decimal(self.data['Result']['ResultParameters']['ResultParameter'][0]['Value'])
        else:
            return decimal.Decimal('0.00')

    def get_full_name(self):
        if self.is_success():
            return '{}'.format(
                self.data['Result']['ResultParameters']['ResultParameter'][2]['Value'].split(' - ')[1]
            ).lower()
        else:
            return 'N/A'

    def get_phone_number(self):
        if self.is_success():
            return self.data['Result']['ResultParameters']['ResultParameter'][2]['Value'].split(' - ')[0]
        else:
            return 'N/A'

    def conversation_id(self):
        return self.data['Result']['ConversationID']

    def originator_conversation_id(self):
        return self.data['Result']['OriginatorConversationID']

    def is_success(self):
        return True if self.data['Result']['ResultCode'] == 0 else False
