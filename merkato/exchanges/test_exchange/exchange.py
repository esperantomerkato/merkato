import hashlib
import hmac
import json
import math
import requests
import time
import random
import urllib.parse
from decimal import *
from merkato.exchanges.test_exchange.utils import apply_resolved_orders
from merkato.exchanges.exchange_base import ExchangeBase
from merkato.constants import BUY, SELL, PRICE, USER_ID, AMOUNT
from merkato.exchanges.test_exchange.orderbook import Orderbook
from merkato.exchanges.test_exchange.constants import test_asks, test_bids
from merkato.exchanges.tux_exchange.utils import translate_ticker

class TestExchange(ExchangeBase):
    def __init__(self, config, coin, base, user_id=20, accounts=None, price = 1, password='password'):
        self.coin = coin
        self.base = base
        self.name = "test"
        self.ticker = translate_ticker(coin=coin, base=base)
        self.orderbook = Orderbook(test_bids, test_asks)
        self.user_id = user_id
        self.USER_ID = user_id
        self.user_accounts = accounts if accounts else {}
        self.order_history = []
        self.price = price
        self.retries = 3
        self.limit_only = True
        self.DEBUG = 3
        self.history = []
        self.index = 0
        self.load_history() # For tuner
        
    def debug(self, level, header, *args):
        if level <= self.DEBUG:
            print("-"*10)
            print("{}---> {}:".format(level, header))
            for arg in args:
                print("\t\t" + repr(arg))
            print("-" * 10)


    def load_history(self):
        with open("price_data.txt") as infile:
            for line in infile:
                obj = json.loads(line)
                self.history.append(obj)
                print(obj)

    def _sell(self, amount, ask,):
        return self.orderbook.addAsk(self.user_id, amount, ask)



    def sell(self, amount, ask):
        if self.limit_only:
            # Get current highest bid on the orderbook
            # If ask price is lower than the highest bid, return.
            if self.get_highest_bid() > ask:
                self.debug(1, "sell","SELL {} {} at {} on {} FAILED - would make a market order.".format(amount, self.ticker, ask, "test"))
                # get highest price
                return True # Maybe needs failed or something
        try:
            return self._sell(amount, ask)
        except Exception as e:  # TODO - too broad exception handling
            self.debug(0, "sell", "ERROR", e)
            raise Exception(e)

                
    def _buy(self, amount, bid):
        return self.orderbook.addBid(self.user_id, amount, bid)


    def buy(self, amount, bid):
        if self.limit_only:
            # Get current lowest ask on the orderbook
            # If bid price is higher than the lowest ask, return.
            if self.get_lowest_ask() < bid:
                
                self.debug(1, "buy", "BUY {} {} at {} on {} FAILED - would make a market order.".format(amount, self.ticker, bid, "test"))
                return True # Maybe needs failed or something
        try:
            return self._buy(amount, bid)
        except Exception as e:  # TODO - too broad exception handling
            self.debug(0, "buy", "ERROR", e)
            raise Exception(e)
            return False


    def get_order_history(self, user_id):
        return self.order_history


    def generate_fake_data(self, delta_range=[-3,3]):
        #positive_or_negative = [-.2, .2]
        self.debug(3,"test exchange.py gen fake data", self.price)
        #self.price = abs(self.price * (1 + random.randint(*delta_range) / 100))  # percent walk of price, never < 0
        self.price = float(self.history[self.index]['price'][1])
        self.debug(3, "test exchange.py gen fake data: new price", self.price)
        new_orders = self.orderbook.generate_fake_orders(self.price)        
        if new_orders:
            self.order_history.extend(new_orders)
        self.index = self.index + 1


    def get_all_orders(self):
        ''' Returns all open orders for the current pair
        '''
        print('self.adfasdf', self.orderbook.bids)
        final_bids = list(map(lambda x: [x[PRICE], x['initamount']], self.orderbook.bids))
        final_asks = list(map(lambda x: [x[PRICE], x['initamount']], self.orderbook.asks))
        return {
            "asks": final_asks,
            "bids": final_bids
        }


    def get_my_open_orders(self, context_formatted = True):
        ''' Returns all open orders for the authenticated user '''
        # my_filtered_bids = list(filter(lambda order: order[USER_ID] == self.user_id, self.orderbook.bids))
        # my_filtered_asks = list(filter(lambda order: order[USER_ID] == self.user_id, self.orderbook.asks))
        # final_bids = list(map(lambda x: [x[PRICE], x[AMOUNT]], my_filtered_bids))
        # final_asks = list(map(lambda x: [x[PRICE], x[AMOUNT]], my_filtered_asks))
        # all_orders = {
        #     "asks": final_asks,
        #     "bids": final_bids
        # }
        my_filtered_bids = list(filter(lambda order: order[USER_ID] == self.user_id, self.orderbook.bids))
        my_filtered_asks = list(filter(lambda order: order[USER_ID] == self.user_id, self.orderbook.asks))
        combined_orders = []

        combined_orders.extend(my_filtered_asks)
        combined_orders.extend(my_filtered_bids)

        my_open_orders = {}

        for order in combined_orders:
            order_id = order['id']
            my_open_orders[order_id] = order
        return my_open_orders

    def get_my_trade_history(self):
        try:
            if not self.order_history:
                return []
            filtered_history = list(filter(lambda order: order[USER_ID] == self.USER_ID, self.order_history))
        except ValueError:
            filtered_history = []
        except:
            self.debug(3, "get_my_trade_history", self.order_history, self.user_id)
            raise
        print("Filtered History:", filtered_history)
        filtered_history.reverse()
        return filtered_history


    def cancel_order(self, order_id):
        ''' Cancels the order with the specified order ID
            :param order_id: string
        '''
        # Broken, TODO
        my_filtered_bids = list(filter(lambda order: order[USER_ID] == self.user_id and order['orderId'] != order_id, self.orderbook.bids))
        my_filtered_asks = list(filter(lambda order: order[USER_ID] == self.user_id and order['orderId'] != order_id, self.orderbook.asks))
        self.orderbook.asks = my_filtered_asks
        self.orderbook.bids = my_filtered_bids

    def get_ticker(self):
        ''' Returns the current ticker data for the target coin.
        '''
        # Broken, TODO
        return ""


    def get_24h_volume(self):
        ''' Returns the 24 hour volume for the target coin.
        '''
        # Broken, TODO
        return ""


    def get_balances(self):
        pair_balances = {"base" : {"amount": {"balance":10000000000},
                                   "name" : self.base},
                         "coin": {"amount": {"balance":10000000000},
                                  "name": self.coin},
                        }

        return pair_balances


    def process_new_transactions(self, new_txs, context_only=False):
        # New, possibly complete
        pass


    def is_partial_fill(self, order_id):
        # New, should be complete
        return False


    def get_total_amount(self, order_id):
        # New, possibly complete
        order_info = self.get_order_info(order_id)
        return Decimal(order_info['amount'])


    def get_order_info(self, order_id):
        # New, possibly complete
        order_info = self.orderbook.get_order(order_id)
        return order_info


    def get_last_trade_price(self):
        if self.index < len(self.history):
            self.generate_fake_data()
            return self.price


    def get_lowest_ask(self):
        asks_exist = len(self.orderbook.asks) > 0
        if not asks_exist:
            return test_asks[0][PRICE]
        return self.orderbook.asks[0][PRICE]


    def get_highest_bid(self):
        bids_exist = len(self.orderbook.bids) > 0
        if not bids_exist:
            return test_bids[0][PRICE]
        return self.orderbook.bids[0][PRICE]
