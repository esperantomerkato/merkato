import datetime
import math
from math import floor
import os
import time
import logging

from decimal import *
from merkato.constants import BUY, SELL, ID, PRICE, LAST_ORDER, ASK_RESERVE, BID_RESERVE, EXCHANGE, ONE_BITCOIN, STARTING_PRICE, \
    ONE_SATOSHI, FIRST_ORDER, MARKET, TYPE, BASE_PROFIT, QUOTE_PROFIT, INIT_BASE_BALANCE, INIT_QUOTE_BALANCE, SELL_VOLUME, BUY_VOLUME
from merkato.utils.database_utils import update_merkato, insert_merkato, merkato_exists, kill_merkato, get_merkato
from merkato.utils import validate_merkato_initialization, get_relevant_exchange, \
    get_allocated_pair_balances, check_reserve_balances, get_last_order, get_new_history, calculate_scaling_factor, \
    get_first_order, get_time_of_last_order, get_market_results, log_new_cointrackr_transactions, \
    calculate_remaining_amount, create_price_data

root_log = logging.getLogger("myapp")
log = root_log.getChild(__name__)
getcontext().prec = 8

#@log_all_methods
class Merkato_Manager(object):
    def __init__(self, configuration, coin, base, spread, bid_reserved_balance, ask_reserved_balance,
                 user_interface=None, profit_margin=0, first_order='', starting_price=.018, increased_orders = 0,
                 step=1.0033, distribution_strategy=1, init_base_balance=0, init_quote_balance=0, base_profit=0, quote_profit=0,
                 buy_volume=0, sell_volume=0):

        UUID = configuration[EXCHANGE] + "coin={}_base={}".format(coin,base)
        self.mutex_UUID = UUID
        self.spread = Decimal(spread)
        self.profit_margin = Decimal(profit_margin)
        self.starting_price = starting_price
        self.step = step
        self.increased_orders = increased_orders
        self.quote_profit = Decimal(quote_profit)
        self.base_profit = Decimal(base_profit)
        self.bid_reserved_balance = Decimal(float(bid_reserved_balance))
        self.ask_reserved_balance = Decimal(float(ask_reserved_balance))
        self.init_base_balance = init_base_balance
        self.init_quote_balance = init_quote_balance
        # The current sum of all partially filled orders
        self.base_partials_balance = 0
        self.quote_partials_balance = 0
        self.buy_volume = buy_volume
        self.sell_volume = sell_volume
        self.last_placed_UUID = '' #this assures that no faulty doubled up orders will be placed sequentially

        self.user_interface = user_interface

        exchange_class = get_relevant_exchange(configuration[EXCHANGE])
        self.exchange = exchange_class(configuration, coin=coin, base=base)


    def kill(self):
        ''' Cancels all orders and removes references to Merkato in database
        '''
        self.cancelrange(ONE_SATOSHI, ONE_BITCOIN) # Technically not all, but should be good enough
        kill_merkato(self.mutex_UUID)

    def update_buy_volume(self, raw_volume, price):
        finalized_volume = float(raw_volume) * float(price)
        self.buy_volume += finalized_volume
        update_merkato(self.mutex_UUID, BUY_VOLUME, self.buy_volume)

    def update_sell_volume(self, new_volume):
        self.sell_volume += float(new_volume)
        update_merkato(self.mutex_UUID, SELL_VOLUME, self.sell_volume)

    def apply_filled_difference(self, tx, total_amount):
        filled_difference = total_amount - Decimal(tx['amount'])
        log.info('apply_filled_difference tx: {} total_amount: {}'.format(tx, total_amount))
        tx_type = tx['type']
        if filled_difference > 0:
            if tx_type == SELL:
                self.base_partials_balance -= filled_difference * Decimal(tx[PRICE])
                update_merkato(self.mutex_UUID, 'base_partials_balance', float(self.base_partials_balance))
                log.info('apply_filled_difference base_partials_balance: {}'.format(self.base_partials_balance))
            if tx_type == BUY:
                self.quote_partials_balance -= filled_difference
                update_merkato(self.mutex_UUID, 'quote_partials_balance', float(self.quote_partials_balance))
                log.info('apply_filled_difference quote_partials_balance: {}'.format(self.quote_partials_balance))

    def handle_partial_fill(self, type, filled_qty, tx_id):
        # This was a buy, so we gained more of the quote asset. 
        # This was a partial fill, so the user's balance is increased by that amount. 
        # However, that amount is 'reserved' (will be placed on the books once the 
        # rest of the order is filled), and therefore is unavailable when creating new
        # Merkatos. Add this amount to a field 'quote_partials_balance'.
        log.info('handle_partial_fill type {} filledqty {} tx_id {}'.format(type, filled_qty, tx_id))
        update_merkato(self.mutex_UUID, LAST_ORDER, tx_id)
        if type == BUY:
            self.quote_partials_balance += filled_qty # may need a multiply by price
            update_merkato(self.mutex_UUID, 'quote_partials_balance', float(self.quote_partials_balance))

        elif type == SELL:
            self.base_partials_balance += filled_qty
            update_merkato(self.mutex_UUID, 'base_partials_balance', float(self.base_partials_balance))

        # 2. update the last order


    def handle_market_order(self, amount, price, type_to_place, tx_id):
        log.info('handle market order price: {}, amount: {}, type_to_place: {}'.format(price, amount, type_to_place))
        
        last_id_before_market = get_last_order(self.mutex_UUID)

        if type_to_place == BUY:
            self.exchange.market_buy(amount, price)

        elif type_to_place == SELL:
            self.exchange.market_sell(amount, price)        
                
        current_history = self.exchange.get_my_trade_history()
        if self.exchange.name != 'tux':
            self.exchange.process_new_transactions(current_history)
        market_history  = get_new_history(current_history, last_id_before_market)
        market_data     = get_market_results(market_history)


        # The sell gave us some BTC. The buy is executed with that BTC.
        # The market buy will get us X xmr in return. All of that xmr
        # should be placed at the original order's matching price.
        #
        # We need to do something here about the partials if it doesnt fully fill
        amount_executed = Decimal(market_data['amount_executed'])
        price_numerator = Decimal(market_data['price_numerator'])
        last_txid    = market_data['last_txid']
        log.info('market data: {}'.format(market_data))
        update_merkato(self.mutex_UUID, LAST_ORDER, last_txid)

        market_order_filled = amount <= amount_executed
        if market_order_filled:
            if type_to_place == BUY:
                price = price * Decimal(1 + self.spread)
                self.exchange.sell(amount_executed, price) # Should never market order
            elif type_to_place == SELL:
                price = price * Decimal(1 - self.spread)
                self.exchange.buy(amount_executed, price)
        else:
            log.info('handle_market_order: partials affected, amount: {} amount_executed: {}'.format(amount, amount_executed))
            if type_to_place == BUY:
                self.quote_partials_balance += amount_executed
                update_merkato(self.mutex_UUID, 'quote_partials_balance', float(self.quote_partials_balance))
                log.info('market buy partials after: {}'.format(self.quote_partials_balance))
            else:
                self.base_partials_balance += amount_executed * price_numerator
                update_merkato(self.mutex_UUID, 'base_partials_balance', float(self.base_partials_balance))
                log.info('market sell partials after {}'.format(self.base_partials_balance))
        # A market buy occurred, so we need to update the db with the latest tx

    def cancelrange(self, start, end):
        ''' TODO: Function comment
        '''
        open_orders = self.exchange.get_my_open_orders()
        print('open_orders', open_orders)
        for order in open_orders:
            print('canceling order', order)
            price = open_orders[order][PRICE]
            order_id = open_orders[order][ID]
            if Decimal(price) >= Decimal(start) and Decimal(price) <= Decimal(end):
                self.exchange.cancel_order(order_id)

                log.debug("price: {}".format(price))

                time.sleep(.3)

    def save_orderbook_to_txt(self):  
      open_orders = self.exchange.get_my_open_orders()
      new_orders = []
      if isinstance(open_orders,dict):
        for order in open_orders:
          new_orders.append(open_orders[order])
      else:
        for order in open_orders:
          order['type'] = order['side']
          order['amount'] = order['origQty']
          new_orders.append(order)
      open_orders = new_orders

      sorted_orders = sorted(open_orders, key=lambda x: float(x['price']))
      f= open(self.mutex_UUID +".txt","w+")
      for order in sorted_orders:
      	f.write("{} {} {}\n".format(order['type'], order['price'], order['amount']))
