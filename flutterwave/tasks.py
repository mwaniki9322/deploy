from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import F
from huey.contrib.djhuey import db_task

from accounts.utils import activate_user
from tasks_feature.utils import tasks_subscribe_user
from utils.models import CurrencyRates
from .models import FWPayment
from .utils import get_fw_trans

UserModel = get_user_model()


def activate_account_process(payment):
    user = UserModel.objects.filter(pk=payment.event['user_id']).first()
    if not user:
        # User does not exist
        return False

    # Activate membership
    activate_user(user=user)
    return True


def buy_spins_process(payment):
    user = UserModel.objects.filter(pk=payment.event['user_id']).first()
    if not user:
        # User does not exist
        return False

    currency_rates = CurrencyRates.objects.last()
    if currency_rates:
        kes_amount = currency_rates.get_kes_amount(payment.get_currency(), payment.get_amount())

        # Top up spins
        UserModel.objects.filter(pk=user.pk).update(spinwin_bal=F('spinwin_bal') + kes_amount)

        # Refresh user object
        user.refresh_from_db()

        # Send alert to websocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'user_alert_{}'.format(user.id_2),
            {
                'type': 'send.alert',
                'alert': {
                    'message': 'spinwin_bal',
                    'spinwin_bal': str(user.spinwin_bal)
                },
            }
        )

        return True
    else:
        # No currency rates
        return False


def tasks_subscribe_process(payment):
    user = UserModel.objects.filter(pk=payment.event['user_id']).first()
    if not user:
        # User does not exist
        return False

    # Subscribe user to package
    tasks_subscribe_user(user, payment.event['package'])
    return True


process_commands = {
    'ACCOUNT_ACTIVATION': activate_account_process,
    'BUY_SPINS': buy_spins_process,
    'TASKS_SUBSCRIBE': tasks_subscribe_process,
}


@db_task()
def process_fw_payment(pk):
    payment = FWPayment.objects.get(pk=pk)

    if payment.is_processed:
        return 'Payment already processed'

    data = get_fw_trans(payment.event['fw_trans_id'])

    if not data:
        return 'Unable to get Flutterwave transaction'

    payment.data = data
    payment.save()

    if not payment.is_verified():
        return 'Payment not verified'

    # Run event type process
    if payment.event['intent'] in process_commands:
        is_processed = process_commands[payment.event['intent']](payment)
    else:
        is_processed = False

    payment.is_processed = is_processed
    payment.save()

    return 'Payment processed'
