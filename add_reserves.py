from merkato.utils.database_utils import update_merkato

UUID = configuration[EXCHANGE] + "coin={}_base={}".format('XMR','BTC')

def sum_orderbook():
	# get_my_open_orders
	# iterate over orders
	# 	add funds to order properly
	# return amounts

def get_reserves(ticker_pair, coin)
	# get reserve from merkato and add the relevant base_partials
	# return it

def calculate_add_percentage(ticker_pair, coin, amount_to_add):
	orderbook_sum = sum_orderbook(ticker_pair, coin)
	reserve_sum = get_reserves(ticker_pair, coin)
	total_amount = orderbook_sum + reserve_sum
	return amount_to_add/total_amount

def update_orders(ticker_pair, coin, amount_to_add)
	add_percentage = calculate_add_percentage(ticker_pair, coin, amount_to_add)
	old_reserves = get_reserves(ticker_pair, coin)
	for order in current_orders:
		current_amount = order['amount']
		order_type = order['type']
		order_price = order['price']
		amount_to_add = current_amount * (1 + add_percentage)
		cancel_order(order['id'])
		place_order(amount_to_add, order_price)
		if coin != 'BTC':
			update_merkato(UUID, 'ask_reserved_balance', old_reserves * (1 + add_percentage))
			#update coin reserves with old_reserves * (1 + add_percentage)
		else:
			update_merkato(UUID, 'bid_reserved_balance', old_reserves * (1 + add_percentage))
			#update base reserves



def cancel_order(order_id):
	pass

def place_order(amount, price)
	pass