#!/usr/bin/env python3
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py --test prod-like; sleep 1; done

import argparse
from collections import deque
from enum import Enum
from math import *
import time
import socket
import json
import sys

# ~~~~~============== CONFIGURATION  ==============~~~~~
# Replace "REPLACEME" with your team name!
team_name = "beeeater"

# ~~~~~============== MAIN LOOP ==============~~~~~

# You should put your code here! We provide some starter code as an example,
# but feel free to change/remove/edit/update any of it as you'd like. If you
# have any questions about the starter code, or what to do next, please ask us!
#
# To help you get started, the sample code below tries to buy BOND for a low
# price, and it prints the current prices for VALE every second. The sample
# code is intended to be a working example, but it needs some improvement
# before it will start making good trades!
positions = {"BOND": 0, "VALBZ": 0, "VALE": 0, "GS": 0, "MS": 0, "WFC": 0, "XLF": 0}
prices = {
    "BOND": {"bid": 0, "ask": 0, "mid": 0},
    "VALBZ": {"bid": 0, "ask": 0, "mid": 0},
    "VALE": {"bid": 0, "ask": 0, "mid": 0},
    "GS": {"bid": 0, "ask": 0, "mid": 0},
    "MS": {"bid": 0, "ask": 0, "mid": 0},
    "WFC": {"bid": 0, "ask": 0, "mid": 0},
    "XLF": {"bid": 0, "ask": 0, "mid": 0},
}
order_num = 1

vale_buy = None
vale_sell = None
xlf_buy = None
xlf_sell = None
components = {
    "VALBZ": {"buy": None, "sell": None},
    "GS": {"buy": None, "sell": None},
    "MS": {"buy": None, "sell": None},
    "WFC": {"buy": None, "sell": None},
}


def vale(exchange):
    # Calculate fair value for valbz
    # If we currently have orders, check if they are still good
    # If they are not, out orders and
    # Check if we're missing an order, then make a new order
    global order_num
    global vale_buy
    global vale_sell
    if positions["VALE"] == 10 and positions["VALBZ"] != 10:
        toConvert = min(10, 10 - positions["VALBZ"])
        exchange.send_convert_message(
            order_id=order_num, symbol="VALE", dir=Dir.SELL, size=toConvert
        )
        order_num += 1
        positions["VALE"] = 10 - toConvert
        positions["VALBZ"] += toConvert
    elif positions["VALE"] == -10 and positions["VALBZ"] != -10:
        toConvert = min(10, 10 + positions["VALBZ"])
        exchange.send_convert_message(
            order_id=order_num, symbol="VALE", dir=Dir.BUY, size=toConvert
        )
        order_num += 1
        positions["VALE"] = toConvert - 10
        positions["VALBZ"] -= toConvert

    if (
        not prices["VALBZ"]["bid"]
        or not prices["VALBZ"]["ask"]
        or not prices["VALBZ"]["mid"]
    ):
        return

    fair = prices["VALBZ"]["mid"]

    dif = 5
    if vale_buy:
        # check if the buy price is less than fair
        if vale_buy[1] > fair - dif:
            exchange.send_cancel_message(order_id=vale_buy[0])
            vale_buy = None
    if vale_sell:
        # check if the sell price is higher than fair
        if vale_sell[1] < fair + dif:
            exchange.send_cancel_message(order_id=vale_sell[0])
            vale_sell = None
    # Buy
    if not vale_buy:
        if 10 - positions["VALE"] > 0:
            exchange.send_add_message(
                order_id=order_num,
                symbol="VALE",
                dir=Dir.BUY,
                price=min(fair - dif, prices["VALE"]["bid"] + 1),
                size=10 - positions["VALE"],
            )
            vale_buy = (order_num, min(fair - dif, prices["VALE"]["bid"] + 1))
            order_num += 1

    # Sell
    if not vale_sell:
        if 10 + positions["VALE"] > 0:
            exchange.send_add_message(
                order_id=order_num,
                symbol="VALE",
                dir=Dir.SELL,
                price=max(fair + dif, prices["VALE"]["ask"] - 1),
                size=10 + positions["VALE"],
            )
            vale_sell = (order_num, max(fair + dif, prices["VALE"]["ask"] - 1))
            order_num += 1


