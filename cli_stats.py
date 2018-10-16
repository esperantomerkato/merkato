from merkato.merkato_config import load_config, get_config, create_exchange
from merkato.merkato import Merkato
from merkato.parser import parse
from merkato.utils.database_utils import no_merkatos_table_exists, create_merkatos_table, insert_merkato, get_all_merkatos, get_exchange, no_exchanges_table_exists, create_exchanges_table, drop_merkatos_table
from merkato.utils import generate_complete_merkato_configs, get_relevant_exchange, load_exchange_by_merkato
import sqlite3
import time
import pprint
from merkato.utils.diagnostics import visualize_orderbook
from merkato.constants import round_trip_exchange_fees

def main():
    print("Merkato Alpha v0.1.1\n")


    if no_merkatos_table_exists():
        create_merkatos_table()

    if no_exchanges_table_exists():
        create_exchanges_table()

    merkatos = get_all_merkatos()
    for merkato in merkatos:
        exchange = load_exchange_by_merkato(merkato)
        initial_base = float(merkato['init_base_balance'])
        initial_quote = float(merkato['init_quote_balance'])

        absolute_balances = exchange.get_balances()
        current_used_quote = float(exchange.get_balance(merkato['alt'])['locked'])
        current_used_base = float(exchange.get_balance(merkato['base'])['locked'])
        absolute_base = float(absolute_balances['base']['amount']['balance'])
        absolute_quote = float(absolute_balances['coin']['amount']['balance'])

        base_profit = float(merkato['base_profit'])
        quote_profit = float(merkato['quote_profit'])

        print('STATS FOR {}'.format(merkato['exchange_pair']))
        print('Initial Base: {} Initial Quote: {} '.format(initial_base, initial_quote))
        print('(INCLUDES UNUSED FUNDS) Current Base Total: {} Current Quote Total: {}'.format(absolute_base, absolute_quote))
        print('(DOES NOT INCLUDE UNUSED FUNDS) Absolute Base Diff: {} Absolute Quote Diff: {}'.format(current_used_base - initial_base, current_used_quote - initial_quote))
        print('MarketMaking Base Profit: {} Quote Profit: {}'.format(base_profit, quote_profit))


if __name__ == '__main__':
    main()