import re
from pprint import pformat

import requests

from swiggy_order.constants import (
    SWIGGY_URL,
    CSRF_PATTERN,
    SWIGGY_COOKIE,
    SWIGGY_SEND_OTP_URL,
    SWIGGY_VERIFY_OTP_URL,
    STATUS_FLAG,
    CART_URL,
    APPLY_COUPON_URL,
    PLACE_ORDER_URL,
)
from swiggy_order.utils import log


session = requests.Session()
csrf_source_pattern = re.compile(CSRF_PATTERN)


def get_cookie(cookies, name):
    return cookies.get_dict().get(name)


def validate_response(response):
    try:
        if response.json().get(STATUS_FLAG) != 0:
            log.error(pformat(response))
            raise ValueError(f"Non-zero {STATUS_FLAG}!")
    except AttributeError:
        log.error(response.text)
        raise ValueError(response.text)


def get_otp(registered_phone, sw_cookie, csrf_token):
    return session.post(
        SWIGGY_SEND_OTP_URL,
        headers={
            "content-type": "application/json",
            "Cookie": "__SW={}".format(sw_cookie),
            "User-Agent": "Mozilla/Gecko/Firefox/65.0",
        },
        json={"mobile": registered_phone, "_csrf": csrf_token},
    )


def verify_otp(otp, csrf_token):
    return session.post(
        SWIGGY_VERIFY_OTP_URL,
        headers={
            "content-type": "application/json",
            "User-Agent": "Mozilla/Gecko/Firefox/65.0",
        },
        json={"otp": otp, "_csrf": csrf_token},
    )


def make_connection():
    response = session.get(SWIGGY_URL)
    try:
        csrf_token = csrf_source_pattern.search(response.text).group(1)
        sw_cookie = get_cookie(response.cookies, SWIGGY_COOKIE)
        return sw_cookie, csrf_token
    except IndexError:
        raise IndexError(
            f"Pattern={CSRF_PATTERN} matched but csrf token not found in expected location."
        )
    except TypeError:
        raise TypeError(
            f"Expected response.txt to be str but found {type(response.text)} instead."
        )


def login(registered_phone):
    sw_cookie, csrf_token = make_connection()
    otp_response = get_otp(registered_phone, sw_cookie, csrf_token)

    if otp_response.json().get(STATUS_FLAG) != 0:
        raise ValueError(otp_response.text)

    sw_cookie, csrf_token = make_connection()
    otp = input("Enter OTP: ")

    response = verify_otp(otp, csrf_token)
    validate_response(response)
    log.info(pformat(response.json()))


def update_cart(payload, quantity=1):
    _, csrf_token = make_connection()
    payload["_csrf"] = csrf_token
    payload["cart"]["cartItems"][0]["quantity"] = quantity
    response = session.post(CART_URL, json=payload)
    validate_response(response)
    log.info(pformat(response.json()))


def apply_coupon_code(coupon_code=""):
    if not coupon_code:
        return
    _, csrf_token = make_connection()
    payload = {"couponCode": coupon_code, "_csrf": csrf_token}
    response = session.post(APPLY_COUPON_URL, json=payload)
    validate_response(response)
    log.info(pformat(response.json()))


def place_order(payment_method, address_id):
    _, csrf_token = make_connection()
    payload = {
        "order": {
            "payment_cod_method": payment_method,
            "address_id": str(address_id),
            "order_comments": "",
            "force_validate_coupon": True,
        },
        "_csrf": csrf_token,
    }

    response = session.post(PLACE_ORDER_URL, json=payload)
    validate_response(response)
    log.info(pformat(response.json()))