def etf(exchange):
    global order_num
    global xlf_buy
    global xlf_sell

    fair = (
        2 * prices["GS"]["mid"]
        + 3 * prices["MS"]["mid"]
        + 2 * prices["WFC"]["mid"]
        + 3 * prices["BOND"]["mid"]
    ) // 10
    if fair == 0:
        fair = prices["XLF"]["ask"]

    if positions["XLF"] >= 90:
        toConvert = min(
            90, 100 - max(positions["GS"], positions["MS"], positions["WFC"]) // 10 * 10
        )
        if toConvert > 0:
            exchange.send_convert_message(
                order_id=order_num, symbol="XLF", dir=Dir.SELL, size=toConvert
            )
            order_num += 1
            positions["XLF"] -= toConvert
            positions["GS"] += toConvert
            positions["MS"] += toConvert
            positions["WFC"] += toConvert

    elif positions["XLF"] <= -90:
        toConvert = min(
            90, 100 + min(positions["GS"], positions["MS"], positions["WFC"]) // 10 * 10
        )
        if toConvert > 0:
            exchange.send_convert_message(
                order_id=order_num, symbol="XLF", dir=Dir.BUY, size=toConvert
            )
            order_num += 1
            positions["XLF"] += toConvert
            positions["GS"] -= toConvert
            positions["MS"] -= toConvert
            positions["WFC"] -= toConvert

    dif = 5
    if xlf_buy:
        if xlf_buy[1] > fair - dif or xlf_buy[1] < prices["XLF"]["bid"] - 100:
            exchange.send_cancel_message(order_id=xlf_buy[0])
            xlf_buy = None
    if xlf_sell:
        if xlf_sell[1] < fair + dif or xlf_sell[1] > prices["XLF"]["ask"] + 100:
            exchange.send_cancel_message(order_id=xlf_sell[0])
            xlf_sell = None

    if not xlf_buy and 100 - positions["XLF"] > 0:
        exchange.send_add_message(
            order_id=order_num,
            symbol="XLF",
            dir=Dir.BUY,
            price=min(fair - dif, prices["XLF"]["bid"] + 1),
            size=100 - positions["XLF"],
        )
        xlf_buy = (order_num, min(fair - dif, prices["XLF"]["bid"] + 1))
        order_num += 1

    if not xlf_sell and 100 + positions["XLF"] > 0:
        exchange.send_add_message(
            order_id=order_num,
            symbol="XLF",
            dir=Dir.SELL,
            price=max(fair + dif, prices["XLF"]["ask"] - 1),
            size=100 + positions["XLF"],
        )
        xlf_sell = (order_num, max(fair + dif, prices["XLF"]["ask"] - 1))
        order_num += 1


def basket(exchange):
    global order_num
    global components
    for sym in ["VALBZ", "GS", "MS", "WFC"]:
        fair = prices[sym]["mid"]
        if not fair:
            continue
        if positions[sym] == 0:
            components[sym]["buy"] = None
            components[sym]["sell"] = None
        else:
            # Buy back borrowed stock used in creation
            if positions[sym] < 0:
                if components[sym]["buy"] and components[sym]["buy"][1] >= fair:
                    exchange.send_cancel_message(order_id=components[sym]["buy"][0])
                    components[sym]["buy"] = None
                if components[sym]["sell"]:
                    exchange.send_cancel_message(order_id=components[sym]["sell"][0])
                    components[sym]["sell"] = None
                if not components[sym]["buy"]:
                    exchange.send_add_message(
                        order_id=order_num,
                        symbol=sym,
                        dir=Dir.BUY,
                        price=min(fair - 1, prices[sym]["bid"] + 1),
                        size=-positions[sym],
                    )
                    components[sym]["buy"] = (
                        order_num,
                        min(fair - 1, prices[sym]["bid"] + 1),
                        -positions[sym],
                    )
                    order_num += 1
            # Sell off extra stock resulting from redemption
            elif positions[sym] < 0:
                if components[sym]["sell"] and components[sym]["sell"][1] <= fair:
                    exchange.send_cancel_message(order_id=components[sym]["sell"][0])
                    components[sym]["sell"] = None
                if components[sym]["buy"]:
                    exchange.send_cancel_message(order_id=components[sym]["buy"][0])
                    components[sym]["buy"] = None
                if not components[sym]["sell"]:
                    exchange.send_add_message(
                        order_id=order_num,
                        symbol=sym,
                        dir=Dir.SELL,
                        price=max(fair + 1, prices[sym]["ask"] - 1),
                        size=positions[sym],
                    )
                    components[sym]["sell"] = (
                        order_num,
                        max(fair + 1, prices[sym]["ask"] - 1),
                        positions[sym],
                    )
                    order_num += 1


