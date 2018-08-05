import json
import requests
import time
from merkato.exchanges.exchange_base import ExchangeBase
from merkato.constants import MARKET, BUY, SELL
from binance.client import Client
from binance.enums import *
from math import floor
import logging
from decimal import *

log = logging.getLogger(__name__)
getcontext().prec = 8

XMR_AMOUNT_PRECISION = 3
XMR_PRICE_PRECISION = 6


class BinanceExchange(ExchangeBase):
    url = "https://api.binance.com"
    #todo coin
    def __init__(self, config, coin, base, password='password'):
        self.client = Client(config['public_api_key'], config['private_api_key'])
        self.limit_only = config['limit_only']
        self.retries = 5
        self.coin = coin
        self.base = base
        self.ticker = coin + base
        self.name = 'bina'

    def is_market_order(self, side, price):
        assert side in (BUY, SELL), "Invalid side {}".format(side)
        if side == BUY:
            if Decimal(self.get_lowest_ask()) < price:
                return True
        elif side == SELL:
            if Decimal(self.get_highest_bid()) > price:
                return True
        return False

    def _order(self, side, amount, price):
        log.info("Binance placing {} amount {} @{}".format(side, amount, price))
        amt_str = "{:0.0{}f}".format(amount, XMR_AMOUNT_PRECISION)
        price_str = "{:0.0{}f}".format(price, XMR_PRICE_PRECISION)
        side_const = SIDE_BUY if side == BUY else SIDE_SELL
        order = self.client.create_order(
            symbol=self.ticker,
            side=side_const,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=amt_str,
            price=price_str,
            recvWindow=10000000)
        return order


    def order(self, side, amount, price, limit_only=None):
        if limit_only is None:
            limit_only = self.limit_only
        attempt = 0
        while attempt < self.retries:
            if limit_only and self.is_market_order(side, price):
                log.info("SELL {} {} at {} on {} FAILED - would make a market order.".format(amount,self.ticker,
                                                                                             price, "binance"))
                return MARKET # Maybe needs failed or something

            try:
                success = self._order(side, amount, price)

                if success:
                    log.info("{} {} {} at {} on {}".format(side, amount, self.ticker, price, "binance"))
                    return success

                else:
                    log.info("{} {} {} at {} on {} FAILED - attempt {} of {}".format(side, amount, self.ticker, price,
                                                                                     "binance", attempt, self.retries))
                    attempt += 1
                    time.sleep(1)

            except Exception as e:  # TODO - too broad exception handling
                raise ValueError(e)


    def market_order(self, side, amount, price):
        return self.order(side, amount, price, limit_only=False)


    def get_all_orders(self):
        ''' Returns all open orders for the ticker XYZ (not BTC_XYZ)
            :param coin: string
        '''
        # TODO: Accept BTC_XYZ by stripping BTC_ if it exists

        orders = self.client.get_order_book(symbol=self.ticker)

        log.info("get_all_orders", orders)
        return orders


    def get_my_open_orders(self, context_formatted=False):
        ''' Returns all open orders for the authenticated user '''
                
        orders = self.client.get_open_orders(symbol=self.ticker, recvWindow=10000000)
        # orders is an array of dicts we need to transform it to an dict of dicts to conform to binance
        new_dict = {}
        for order in orders:
            id = order['orderId']
            new_dict[id] = order
            new_dict[id]['id'] = id
            if order['side'] == 'BUY':
                new_dict[id]['type'] = 'buy'
            else:
                new_dict[id]['type'] = 'sell'
            
            origQty = Decimal(float(order['origQty']))
            executedQty = Decimal(float(order['executedQty']))
            new_dict[id]['amount'] = origQty - executedQty
        return new_dict


    def cancel_order(self, order_id):
        ''' Cancels the order with the specified order ID
            :param order_id: string
        '''

        log.info("Cancelling order.")

        if order_id == 0:
            log.warning("Cancel order id 0. Bailing")
            return False

        return self.client.cancel_order(
            symbol=self.ticker,
            orderId=order_id)


    def get_ticker(self, coin=None):
        ''' Returns the current ticker data for the given coin. If no coin is given,
            it will return the ticker data for all coins.
            :param coin: string (of the format BTC_XYZ)
        '''

        ticker = self.client.get_ticker(symbol=coin)

        # if not coin:
        #     return json.loads(response.text)
        # response_json = json.loads(response.text)
        log.info(ticker)

        return ticker


    def get_24h_volume(self, coin=None):
        ''' Returns the 24 hour volume for the given coin.
            If no coin is given, returns for all coins.
            :param coin string (of the form BTC_XYZ where XYZ is the alt ticker)
        '''

        params = { "method": "get24hvolume" }
        response = requests.get(self.url, params=params)

        if not coin:
            return json.loads(response.text)

        response_json = json.loads(response.text)
        log.info(response_json[coin])

        return response_json[coin]


    def get_balances(self):
        ''' TODO Function Definition
        '''

        # also keys go unused, also coin...
        base_balance = self.client.get_asset_balance(asset=self.base, recvWindow=10000000)
        coin_balance = self.client.get_asset_balance(asset=self.coin, recvWindow=10000000)
        base = Decimal(base_balance['free']) + Decimal(base_balance['locked'])
        coin = Decimal(coin_balance['free']) + Decimal(coin_balance['locked'])

        log.info("Base balance: {}".format(base_balance))
        log.info("Coin balance: {}".format(coin_balance))

        pair_balances = {"base" : {"amount": {'balance': base},
                                   "name" : self.base},
                         "coin": {"amount": {'balance': coin},
                                  "name": self.coin},
                        }

        return pair_balances

    def process_new_transactions(self, new_txs, context_only=False):
        for trade in new_txs:

            if trade['isBuyer'] == True:
                trade['type'] = 'buy'
            else:
                trade['type'] = 'sell'

            if 'time' in trade:

                date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(floor(trade['time']/1000))))
                trade['date'] = date

            trade['total'] = Decimal(trade['price']) * Decimal(trade['qty'])
            trade['amount'] = Decimal(trade['qty'])
            if not context_only:
                order_info = self.client.get_order(symbol=self.ticker, orderId=trade['orderId'], recvWindow=10000000)
                trade['initamount'] = order_info['origQty']

    def get_my_trade_history(self, start=0, end=0):
        ''' TODO Function Definition
        '''
        log.info("Getting trade history...")
        # start_is_provided = start != 0 and start != ''
        # print('start', start)
        # if start_is_provided:
        #     trades = self.client.get_my_trades(symbol=self.ticker, fromId=int(start), recvWindow=10000000)
        # else:
        trades = self.client.get_my_trades(symbol=self.ticker, recvWindow=10000000)
        trades.reverse()
        return trades


    def get_last_trade_price(self):
        ''' TODO Function Definition
        '''
        return self.get_ticker(self.ticker)["lastPrice"]


    def get_lowest_ask(self):
        ''' TODO Function Definition
        '''
        return self.get_ticker(self.ticker)["askPrice"]


    def get_highest_bid(self):
        ''' TODO Function Definition
        '''
        return self.get_ticker(self.ticker)["bidPrice"]
    
    
    def is_partial_fill(self, order_id): 
        order_info = self.client.get_order(symbol=self.ticker, orderId=order_id, recvWindow=10000000)
        amount_placed = Decimal(order_info['origQty'])
        amount_executed = Decimal(order_info['executedQty'])
        log.info('Binance checking_is_partial_fill order_id: {} amount_placed: {} amount_executed: {}'.format(order_id, amount_placed, amount_executed))
        return amount_placed > amount_executed

    def get_total_amount(self, order_id):
        order_info = self.client.get_order(symbol=self.ticker, orderId=order_id, recvWindow=10000000)
        return Decimal(order_info['origQty'])
