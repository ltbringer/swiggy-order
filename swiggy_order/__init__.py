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
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import checkboxlist_dialog

from swiggy_order.apis import login, update_cart, apply_coupon_code, place_order
from swiggy_order.utils import log, change_log_level


def combine_items(menu_items, address_id):
    combined_cart = [menu_items[0]]
    for menu_item in menu_items[1:]:
        combined_cart[0]["cart"]["cartItems"].append(menu_item["cart"]["cartItems"][0])
    combined_cart[0]["cart"]["addressId"] = address_id
    return combined_cart[0]


def extract_if_valid(config_file, config, property):
    try:
        return config[property]
    except KeyError:
        KeyError(f"Expected key `registered_phone` within {config_file}.")

def order_food(config_file, config):
    menu = extract_if_valid(config_file, config, "menu")
    registered_phone = extract_if_valid(config_file, config, "registered_phone")
    address_id = extract_if_valid(config_file, config, "address_id")

    checkboxes = [(i, item["name"]) for i, item in enumerate(menu)]
    item_indices = checkboxlist_dialog(title="Menu", text="Pick items from this menu:", values=checkboxes).run()
    selected_items = [item["payload"] for i, item in enumerate(menu) if i in item_indices]
    all_items = combine_items(selected_items, address_id)
    return registered_phone, address_id, all_items


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