def bond(exchange):
    global order_num
    if 100 - positions["BOND"] > 0:
        exchange.send_add_message(
            order_id=order_num,
            symbol="BOND",
            dir=Dir.BUY,
            price=999,
            size=min(200, 100 - positions["BOND"]),
        )
        order_num += 1
    if 100 + positions["BOND"] > 0:
        exchange.send_add_message(
            order_id=order_num,
            symbol="BOND",
            dir=Dir.SELL,
            price=1001,
            size=min(200, positions["BOND"] + 100),
        )
        order_num += 1


def main():
    args = parse_arguments()
    exchange = ExchangeConnection(args=args)
    hello_message = exchange.read_message()
    print("First message from exchange:", hello_message)
    initialize(hello_message)
    oldBond = 0
    oldTime = time.time()
    bond(exchange)
    while True:
        fetch_data(exchange)
        now = time.time()
        if now - oldTime > 5:
            oldTime = now
            printPrices()
            printPositions()
        basket(exchange)
        etf(exchange)
        vale(exchange)
        if oldBond != positions["BOND"]:
            bond(exchange)
            oldBond = positions["BOND"]


def fetch_data(exchange):
    message = exchange.read_message()

    def best_price(side):
        if message[side]:
            if message[side][0][0]:
                return message[side][0][0]
        if side == "buy":
            return prices[message["symbol"]]["bid"]
        return prices[message["symbol"]]["ask"]

    if message["type"] == "close":
        print("The round has ended")
        sys.exit(0)
    elif message["type"] == "fill":
        symbol = message["symbol"]
        size = message["size"]
        direction = message["dir"]
        if direction == "BUY":
            positions[symbol] += size
        elif direction == "SELL":
            positions[symbol] -= size
        print(f"Filled {direction} {size} {symbol}")
    elif message["type"] == "error":
        print(message)
    elif message["type"] == "reject":
        print(message)
        if message["error"] == "TRADING_CLOSED":
            sys.exit(0)
    elif message["type"] == "book":
        for sym in ["BOND", "VALBZ", "VALE", "GS", "MS", "WFC", "XLF"]:
            if message["symbol"] == sym:
                prices[sym]["bid"] = best_price("buy")
                prices[sym]["ask"] = best_price("sell")
                if prices[sym]["bid"] and prices[sym]["ask"]:
                    prices[sym]["mid"] = (
                        prices[sym]["bid"]
                        + (prices[sym]["ask"] - prices[sym]["bid"]) // 2
                    )
                elif prices[sym]["bid"]:
                    prices[sym]["mid"] = prices[sym]["bid"]
                else:
                    prices[sym]["mid"] = prices[sym]["ask"]


def printPrices():
    for sym in ["BOND", "VALBZ", "VALE", "GS", "MS", "WFC", "XLF"]:
        print(f'{sym}: {prices[sym]["bid"]} at {prices[sym]["ask"]}.')


def printPositions():
    for sym in ["BOND", "VALBZ", "VALE", "GS", "MS", "WFC", "XLF"]:
        print(f"{sym}: {positions[sym]}")


