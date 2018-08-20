from merkato.merkato_config import load_config, get_config, create_exchange
from merkato.merkato import Merkato
from merkato.parser import parse
from merkato.utils.database_utils import no_merkatos_table_exists, create_merkatos_table, insert_merkato, get_all_merkatos, get_exchange, no_exchanges_table_exists, create_exchanges_table, drop_merkatos_table
from merkato.utils import generate_complete_merkato_configs, get_relevant_exchange
import sqlite3
import time
import pprint
from merkato.utils.diagnostics import visualize_orderbook
from gui.gui_utils import get_unmade_volume


# WARNING IS ONLY COMPATIBLE WITH BINANCE#
def sort_orders(order):
    return float(order['price'])


def find_problems(orders):
    for i, order in enumerate(orders):
        not_last_order = i != len(orders) -1
        if not_last_order:
            small = float(orders[i]['price'])
            big = float(orders[i + 1]['price'])
            small_big_div = big/small
            if small_big_div > 1 + (.0033 * 1.50):
                print('ERROR GAP')
                print('small', small)
                print('big', big)

    orders.sort(key=sort_orders, reverse=True)
    for i, order in enumerate(orders):
        not_last_order = i != len(orders) -1
        if not_last_order:
            big = float(orders[i]['price'])
            small = float(orders[i + 1]['price'])
            gap = (big-small)/small
            if gap < (.0033 / 2):
                print('ERROR DOUBLED UP')
                print('small', small)
                print('big', big)

def main():
    print("Merkato Alpha v0.1.1\n")


    if no_merkatos_table_exists():
        create_merkatos_table()

    if no_exchanges_table_exists():
        create_exchanges_table()

    merkatos = get_all_merkatos()
    for merkato in merkatos:
        exchange_class = get_relevant_exchange(merkato['exchange'])
        config = load_config(merkato['exchange'])
        exchange = exchange_class(config, merkato['alt'], merkato['base'])
        orders = exchange.client.get_open_orders(symbol=exchange.ticker, recvWindow=10000000)
        orders.sort(key=sort_orders)
        find_problems(orders)


if __name__ == '__main__':
    main()






# from merkato.utils.database_utils import get_all_merkatos, insert_merkato

# # merkato_args = {'exchange': 'bina', 'exchange_pair': 'binacoin=XMR_base=BTC', 'base': 'BTC', 'alt': 'XMR', 'spread': 0.015, 'profit_limit': 10, 'last_order': '5144153', 'first_order': '5131780', 'starting_price': 0.0167645, 'ask_reserved_balance': 7.749992, 'bid_reserved_balance': 0.128625, 'profit_margin': 0, 'base_partials_balance': 0, 'quote_partials_balance': 0, 'quote_volume': 0.912, 'base_volume': 0, 'step': 1.0033}
# # insert_merkato(**merkato_args)


# def add_profits_to_db():
# 	try:
# 			conn = sqlite3.connect('merkato.db')

# 	except Exception as e:
# 			print(str(e))
			
# 	finally:
# 			c = conn.cursor()
# 			c.execute('''ALTER TABLE merkatos ADD COLUMN base_profit float DEFAULT 0;''')
# 			c.execute('''ALTER TABLE merkatos ADD COLUMN quote_profit float DEFAULT 0;''')
# 			conn.commit()
# 			conn.close()

# add_profits_to_db()

# print('get_all', get_all_merkatos())
