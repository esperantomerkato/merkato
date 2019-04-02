from merkato.exchanges.kraken_exchange.constants import DEPTH, ADD_ORDER, RESULT, OPEN_ORDERS, REF_ID, DESCRIPTION, CANCEL_ORDER, TICKER, TRADES_HISTORY, QUERY_ORDERS, \
    CRYPTO_ASSETS, TRADES, OPEN, VOL, VOLUME_EXECUTED

from math import floor
import sqlite3

from binance.enums import *
from binance.client import Client
from binance.enums import *
import krakenex

client = Client()

base_balance = client.get_asset_balance(asset='BTC', recvWindow=10000000)
coin_balance = client.get_asset_balance(asset='XMR', recvWindow=10000000)
history = client.get_my_trades(symbol='XMRBTC', recvWindow=10000000, fromId=5419788)
history_2 = client.get_my_trades(symbol='XMRBTC', recvWindow=10000000, fromId=7294366)
# history_3 = client.get_my_trades(symbol='XMRBTC', recvWindow=10000000, fromId=9113531)
# print('history', history_3[0], history_3[len(history_3)-1])
history += history_2
date_obj = { 
	'sep': {
		'btc': 0,
		'xmr': 0
	}, 	
	'oct': {
		'btc': 0,
		'xmr': 0
	}, 
	'nov': {
		'btc': 0,
		'xmr': 0
	}, 
	'dec': {
		'btc': 0,
		'xmr': 0
	}, 
	'jan': {
		'btc': 0,
		'xmr': 0
	}, 
}



def resolve_stack(amount, price, date, isBuyer):
	empty_stack = len(stack) == 0
	if empty_stack:
		stack.insert(0, { 'amt': amount, 'price': price, 'isBuyer': isBuyer })

	stack_same_as_order = stack[0]['isBuyer'] == isBuyer
	if stack_same_as_order:
		stack.insert(0, { 'amt': amount, 'price': price, 'isBuyer': isBuyer })
	elif not stack_same_as_order:
		start_resolve_order(price, amount, date, isBuyer)

def start_resolve_order(price, amount, date, isBuyer):
		cur_stack_amount = float(stack[0]['amt'])
		cur_stack_price = stack[0]['price']
		amount_to_resolve = amount if amount < cur_stack_amount else cur_stack_amount
		smaller_price = price if price < cur_stack_price else cur_stack_price
		spread = abs(float(cur_stack_price) - float(price))/float(smaller_price)
		profit = amount_to_resolve * spread
		date_obj[date]['xmr'] += profit
		stack[0]['amt'] -= amount_to_resolve
		if stack[0]['amt'] == 0:
			stack.pop(0)
		if amount > amount_to_resolve:
			if len(stack) > 0:
				start_resolve_order(price, amount - amount_to_resolve, date, isBuyer)
			else:
				stack.append({ 'amt': amount - amount_to_resolve, 'price': price, 'isBuyer': isBuyer })

stack = []
sep_1 = 1535760000000
oct_1 = 1538352000000
nov_1 = 1541030400000
dec_1 = 1543622400000
jan_1 = 1546300800000
feb_1 = 1548979200000
for tx in history:
	time = tx['time']
	amount = float(tx['qty'])
	price = float(tx['price'])
	if time >= sep_1 and time <= oct_1:
		resolve_stack(amount, price, 'sep', tx['isBuyer'])
	elif time >= oct_1 and time <= nov_1:
		resolve_stack(amount, price, 'oct', tx['isBuyer'])
	elif time >= nov_1 and time <= dec_1:
		resolve_stack(amount, price, 'nov', tx['isBuyer'])
	elif time >= dec_1 and time <= jan_1:
		resolve_stack(amount, price, 'dec', tx['isBuyer'])
	elif time >= jan_1 and time <= feb_1:
		resolve_stack(amount, price, 'jan', tx['isBuyer'])

print('dateobj', date_obj)