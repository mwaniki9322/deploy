from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Withdrawal
from mpesa.utils import mpesa_b2c_request
from online_marketing.celery import app


@app.task
def auto_disburse_withdrawal_task(pk):
    withdrawal = Withdrawal.objects.filter(pk=pk).first()

    if not withdrawal:
        # Withdrawal does not exist
        return 'Withdrawal {} not found'.format(pk)

    # Init
    data = {
        'result_url': "https://www.easyearn.co.ke{}".format(
            reverse('mpesa_b2c_result', args=(settings.MPESA_SECRET, withdrawal.pk,))
        ),
        'queue_timeout_url': "https://www.easyearn.co.ke{}".format(
            reverse('mpesa_b2c_queue_time_out', args=(settings.MPESA_SECRET, withdrawal.pk,))
        ),
        'mpesa_number': withdrawal.user.mpesa_number.replace('+', ''),
        'amount': str(withdrawal.net_amount),
        'occasion': timezone.now().strftime('%Y%m%d%H%M%S%f') + str(withdrawal.pk)
    }

    # Send mpesa b2c request
    b2c_request = mpesa_b2c_request(data)

    if b2c_request:
        return 'Withdrawal {} auto disbursed.'.format(pk)
    else:
        # Failed disbursement
        return 'The withdrawal {} failed disbursement'.format(pk)