def initialize(hello_message):
    for message in hello_message["symbols"]:
        for sym in ["BOND", "VALBZ", "VALE", "GS", "MS", "WFC", "XLF"]:
            if message["symbol"] == sym:
                positions[sym] = message["position"]


class Dir(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ExchangeConnection:
    def __init__(self, args):
        self.message_timestamps = deque(maxlen=500)
        self.exchange_hostname = args.exchange_hostname
        self.port = args.port
        self.exchange_socket = self._connect(add_socket_timeout=args.add_socket_timeout)

        self._write_message({"type": "hello", "team": team_name.upper()})

    def read_message(self):
        """Read a single message from the exchange"""
        message = json.loads(self.exchange_socket.readline())
        if "dir" in message:
            message["dir"] = Dir(message["dir"])
        return message

    def send_add_message(
        self, order_id: int, symbol: str, dir: Dir, price: int, size: int
    ):
        """Add a new order"""
        print(f"Order {order_id}, Adding {symbol} {dir} {price} {size}")
        self._write_message(
            {
                "type": "add",
                "order_id": order_id,
                "symbol": symbol,
                "dir": dir,
                "price": price,
                "size": size,
            }
        )

    def send_convert_message(self, order_id: int, symbol: str, dir: Dir, size: int):
        """Convert between related symbols"""
        print(f"Order {order_id}, Converting {symbol} {dir} {size}")
        self._write_message(
            {
                "type": "convert",
                "order_id": order_id,
                "symbol": symbol,
                "dir": dir,
                "size": size,
            }
        )

    def send_cancel_message(self, order_id: int):
        """Cancel an existing order"""
        print(f"Canceling {order_id}")
        self._write_message({"type": "cancel", "order_id": order_id})

    def _connect(self, add_socket_timeout):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if add_socket_timeout:
            # Automatically raise an exception if no data has been recieved for
            # multiple seconds. This should not be enabled on an "empty" test
            # exchange.
            s.settimeout(5)
        s.connect((self.exchange_hostname, self.port))
        return s.makefile("rw", 1)

    def _write_message(self, message):
        json.dump(message, self.exchange_socket)
        self.exchange_socket.write("\n")

        now = time.time()
        self.message_timestamps.append(now)
        if len(
            self.message_timestamps
        ) == self.message_timestamps.maxlen and self.message_timestamps[0] > (now - 1):
            print(
                "WARNING: You are sending messages too frequently. The exchange will start ignoring your messages. Make sure you are not sending a message in response to every exchange message."
            )


def parse_arguments():
    test_exchange_port_offsets = {"prod-like": 0, "slower": 1, "empty": 2}

    parser = argparse.ArgumentParser(description="Trade on an ETC exchange!")
    exchange_address_group = parser.add_mutually_exclusive_group(required=True)
    exchange_address_group.add_argument(
        "--production", action="store_true", help="Connect to the production exchange."
    )
    exchange_address_group.add_argument(
        "--test",
        type=str,
        choices=test_exchange_port_offsets.keys(),
        help="Connect to a test exchange.",
    )

    # Connect to a specific host. This is only intended to be used for debugging.
    exchange_address_group.add_argument(
        "--specific-address", type=str, metavar="HOST:PORT", help=argparse.SUPPRESS
    )

    args = parser.parse_args()
    args.add_socket_timeout = True

    if args.production:
        args.exchange_hostname = "production"
        args.port = 25000
    elif args.test:
        args.exchange_hostname = "test-exch-" + team_name
        args.port = 25000 + test_exchange_port_offsets[args.test]
        if args.test == "empty":
            args.add_socket_timeout = False
    elif args.specific_address:
        args.exchange_hostname, port = args.specific_address.split(":")
        args.port = int(port)

    return args


if __name__ == "__main__":
    # Check that [team_name] has been updated.
    assert (
        team_name != "REPLACEME"
    ), "Please put your team name in the variable [team_name]."

    main()
