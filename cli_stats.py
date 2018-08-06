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
        last_trade_price = exchange.get_last_trade_price()
        step = 1.0033
        spread = merkato['spread']
        initial_base = float(merkato['bid_reserved_balance']) * 4
        initial_quote = float(merkato['ask_reserved_balance']) * 4
        starting_price = merkato['starting_price']
        quote_volume = merkato['quote_volume']
        base_volume = merkato['base_volume']
        unmade_volume = get_unmade_volume(last_trade_price, starting_price, initial_base, initial_quote, spread, step)

        base_profit = (base_volume - unmade_volume['base']) * spread
        quote_profit = (quote_volume - unmade_volume['quote']) * spread

        print('STATS FOR {}'.format(merkato['exchange_pair']))
        print('Quote Volume: {} Base Volume: {}'.format(quote_volume, base_volume))
        print('Quote Profit: {} Base Profit: {}'.format(quote_profit, base_profit))

if __name__ == '__main__':
    main()