"""
Order food through terminal.

Usage:
  order-food --config=<config> [--coupon-code=<coupon_code>] [--log-level=<log_level>]
  order-food (-h | --help)
  order-food --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  --config=<config>             Path to config file (.json is expected).
  --log-level=<log_level>       Log level [default: INFO].
  --coupon-code=<coupon_code>   Discount offers [default: ].
"""
import os
import json
import time

from docopt import docopt

from swiggy_order.apis import login, update_cart, apply_coupon_code, place_order
from swiggy_order.utils import log, change_log_level


def extract_if_valid(config_file, config, property):
    try:
        return config[property]
    except KeyError:
        KeyError(f"Expected key `registered_phone` within {config_file}.")

def order_food(config_file, config):
    menu = extract_if_valid(config_file, config, "menu")
    registered_phone = extract_if_valid(config_file, config, "registered_phone")
    address_id = extract_if_valid(config_file, config, "address_id")
    choice = None
    item_index = -1
    menu_items = [f'{i + 1}) {item["name"]}' for i, item in enumerate(menu)]

    while not choice:
        log.info("\n\t\tMENU\n\n%s", "\n".join(menu_items))
        choice = input("Enter item id: ")
        
        if not choice.isdigit():
            choice = None
            continue
        
        item_index = int(choice) - 1
        if item_index > len(menu_items):
            choice = None

    selected_items = menu[item_index]["payload"]
    return registered_phone, address_id, selected_items


def main():
    args = docopt(__doc__)
    config_file = args["--config"]
    log_level = args["--log-level"]
    coupon_code = args["--coupon-code"]

    if log_level:
        change_log_level(log_level)

    with open(config_file, "r") as handle:
        config = json.load(handle)

    registered_phone, address_id, all_items = order_food(config_file, config)

    login(registered_phone)
    log.info("Setting items in cart.")
    update_cart(all_items)
    time.sleep(1.5)
    log.info("Applying coupon code='%s'", coupon_code)
    apply_coupon_code(coupon_code=coupon_code)
    time.sleep(1.5)
    place_order("SwiggyPay", address_id)
