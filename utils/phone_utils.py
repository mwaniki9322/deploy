import phonenumbers
import pycountry
from phonenumbers import carrier, geocoder


def validate_phone(phone_string):
    """
    Checks if a given string is a valid phone number
    """

    try:

        num = phonenumbers.parse(phone_string)
        if not phonenumbers.is_valid_number(num):
            return False

    except phonenumbers.NumberParseException:

        return False

    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)


def validate_mpesa_number(phone_string):
    """
    Checks if a given string is a valid M-pesa number
    """
    if validate_phone(phone_string):
        mpesa_number = phonenumbers.parse(phone_string)

        if carrier.name_for_number(mpesa_number, "en") == 'Safaricom':
            return True

    return False


def local_phone_number(phone_string):

    validated_number = validate_phone(phone_string)

    if validated_number:

        phone_obj = phonenumbers.parse(validated_number)

        return '0{}'.format(phone_obj.national_number)

    else:
        return None


def get_phone_carrier(phone_string):
    """
    Return phone carrier
    """
    if validate_phone(phone_string):
        phone = phonenumbers.parse(phone_string)

        return carrier.name_for_number(phone, "en")

    return False


def phone_from_mpesa_acc_num(acc_num):
    num = acc_num[2:]
    num_list = list(num)
    num_list[0] = '+254'
    return ''.join(num_list)


def parse_phone_number(phone_string, country_code):
    try:

        phone = phonenumbers.parse(phone_string, country_code)

        if phonenumbers.is_valid_number(phone):
            # Confirm country
            country = pycountry.countries.get(alpha_2=country_code)

            if hasattr(country, 'common_name'):
                country_name = country.common_name
            else:
                country_name = country.name

            if geocoder.description_for_number(phone, "en") != country_name:
                # Phone number country does not match country specified
                return None

            # Return phone number in E.164 format
            return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        else:
            # String is not a valid phone number
            return None

    except phonenumbers.NumberParseException:
        # String can't be parsed to phone number
        return None

    except TypeError:
        return None
