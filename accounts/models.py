import decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from utils.misc import unique_id_2
from utils.phone_utils import local_phone_number


class User(AbstractUser):
    email = models.EmailField(null=True)
    mpesa_number = models.CharField(unique=True, max_length=50, null=True, blank=True)
    phone_number = models.CharField(unique=True, max_length=50, null=True)
    pic = models.ImageField(
        upload_to='users_profile_pics/%Y/%m/%d/', null=True
    )
    id_2 = models.CharField(max_length=50, null=True, unique=True)

    utc_offset = models.FloatField(default=0)
    referrer = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)

    is_activated = models.BooleanField(default=False)
    wallet_bal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spinwin_bal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Tasks
    TASKS_PACKAGES_CHOICES = [
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum')
    ]
    tasks_package = models.CharField(max_length=20, choices=TASKS_PACKAGES_CHOICES, null=True)
    tasks_package_expire = models.DateTimeField(null=True)
    tasks_wallet = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    country = models.CharField(max_length=5, default='KE')

    def __str__(self):
        return self.username

    def get_pic(self):
        return self.pic.url if self.pic else '/static/images/no-image-person.jpg'

    def get_greeting_name(self):
        if self.first_name:
            name = super().first_name
        else:
            name = self.username

        return name.title()

    def get_full_name(self):

        if self.first_name and self.last_name:
            return super().get_full_name()
        else:
            return self.username.title()

    def get_local_mpesa_number(self):
        return local_phone_number(self.mpesa_number) if self.mpesa_number else ''

    def get_local_phone_number(self):
        return local_phone_number(self.phone_number) if self.phone_number else ''

    def total_income(self):
        amount = Income.objects.filter(user=self).aggregate(
            models.Sum('amount')
        )
        return round(amount['amount__sum'], 2) if amount['amount__sum'] else decimal.Decimal('0.00')

    def income_break(self, amount):
        total_income = self.total_income()
        amount = round(amount['amount__sum'], 2) if amount['amount__sum'] else decimal.Decimal('0.00')
        percentage = (amount / total_income) * 100 if total_income > 0 else 0
        return {'amount': amount, 'percentage': round(percentage, 2)}

    def referral_income(self):
        amount = Income.objects.filter(user=self, source='RB').aggregate(
            models.Sum('amount')
        )
        return self.income_break(amount)

    def spinwin_income(self):
        amount = Income.objects.filter(user=self, source='SP').aggregate(
            models.Sum('amount')
        )
        return self.income_break(amount)

    def awards_income(self):
        amount = Income.objects.filter(user=self, source='AW').aggregate(
            models.Sum('amount')
        )
        return self.income_break(amount)

    def tasks_income(self):
        amount = Income.objects.filter(user=self, source='TS').aggregate(
            models.Sum('amount')
        )
        return self.income_break(amount)

    def get_this_month_income(self):
        now = timezone.now()
        this_month = now.replace(day=1)

        this_month_income = Income.objects.filter(
            user=self, created_at__year=this_month.year, created_at__month=this_month.month
        ).aggregate(models.Sum('amount'))
        this_month_income = round(this_month_income['amount__sum'], 2) if this_month_income['amount__sum'] \
            else decimal.Decimal('0.00')

        return this_month_income

    def daily_income(self):
        """Return daily income for user"""
        incomes = Income.objects.filter(user=self).values('created_at')
        dates = [x['created_at'].date() for x in incomes]
        total_days = len(list(dict.fromkeys(dates)))
        return round((self.total_income() / total_days), 2) if total_days > 0 else 0

    def total_withdrawals(self):
        amount = Withdrawal.objects.filter(user=self).aggregate(
            models.Sum('amount')
        )
        return round(amount['amount__sum'], 2) if amount['amount__sum'] else decimal.Decimal('0.00')

    def total_referrals(self):
        return User.objects.filter(referrer=self).count()

    def get_tasks_package_name(self):
        return self.tasks_package.title() if self.tasks_package else None

    def get_tasks_package_status(self):
        if self.tasks_package:
            if timezone.now() > self.tasks_package_expire:
                return 'expired'
            else:
                return 'active'
        else:
            return 'not_subscribed'

    def save(self, *args, **kwargs):
        # Save id_2 on create
        if not self.id_2:
            self.id_2 = unique_id_2(self)

        if not self.email:
            # Nullify email if not available
            self.email = None

        super(User, self).save()


class Income(models.Model):

    class EarningSources(models.TextChoices):
        REFERRAL_BONUS = 'RB'
        SPIN_WIN = 'SP'
        AWARD = 'AW'
        TASKS = 'TS'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(
        max_length=3,
        choices=EarningSources.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return 'Ksh {} - {} - {}'.format(self.amount, self.get_source(), self.user)
        else:
            return 'Ksh {} - {}'.format(self.amount, self.get_source())

    def get_source(self):
        sources = {
            'RB': 'Referral bonus',
            'SP': 'Spin win',
            'AW': 'Award',
            'TS': 'Tasks'
        }

        return sources[self.source]


class Withdrawal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_disbursed = models.BooleanField(default=False)  # Has the amount been sent to user
    is_cancelled = models.BooleanField(default=False)
    disbursed_at = models.DateTimeField(null=True)  # Time amount was disbursed
    cancelled_at = models.DateTimeField(null=True)  # Time it was cancelled
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Ksh {} - {}'.format(self.amount, self.user.username)
