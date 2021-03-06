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
class Merkato(object):
    def __init__(self, configuration, coin, base, spread, bid_reserved_balance, ask_reserved_balance,
                 user_interface=None, profit_margin=0, first_order='', starting_price=.018, increased_orders = 0,
                 step=1.0033, distribution_strategy=1, init_base_balance=0, init_quote_balance=0, base_profit=0, quote_profit=0,
                 buy_volume=0, sell_volume=0):

        validate_merkato_initialization(configuration, coin, base, spread)
        self.initialized = False
        UUID = configuration[EXCHANGE] + "coin={}_base={}".format(coin,base)
        self.mutex_UUID = UUID
        self.distribution_strategy = distribution_strategy
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

        merkato_does_exist = merkato_exists(self.mutex_UUID)

        if not merkato_does_exist:
            log.info("Creating New Merkato")

            self.cancelrange(ONE_SATOSHI, ONE_BITCOIN)

            total_pair_balances = self.exchange.get_balances()

            log.info("total pair balances: {}".format(total_pair_balances))

            allocated_pair_balances = get_allocated_pair_balances(configuration['exchange'], base, coin)
            check_reserve_balances(total_pair_balances, allocated_pair_balances, coin_reserve=ask_reserved_balance, base_reserve=bid_reserved_balance)

            insert_merkato(configuration[EXCHANGE], self.mutex_UUID, base, coin, spread, bid_reserved_balance, ask_reserved_balance, first_order, starting_price, init_base_balance=bid_reserved_balance, init_quote_balance=ask_reserved_balance, step=step)
            history = self.exchange.get_my_trade_history()

            log.debug('initial history: {}'.format(history))

            if len(history) > 0:
                log.debug('updating history first ID: {}'.format(history[0][ID]))
                new_last_order = history[0][ID]
                update_merkato(self.mutex_UUID, LAST_ORDER, new_last_order)
            self.distribute_initial_orders(total_base=bid_reserved_balance, total_alt=ask_reserved_balance)

        else:
            first_order = get_first_order(self.mutex_UUID)
            current_history = self.exchange.get_my_trade_history()
            last_order = get_last_order(self.mutex_UUID)
            new_history = get_new_history(current_history, last_order)
            self.rebalance_orders(new_history)

        self.initialized = True  # to avoid being updated before orders placed


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

    def rebalance_orders(self, new_txes):
        # This function places matching orders for all orders that filled fully since last

        factor = self.spread*self.profit_margin/2
        ordered_transactions = new_txes

        log.info('ordered transactions rebalanced: {}'.format(ordered_transactions))

        filled_orders = []
        market_orders = []
        
        if self.exchange.name != 'tux':
            self.exchange.process_new_transactions(ordered_transactions)

        for tx in ordered_transactions:
            log.info('Checking Transaction: {}'.format(tx))
            orderid = tx['orderId']
            tx_id   = tx[ID]
            price   = tx[PRICE]
            
            filled_amount = Decimal(tx['amount'])
            init_amount   = Decimal(tx['initamount'])

            if self.exchange.name == 'tux':
                partial_fill_info = self.exchange.get_my_order_info(orderid)
                init_amount = partial_fill_info['initamount']
                partial_fill = (partial_fill_info['state'] == 'closed')
            else:
                partial_fill = self.exchange.is_partial_fill(orderid) # todo implement for tux (binance done)

            total_amount = self.get_total_amount(init_amount, orderid)
            amount = Decimal(total_amount)*Decimal((1-factor))

            if partial_fill:
                self.handle_partial_fill(tx[TYPE], filled_amount, tx_id)
                continue

            if orderid in filled_orders:
                self.handle_is_in_filled_orders(tx)
                continue

            if tx[TYPE] == SELL:
                buy_price = Decimal(price) * ( 1  - self.spread)
                
                # Convert from the coin amount into base at the executed price
                base_amt = Decimal(price)*amount
                # Convert the base amount into coin at the final price
                coin_amt = base_amt/buy_price
                # This is the actual number we want to apply, not the original executed amount.
                amount = coin_amt


                if self.last_placed_UUID != buy_price + amount:
                    log.info("Found sell {} corresponding buy price: {} amount: {}".format(tx, buy_price, amount))
                    order_response = self.exchange.buy(amount, buy_price)
                else:
                    order_response = None

                self.update_sell_volume(filled_amount)

                if order_response == MARKET:
                    log.info('MARKET ORDER buy {}'.format(order_response))
                    market_orders.append((amount, buy_price, BUY, tx_id,))

                self.apply_filled_difference(tx, total_amount)

                is_round_trip = float(price) <= (float(self.starting_price) * float(1+(self.spread/2)))
                if is_round_trip:
                    log.info('Is round trip sell price: {}'.format(price))
                    self.base_profit += total_amount * Decimal(float(price)) * (self.spread - Decimal(self.exchange.fee *2))
                    update_merkato(self.mutex_UUID, BASE_PROFIT, float(self.base_profit))
                order_price = buy_price

            if tx[TYPE] == BUY:
                sell_price = Decimal(price) * ( 1  + self.spread)

                if self.last_placed_UUID != sell_price + amount:
                    log.info("Found buy {} corresponding sell price: {} amount: {}".format(tx, sell_price, amount))
                    order_response = self.exchange.sell(amount, sell_price)
                else:
                    order_response = None
                
                self.update_buy_volume(filled_amount, price)

                if order_response == MARKET:
                    log.info('MARKET ORDER sell {}'.format(order_response))
                    market_orders.append((amount, sell_price, SELL, tx_id))

                self.apply_filled_difference(tx, total_amount)

                is_round_trip = float(price) >= (float(self.starting_price) * float(1-(self.spread/2)))
                if is_round_trip:
                    log.info('Is round trip buy price: {}'.format(price))
                    self.quote_profit += total_amount * Decimal(self.spread - Decimal(self.exchange.fee *2))
                    update_merkato(self.mutex_UUID, QUOTE_PROFIT, float(self.quote_profit))
                order_price = sell_price

            if order_response != MARKET: 
                log.info('NOT MARKET ORDER')
                update_merkato(self.mutex_UUID, LAST_ORDER, tx[ID])

            filled_orders.append(orderid)
            
            first_order = get_first_order(self.mutex_UUID)
            no_first_order = first_order == ''

            if no_first_order:
                update_merkato(self.mutex_UUID, FIRST_ORDER, tx_id)
            self.last_placed_UUID = order_price + amount


        for order in market_orders:
            self.handle_market_order(*order)
        log.info('ending partials base: {} quote: {}'.format(self.base_partials_balance, self.quote_partials_balance))
        return ordered_transactions


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


    def decaying_bid_ladder(self, total_amount, step, start_price, hyper=False):
        '''total_amount is denominated in the base asset (BTC)
        '''
        # Abandon all hope, ye who enter here. This function uses black magic (math).

        scaling_log_factor = 2 if hyper == False else 1.5
        total_orders = floor(math.log(scaling_log_factor, step)) # 277 for a step of 1.0025
        scaling_factor = calculate_scaling_factor(scaling_log_factor, step, total_orders)

        current_order = 0
        amount = 0

        prior_reserve = self.bid_reserved_balance
        amount_for_main_orders = calculate_remaining_amount(total_amount, self.increased_orders, step, scaling_factor)
        while current_order < total_orders:
            step_adjusted_factor = Decimal(step**current_order)
            current_bid_price = Decimal(start_price/step_adjusted_factor)
            if current_order < self.increased_orders:
                current_bid_total = Decimal(total_amount/(scaling_factor * step_adjusted_factor)) * Decimal(1.5)
                current_bid_amount = Decimal(Decimal(total_amount)/(scaling_factor * step_adjusted_factor))/current_bid_price * Decimal(1.5)
                print('incresed', current_bid_total, 'current_bid_amount', current_bid_amount)
            else:
                current_bid_total =  Decimal(Decimal(amount_for_main_orders)/(scaling_factor * step_adjusted_factor))
                current_bid_amount = Decimal(Decimal(amount_for_main_orders)/(scaling_factor * step_adjusted_factor))/current_bid_price
            amount += current_bid_amount
            
            # TODO Create lock
            response = self.exchange.buy(current_bid_amount, current_bid_price)

            log.info('bid response {}'.format(response))

            self.remove_reserve(current_bid_total, BID_RESERVE) 
            # TODO Release lock
            
            current_order += 1
            self.avoid_blocking()

        log.info('allocated amount {}'.format(prior_reserve - self.bid_reserved_balance))


    def handle_is_in_filled_orders(self, tx):
        tx_type = tx[TYPE]
        filled_amount = Decimal(tx['amount'])
        price = Decimal(tx[PRICE])
        tx_id = tx[ID]
        if tx_type == BUY:
            self.quote_partials_balance += filled_amount
            update_merkato(self.mutex_UUID, 'quote_partials_balance', float(self.quote_partials_balance))
        if tx_type == SELL:
            self.base_partials_balance += filled_amount  * price
            update_merkato(self.mutex_UUID, 'base_partials_balance', float(self.base_partials_balance))
        log.info('{}, orderid in filled_orders filled_amount: {} tx_id: {} '.format(tx_type, filled_amount, tx_id))
        update_merkato(self.mutex_UUID, LAST_ORDER, tx_id)


    def distribute_bids(self, price, total_to_distribute):
        # Allocates your market making balance on the bid side, in a way that
        # will never be completely exhausted (run out).
        # total_to_distribute is in the base currency (usually BTC)
        if self.distribution_strategy == 1:
            log.info('Distribute Agressive Bids')
            self.decaying_bid_ladder(Decimal(total_to_distribute), self.step, price)
        elif self.distribution_strategy == 2:
            log.info('Distribute Neutral Bids')
            self.decaying_bid_ladder(Decimal(total_to_distribute/(4/3)), self.step, price)
            self.decaying_bid_ladder(Decimal(total_to_distribute/4), self.step, price/2)
        elif self.distribution_strategy == 3:
            log.info('Distribute Hyper-Aggressive Bids')
            self.decaying_bid_ladder(Decimal(total_to_distribute), self.step, price, True)


    def get_total_amount(self, init_amount, orderid):
        if self.exchange.name == "tux":
            return Decimal(init_amount)

        else:
            return self.exchange.get_total_amount(orderid) # todo unimplemented on tux


    def decaying_ask_ladder(self, total_amount, step, start_price, hyper=False):
        # Places an ask ladder from the start_price to 2x the start_price.
        # The last order in the ladder is half the amount of the first
        # order in the ladder. The amount allocated at each step decays as
        # orders are placed.
        # Abandon all hope, ye who enter here. This function uses black magic (math).

        scaling_log_factor = 2 if hyper == False else 1.5
        total_orders = floor(math.log(scaling_log_factor, step)) # 277 for a step of 1.0025
        scaling_factor = calculate_scaling_factor(scaling_log_factor, step, total_orders)

        current_order = 0
        amount = 0

        prior_reserve = self.ask_reserved_balance
        amount_for_main_orders = calculate_remaining_amount(total_amount, self.increased_orders, step, scaling_factor)
        while current_order < total_orders:
            step_adjusted_factor = Decimal(step**current_order)
            if current_order < self.increased_orders:
                current_ask_amount = total_amount/(scaling_factor * step_adjusted_factor) * Decimal(1.5)
            else:
                current_ask_amount = amount_for_main_orders /(scaling_factor * step_adjusted_factor)
            current_ask_price = start_price*step_adjusted_factor
            amount += current_ask_amount

            # TODO Create lock
            response = self.exchange.sell(current_ask_amount, current_ask_price)

            log.info('ask response {}'.format(response))

            self.remove_reserve(current_ask_amount, ASK_RESERVE) 
            # TODO Release lock

            current_order += 1
            self.avoid_blocking()

        log.info('allocated amount: {}'.format(prior_reserve - self.ask_reserved_balance))


    def distribute_asks(self, price, total_to_distribute):
        # Allocates your market making balance on the ask side, in a way that
        # will never be completely exhausted (run out).


        if self.distribution_strategy == 1:
            log.info('Distribute Aggressive Asks')
            self.decaying_ask_ladder(Decimal(total_to_distribute), self.step, price)
        elif self.distribution_strategy == 2:
            log.info('Distribute Neutral Asks')
            self.decaying_ask_ladder(Decimal(total_to_distribute/(4/3)), self.step, price)
            self.decaying_ask_ladder(Decimal(total_to_distribute/4), self.step, price * 2)
        elif self.distribution_strategy == 3:
            log.info('Distribute Hyper-Aggressive Asks')
            self.decaying_ask_ladder(Decimal(total_to_distribute), self.step, price, True)



    def distribute_initial_orders(self, total_base, total_alt):
        ''' TODO: Function comment
        '''
        current_price = (Decimal(self.exchange.get_highest_bid()) + Decimal(self.exchange.get_lowest_ask()))/2
        if self.user_interface:
            current_price = Decimal(self.user_interface.confirm_price(current_price))
        update_merkato(self.mutex_UUID, STARTING_PRICE, float(current_price))

        ask_start = current_price + current_price*self.spread/2
        bid_start = current_price - current_price*self.spread/2
        
        self.distribute_bids(bid_start, total_base)
        self.distribute_asks(ask_start, total_alt)


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

    def get_context_history(self):
        now = str(datetime.datetime.now().isoformat()[:-7].replace("T", " "))
        last_trade_price = self.exchange.get_last_trade_price()
        current_history = self.exchange.get_my_trade_history()
        first_order = get_first_order(self.mutex_UUID)
        new_history = get_new_history(current_history, first_order)

        self.exchange.process_new_transactions(new_history, context_only=True)

        context = {"price": (now, last_trade_price),
                "filled_orders": new_history,
                "open_orders": self.exchange.get_my_open_orders(context_formatted=True),
                "balances": self.exchange.get_balances(),
                "orderbook": self.exchange.get_all_orders(),
                "starting_price": self.starting_price,
                "starting_base": self.base_quote_balance,
                "starting_quote": self.init_quote_balance,
                "spread": self.spread,
                "step": self.step
                }
        
        return context


    def update(self):
        ''' TODO: Function comment
        '''
        log.info("Update entered")
        
        now = str(datetime.datetime.now().isoformat()[:-7].replace("T", " "))
        last_trade_price = self.exchange.get_last_trade_price()

        first_order = get_first_order(self.mutex_UUID)
        last_order  = get_last_order(self.mutex_UUID)
        
        current_history = self.exchange.get_my_trade_history()
        new_history = get_new_history(current_history, last_order)
        log.info('update new_history: {} first_order: {} last_order: {}'.format(new_history, first_order, last_order))
        new_transactions = []
        
        if len(new_history) > 0:
            log.info('we have new history')
            log.info("New transactions: {}".format(new_history))

            new_transactions = self.rebalance_orders(new_history)
            #self.merge_orders()
            # todo: Talk about whether merging 'close enough' orders is reasonable. 
            
        # context to be used for GUI plotting
        context = {"price": (now, last_trade_price),
                   "filled_orders": new_transactions,
                   "open_orders": self.exchange.get_my_open_orders(context_formatted=True),
                   "balances": self.exchange.get_balances(),
                   "orderbook": self.exchange.get_all_orders(),
                   "starting_price": self.starting_price,
                   "starting_base": self.init_base_balance,
                   "starting_quote": self.init_quote_balance,
                   "spread": self.spread,
                   "step": self.step
                   }
        
        return context


    def modify_settings(self, settings):
        # replace old settings with new settings
        pass


    def add_reserve(self):
        ''' TODO: Function comment
            This will be necessary when we remove orders lower on the books so we can place more orders higher.
        '''
        pass


    def remove_reserve(self, amount, type_of_reserve):
        ''' TODO: Function comment
        '''
        current_reserve_amount = self.ask_reserved_balance if type_of_reserve == ASK_RESERVE else self.bid_reserved_balance
        invalid_reserve_reduction = amount > current_reserve_amount
        
        if invalid_reserve_reduction:
            return False
        if type_of_reserve == ASK_RESERVE:
            new_amount = self.ask_reserved_balance - amount
            self.ask_reserved_balance = new_amount           
        elif type_of_reserve == BID_RESERVE:
            new_amount = self.bid_reserved_balance - amount
            self.bid_reserved_balance = new_amount

        update_merkato(self.mutex_UUID, type_of_reserve, float(new_amount))
        return True


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


    def avoid_blocking(self):
        ''' TODO: Function comment
        '''
        if self.user_interface:

            try:
                self.user_interface.app.update_idletasks()
                self.user_interface.app.update()

            except UnicodeDecodeError:

                log.info("Caught Scroll Error")

            except:
                pass

    def calculate_add_percentage(self, coin, amount_to_add):
        orderbook_sum = 0
        current_orders = self.exchange.get_my_open_orders()
        for order_id, order in current_orders.items():
            current_amount = order['amount']
            order_price = order['price']
            order_type = order['type']
            if coin == self.exchange.coin and order_type == SELL:
                orderbook_sum += current_amount
            elif coin == self.exchange.base and order_type == BUY:
                orderbook_sum += float(current_amount) * float(order_price)

        if coin == self.exchange.coin:
            old_reserves = self.ask_reserved_balance + self.quote_partials_balance
        else:
            old_reserves = self.bid_reserved_balance + self.base_partials_balance      
        total_amount = Decimal(orderbook_sum) + old_reserves
        return amount_to_add/total_amount

    def update_orders(self, coin, amount_to_add):
        print('amount_to_add', amount_to_add, 'coin', coin)
        amount_to_add = Decimal(float(amount_to_add))
        self.check_balances_available(coin, amount_to_add)
        add_percentage = self.calculate_add_percentage(coin, amount_to_add)
        if coin == self.exchange.coin:
            old_reserves = self.ask_reserved_balance + self.quote_partials_balance
        else:
            old_reserves = self.bid_reserved_balance + self.base_partials_balance
        current_orders = self.exchange.get_my_open_orders()
        for order_id, order in current_orders.items():
            current_amount = order['amount']
            order_type = order['type']
            order_price = Decimal(float(order['price']))
            amount_to_add = Decimal(float(current_amount * (1 + add_percentage)))
            if coin == self.exchange.coin and order_type == SELL:
                self.exchange.cancel_order(order['id'])
                self.exchange.sell(amount_to_add, order_price)
            if coin == self.exchange.base and order_type == BUY:
                self.exchange.cancel_order(order['id'])
                self.exchange.buy(amount_to_add, order_price)
        if coin == self.exchange.coin:
            print('old reserve balance', self.ask_reserved_balance)
            update_merkato(self.mutex_UUID, 'ask_reserved_balance', float(old_reserves * (1 + add_percentage)))
            self.ask_reserved_balance = Decimal(float(old_reserves * (1 + add_percentage)))
            print('new reserve balances', self.ask_reserved_balance)
        elif coin == self.exchange.base:
            print('old reserve balance', self.bid_reserved_balance )
            update_merkato(self.mutex_UUID, 'bid_reserved_balance', float(old_reserves * (1 + add_percentage)))
            self.bid_reserved_balance = Decimal(float(old_reserves * (1 + add_percentage)))
            print('new reserve balances', self.bid_reserved_balance)

    def check_balances_available(self, coin, amoount_to_add):
        total_pair_balances = self.exchange.get_balances()
        log.info("total pair balances: {}".format(total_pair_balances))
        allocated_pair_balances = get_allocated_pair_balances(self.exchange.name, self.exchange.base, self.exchange.coin)
        ask_reserved_balance = self.ask_reserved_balance if coin == 'BTC' else self.ask_reserved_balance + amoount_to_add
        bid_reserved_balance = self.bid_reserved_balance + amoount_to_add if coin == 'BTC' else self.bid_reserved_balance
        print('ask_reserved_balance', ask_reserved_balance, 'bid_reserved_balance', bid_reserved_balance)
        check_reserve_balances(total_pair_balances, allocated_pair_balances, coin_reserve=ask_reserved_balance, base_reserve=bid_reserved_balance)
