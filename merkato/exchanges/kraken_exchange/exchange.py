import json
import requests
import time
from merkato.exchanges.exchange_base import ExchangeBase
from merkato.constants import MARKET, SELL, BUY, LIMIT, ID
from merkato.exchanges.kraken_exchange.constants import DEPTH, ADD_ORDER, RESULT, OPEN_ORDERS, REF_ID, DESCRIPTION, CANCEL_ORDER, TICKER, TRADES_HISTORY, QUERY_ORDERS
import krakenex
from math import floor
import logging
from decimal import *
from requests.adapters import HTTPAdapter

s = requests.Session()
s.mount('http', HTTPAdapter(max_retries=3))
s.mount('https', HTTPAdapter(max_retries=3))
log = logging.getLogger(__name__)
getcontext().prec = 8

XMR_AMOUNT_PRECISION = 3
XMR_PRICE_PRECISION = 6


class KrakenExchange(ExchangeBase):
    def __init__(self, config, coin, base, password='password'):
        self.client = krakenex.API(config['public_api_key'], config['private_api_key'])
        self.limit_only = config['limit_only']
        self.retries = 5
        self.coin = coin
        self.base = base
        self.ticker = coin + 'XBT'
        self.name = 'Kraken'

    def _sell(self, amount, ask):
        ''' Places a sell for a number of an asset at the indicated price (0.00000503 for example)
            :param amount: string
            :param ask: float
            :param ticker: string
        '''
        print('amount', amount, 'ask', ask)
        amt_str = "{:0.0{}f}".format(amount, XMR_AMOUNT_PRECISION)
        ask_str = "{:0.0{}f}".format(ask, XMR_PRICE_PRECISION)
        log.info("{} placing sell ask: {} amount: {}".format(self.name, ask_str, amt_str))
        order = self.client.query_private(ADD_ORDER,
            {'pair': self.ticker,
            'ordertype': LIMIT,
            'type': SELL,
            'volume':amt_str,
            'price': ask_str})[RESULT]
        return order


    def sell(self, amount, ask):
        attempt = 0
        while attempt < self.retries:
            if self.limit_only:
                # Get current highest bid on the orderbook
                # If ask price is lower than the highest bid, return.

                if Decimal(float(self.get_highest_bid())) > ask:
                    log.info("SELL {} {} at {} on {} FAILED - would make a market order.".format(amount,self.ticker, ask, self.name))
                    return MARKET # Maybe needs failed or something

            try:
                success = self._sell(amount, ask)

                if success:
                    log.info("SELL {} {} at {} on {}".format(amount, self.ticker, ask, self.name))
                    return success

                else:
                    log.info("SELL {} {} at {} on {} FAILED - attempt {} of {}".format(amount, self.ticker, ask, self.name, attempt, self.retries))
                    attempt += 1
                    time.sleep(1)

            except Exception as e:  # TODO - too broad exception handling
                raise ValueError(e)


    def _buy(self, amount, bid):
        ''' Places a buy for a number of an asset at the indicated price (0.00000503 for example)
            :param amount: string
            :param bid: float
            :param ticker: string
        '''
        amt_str = "{:0.0{}f}".format(amount, XMR_AMOUNT_PRECISION)
        bid_str = "{:0.0{}f}".format(bid, XMR_PRICE_PRECISION)
        info = self.client.get_symbol_info(symbol=self.ticker)
        log.info("Bina placing buy bid: {} amount: {}".format(bid_str, amt_str))
        order = self.client.query_private(ADD_ORDER,
            {'pair': self.ticker,
            'ordertype': LIMIT,
            'type': BUY,
            'volume':amt_str,
            'price': bid_str})[RESULT]
        return order


    def buy(self, amount, bid):
        attempt = 0
        bid_amount = amount
        while attempt < self.retries:
            if self.limit_only:
                # Get current lowest ask on the orderbook
                # If bid price is higher than the lowest ask, return.

                if Decimal(float(self.get_lowest_ask())) < bid:

                    log.info("BUY {} {} at {} on {} FAILED - would make a market order.".format(amount, self.ticker, bid, self.name))
                    return MARKET # Maybe needs failed or something

            try:
                success = self._buy(bid_amount, bid)
                if success:
                    log.info("BUY {} {} at {} on {}".format(bid_amount, self.ticker, bid, self.name))
                    return success

                else:
                    log.info("BUY {} {} at {} on {} FAILED - attempt {} of {}".format(amount, self.ticker, bid, self.name, attempt, self.retries))
                    attempt += 1
                    time.sleep(1)

            except Exception as e:  # TODO - too broad exception handling
                raise ValueError(e)

    def market_buy(self, amount, bid):
        attempt = 0
        bid_amount = amount
        while attempt < self.retries:
            try:
                success = self._buy(bid_amount, bid)
                if success:
                    log.info("BUY {} {} at {} on {}".format(bid_amount, self.ticker, bid, self.name))
                    return success

                else:
                    log.info("BUY {} {} at {} on {} FAILED - attempt {} of {}".format(amount, self.ticker, bid, self.name, attempt, self.retries))
                    attempt += 1
                    time.sleep(1)

            except Exception as e:  # TODO - too broad exception handling
                raise ValueError(e)

    def market_sell(self, amount, ask):
        attempt = 0
        try:
            success = self._sell(amount, ask)

            if success:
                log.info("SELL {} {} at {} on {}".format(amount, self.ticker, ask, self.name))
                return success

            else:
                log.info("SELL {} {} at {} on {} FAILED - attempt {} of {}".format(amount, self.ticker, ask, self.name, attempt, self.retries))
                attempt += 1
                time.sleep(1)

        except Exception as e:  # TODO - too broad exception handling
            raise ValueError(e)


    def get_all_orders(self):
        ''' Returns all open orders for the ticker XYZ (not BTC_XYZ)
            :param coin: string
        '''
        # TODO: Accept BTC_XYZ by stripping BTC_ if it exists
        
        orders = self.client.query_public(DEPTH, {'pair': self.ticker})[RESULT]

        log.info("get_all_orders", orders)
        return orders


    def get_my_open_orders(self, context_formatted=False):
        ''' Returns all open orders for the authenticated user '''
                
        orders = self.client.query_private(OPEN_ORDERS, {'oflags': 'viqc'})[RESULT]
        # orders is an array of dicts we need to transform it to an dict of dicts to conform to binance
        new_dict = {}
        for order_id in orders:
            order = orders[order_id]
            order_data = orders[order_id][DESCRIPTION]
            id = order[REF_ID]
            new_dict[id] = order_data
            new_dict[id][ID] = order_id
            
            origQty = Decimal(float(order['vol']))
            executedQty = Decimal(float(order['vol_exec']))
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

        return self.client.query_private(CANCEL_ORDER,
            {   'pair':self.ticker,
                'orderId': order_id})[RESULT]


    def get_ticker(self, coin=None):
        ''' Returns the current ticker data for the given coin. If no coin is given,
            it will return the ticker data for all coins.
            :param coin: string (of the format BTC_XYZ)
        '''
        attempts = 0
        while attempts < 4:
            try:
                result = self.client.query_public(TICKER, {'pair': self.ticker})[RESULT]
                log.info(result)
                for ticker_data in result.values():
                    return ticker_data
            except Exception as e:
                print('Error getting trade price {}'.format(e))
                print('Trying again attempt {}'.format(attempts + 2))
                attempts += 1


    def get_24h_volume(self, coin=None):
        ''' Returns the 24 hour volume for the given coin.
            If no coin is given, returns for all coins.
            :param coin string (of the form BTC_XYZ where XYZ is the alt ticker)
        '''

        return self.get_ticker()['v']


    def get_balances(self):
        ''' TODO Function Definition
        '''

        # also keys go unused, also coin...
        balances = self.client.query_private('Balance')[RESULT]
        coin_balance = balances[self.coin]
        base_balance = balances[self.base]

        log.info("Base balance: {}".format(base_balance))
        log.info("Coin balance: {}".format(coin_balance))

        pair_balances = {"base" : {"amount": {'balance': base_balance},
                                   "name" : self.base},
                         "coin": {"amount": {'balance': coin_balance},
                                  "name": self.coin},
                        }

        return pair_balances

    def process_new_transactions(self, new_txs, context_only=False):
        for trade in new_txs:

            if 'time' in trade:

                date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(floor(trade['time']/1000))))
                trade['date'] = date

            trade['total'] = Decimal(trade['price']) * Decimal(trade['qty'])
            trade['amount'] = Decimal(trade['qty'])
            if not context_only:
                order_info = self.client.query_private(QUERY_ORDERS, {'oflags': 'viqc', 'txid': [trade['orderId']]})[RESULT][trade['orderId']]
                trade['initamount'] = order_info['vol']


    def get_my_trade_history(self, start=0, end=0):
        ''' TODO Function Definition
        '''
        log.info("Getting trade history...")
        # start_is_provided = start != 0 and start != ''
        # print('start', start)
        # if start_is_provided:
        #     trades = self.client.get_my_trades(symbol=self.ticker, fromId=int(start), recvWindow=10000000)
        # else:
        trades = self.client.query_private(TRADES_HISTORY)
        trade_array = []
        for trade_id in trades:
            trade = trades[trade_id]
            trade[ID] = trade_id
            trade['orderId'] = trade['ordertxid'] 
            trade['qty'] = float(trade['vol']) * float(trade['price'])
            trade_array.append(trade)
        trade_array.reverse()
        return trade_array


    def get_last_trade_price(self):
        ''' TODO Function Definition
        '''
        return self.get_ticker()["c"][0]


    def get_lowest_ask(self):
        ''' TODO Function Definition
        '''
        return self.get_ticker()["a"][0]


    def get_highest_bid(self):
        ''' TODO Function Definition
        '''
        return self.get_ticker()["b"][0]
    

    def get_total_amount(self, order_id):
        order_info = self.client.get_order(symbol=self.ticker, orderId=order_id, recvWindow=10000000)
        return Decimal(order_info['origQty'])

    def is_partial_fill(self, order_id): 
        order_info = self.client.get_order(symbol=self.ticker, orderId=order_id, recvWindow=10000000)
        amount_placed = Decimal(order_info['origQty'])
        amount_executed = Decimal(order_info['executedQty'])
        log.info('Binance checking_is_partial_fill order_id: {} amount_placed: {} amount_executed: {}'.format(order_id, amount_placed, amount_executed))
        return amount_placed > amount_executed
