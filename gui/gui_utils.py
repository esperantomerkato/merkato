import math
from math import floor
from merkato.constants import BUY, SELL

def get_expected_balances(market_price, starting_price, start_base, start_quote, spread, step):
    scaling_factor = 0
    total_orders = floor(math.log(2, step)) # 277 for a step of 1.0025
    current_order = 0

    while current_order < total_orders:
        scaling_factor += 1/(step**current_order)
        current_order += 1

    current_order = 0
    expected_base = start_base
    expected_quote = start_quote

    start_base = start_base/2
    start_quote = start_quote/2
    market_starting_price_delta = market_price - starting_price

    if market_starting_price_delta > 0:
        while current_order < total_orders:
            step_adjusted_factor = step**current_order
            current_ask_amount = start_quote/(scaling_factor * step_adjusted_factor)
            current_ask_price = starting_price*step_adjusted_factor
            # print('current_ask_price', current_ask_price)
            expected_base += current_ask_amount * current_ask_price
            expected_quote -= current_ask_amount
            if current_ask_price > market_price:
                break
            current_order += 1
    else:
        while current_order < total_orders:
            step_adjusted_factor = step**current_order
            current_bid_price = starting_price/step_adjusted_factor
            # print('current_bid_price', current_bid_price)
            current_bid_amount = start_base/(scaling_factor * step_adjusted_factor)/current_bid_price
            expected_base -= current_bid_amount * current_bid_price
            expected_quote += current_bid_amount
            if current_bid_price < market_price:
                break
            current_order += 1
        
    if current_order != total_orders:
        return (expected_base, expected_quote)

    start_base = start_base/2
    start_quote = start_quote/2
    current_order = 0

    if market_starting_price_delta > 0:
        starting_price = current_ask_price
        while current_order < total_orders:
            step_adjusted_factor = step**current_order
            current_ask_amount = start_quote/(scaling_factor * step_adjusted_factor)
            current_ask_price = starting_price*step_adjusted_factor
            # print('current_ask_price', current_ask_price)
            expected_base += current_ask_amount * current_ask_price
            expected_quote -= current_ask_amount
            if current_ask_price > market_price:
                break
            current_order += 1
    else:
        starting_price = current_bid_price
        while current_order < total_orders:
            step_adjusted_factor = step**current_order
            current_bid_price = starting_price/step_adjusted_factor
            # print('current_bid_price', current_bid_price)
            current_bid_amount = start_base/(scaling_factor * step_adjusted_factor)/current_bid_price
            expected_base -= current_bid_amount * current_bid_price
            expected_quote += current_bid_amount
            if current_bid_price < market_price:
                break
            current_order += 1
    return (expected_base, expected_quote)


def get_orderbook_balances(current_orders):
    base_sum = 0
    quote_sum = 0
    for order_id, order in current_orders.items():
        current_amount = order['amount']
        order_price = order['price']
        order_type = order['type']
        if order_type == SELL:
            quote_sum += current_amount
        elif order_type == BUY:
            base_sum += float(current_amount) * float(order_price)
    return (float(base_sum), float(quote_sum))

def get_unmade_volume(market_price, starting_price, start_base, start_quote, spread, step):
  scaling_factor = 0
  total_orders = floor(math.log(2, step)) # 277 for a step of 1.0025
  current_order = 0

  while current_order < total_orders:
      scaling_factor += 1/(step**current_order)
      current_order += 1

  current_order = 0
  summed_base = 0
  summed_quote = 0
  
  start_base = start_base/2
  start_quote = start_quote/2
  market_starting_price_delta = float(market_price) - float(starting_price)
  starting_ask_price = starting_price*(1+(spread/2))
  starting_bid_price = starting_price*(1-(spread/2))

  if market_starting_price_delta > 0:
    while current_order < total_orders:
      step_adjusted_factor = step**current_order
      current_ask_amount = round(start_quote/(scaling_factor * step_adjusted_factor),3)
      current_ask_price = starting_ask_price*step_adjusted_factor
      if current_ask_price > float(market_price):
        break
      summed_base += current_ask_amount * current_ask_price
      current_order += 1
  else:
    while current_order < total_orders:
      step_adjusted_factor = step**current_order
      current_bid_price = starting_bid_price/step_adjusted_factor
      if current_bid_price < float(market_price):
        break
      current_bid_amount = round(float(start_base)/(scaling_factor * step_adjusted_factor),3)/current_bid_price

      summed_quote += current_bid_amount
      current_order += 1
    
  #broken for more than doubling/halving
  return { 'base':summed_base, 'quote': summed_quote }