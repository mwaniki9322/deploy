import secrets
import uuid

from django.utils import timezone
from django.utils.crypto import get_random_string
import string
from dateutil.relativedelta import relativedelta
from dateutil import tz


def unique_slugify(instance, slug):
    model = instance.__class__
    unique_slug = slug
    while model.objects.filter(
            slug=unique_slug
    ).exists():
        unique_slug = '{}-{}'.format(slug, get_random_string(length=10))
    return unique_slug


def unique_guid(instance):

    model = instance.__class__
    guid = uuid.uuid4()

    while model.objects.filter(guid=guid).exists():
        guid = uuid.uuid4()

    return guid


def unique_id_2(instance):
    chars = string.digits + string.ascii_letters
    model = instance.__class__
    id_2 = get_random_string(length=10, allowed_chars=chars)

    while model.objects.filter(id_2=id_2).exists():
        id_2 = get_random_string(length=10, allowed_chars=chars)

    return id_2


def secrets_unique_id_2(model_name, length):
    """Generate and return a unique id_2 for model"""
    id_2 = secrets.token_hex(length)

    while model_name.objects.filter(id_2=id_2).exists():
        # Exists, generate again
        id_2 = secrets.token_hex(length)

    return id_2


def elapsed_time(start_time, end_time, suf):

    """
    Start time should the in future of end time
    """

    diff = relativedelta(start_time, end_time)

    if diff.years > 0:
        return '{} years {}'.format(diff.years, suf) if diff.years > 1 else 'An year {}'.format(suf)
    elif diff.months > 0:
        return '{} months {}'.format(diff.months, suf) if diff.months > 1 else 'A month {}'.format(suf)
    elif diff.days > 0:
        return '{} days {}'.format(diff.days, suf) if diff.days > 1 else 'A day {}'.format(suf)
    elif diff.hours > 0:
        return '{} hours {}'.format(diff.hours, suf) if diff.hours > 1 else 'An hour {}'.format(suf)
    elif diff.minutes > 0:
        return '{} mins {}'.format(diff.minutes, suf) if diff.minutes > 1 else 'A min {}'.format(suf)
    elif diff.seconds > 0:
        return '{} secs {}'.format(diff.seconds, suf) if diff.seconds > 1 else 'A sec {}'.format(suf)
    else:
        return '0 secs {}'.format(suf)


def utc_to_local_time():
    to_zone = tz.gettz('Africa/Nairobi')
    utc_now = timezone.now()
    return utc_now.astimezone(to_zone)


def utc_local_eq(utc_time):
    return utc_time.astimezone(tz.gettz('Africa/Nairobi'))
