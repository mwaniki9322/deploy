from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone

from accounts.utils import activate_user
from mpesa.models import MpesaConfirmation, MpesaB2CResult
from mpesa.utils import extract_mpesa_confirmation
from online_marketing.celery import app
from tasks_feature.utils import tasks_subscribe_user

UserModel = get_user_model()


def activate_user_process(mpesa_confirmation):
    user_pk = mpesa_confirmation.account_number[2:]

    # Try to load user
    user = UserModel.objects.filter(pk=user_pk).first()

    if user and settings.ACTIVATION_AMOUNT == mpesa_confirmation.amount:

        # Activate membership
        activate_user(user=user)
        return True

    return False


def buy_spins_process(mpesa_confirmation):
    user_pk = mpesa_confirmation.account_number[2:]

    # Try to load user
    user = UserModel.objects.filter(pk=user_pk).first()

    if user:
        # Top up spins
        amount = mpesa_confirmation.amount
        UserModel.objects.filter(pk=user_pk).update(spinwin_bal=F('spinwin_bal') + amount)

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
        return False


def tasks_subscribe_process(mpesa_confirmation):
    user_pk = mpesa_confirmation.account_number[2:]
    user = UserModel.objects.filter(pk=user_pk).first()

    if not user:
        # User mot found
        return False

    amount = mpesa_confirmation.amount
    package = None

    for key, value in settings.TASKS_PACKAGES.items():

        if value['price'] == amount:
            package = key
            break

    if package:
        # Subscribe user to package
        tasks_subscribe_user(user, package)
        return True
    else:
        return False


# Confirmation processes based on acc num prefix
confirmation_processes = {
    'aa': activate_user_process,
    'sw': buy_spins_process,
    'ts': tasks_subscribe_process,
}


@app.task
def mpesa_confirmation_process(pk):
    mpesa_confirmation = MpesaConfirmation.objects.filter(pk=pk).first()

    if mpesa_confirmation and not mpesa_confirmation.is_processed:

        # Extract data
        extract_mpesa_confirmation(pk, mpesa_confirmation.data)

        # Refresh confirmation object
        mpesa_confirmation.refresh_from_db()

        # Acc num prefix
        ac_prefix = mpesa_confirmation.account_number[:2].lower()

        if ac_prefix in confirmation_processes:

            # Run respective process
            is_processed = confirmation_processes[ac_prefix](mpesa_confirmation)

            # Mark as processed
            mpesa_confirmation.is_processed = is_processed
            mpesa_confirmation.save()

            return 'Mpesa confirmation, {}, processed'.format(pk)

        else:
            return 'Unable to process mpesa confirmation - {}'.format(pk)

    else:
        return 'Mpesa confirmation, {}, not found'.format(pk)


@app.task
def mpesa_b2c_result_process(pk):
    try:
        b2c_result = MpesaB2CResult.objects.get(pk=pk)
    except MpesaB2CResult.DoesNotExist:
        b2c_result = None

    if b2c_result:

        if b2c_result.withdrawal:

            withdrawal = b2c_result.withdrawal

            if b2c_result.is_success():

                # Disbursement was successful
                is_disbursed = True
                disbursed_at = timezone.now()
                status = 'disbursed'
                msg = 'Withdrawal of Ksh. {} by {} has been disbursed.'.format(
                    withdrawal.amount, withdrawal.user.username
                )

            else:
                # Disbursement failed. Reset
                is_disbursed = False
                disbursed_at = None
                status = 'failed_disbursement'
                msg = 'Withdrawal of Ksh. {} by {} has failed disbursement.'.format(
                    withdrawal.amount, withdrawal.user.username
                )

            # Update withdrawal
            withdrawal.is_disbursed = is_disbursed
            withdrawal.disbursed_at = disbursed_at
            withdrawal.save()

            # Send alert
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'admin_alert',
                {
                    'type': 'send.alert',
                    'alert': {
                        'message': 'withdrawal_alert',
                        'status': status,
                        'id': withdrawal.pk,
                        'msg': msg,
                    },
                }
            )

        return 'Mpesa b2c result, {}, processed'.format(pk)
    else:
        return 'Mpesa b2c result, {}, not found'.format(pk)
