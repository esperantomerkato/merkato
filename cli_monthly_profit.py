from merkato.merkato_config import load_config, get_config, create_exchange
from merkato.merkato import Merkato
from merkato.parser import parse
from merkato.utils.database_utils import no_merkatos_table_exists, create_merkatos_table, insert_merkato, get_all_merkatos, get_exchange, no_exchanges_table_exists, create_exchanges_table, drop_merkatos_table, update_merkato
from merkato.utils import generate_complete_merkato_configs, get_relevant_exchange
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
        exchange_name = merkato['exchange']
        exchange_class = get_relevant_exchange(exchange_name)
        round_trip_fee = round_trip_exchange_fees[exchange_name]
        config = load_config(exchange_name)
        exchange = exchange_class(config, merkato['alt'], merkato['base'])
        last_trade_price = exchange.get_last_trade_price()
        spread = merkato['spread']
        initial_base = float(merkato['bid_reserved_balance']) * 4 + float(merkato['base_profit'])
        initial_quote = float(merkato['ask_reserved_balance']) * 4 + float(merkato['quote_profit'])
        quote_volume = merkato['quote_volume']
        base_volume = merkato['base_volume']
        UUID = merkato['exchange_pair']

        base_profit = (base_volume) * (spread - round_trip_fee)
        quote_profit = (quote_volume) * (spread - round_trip_fee)

        print('STATS FOR {}'.format(UUID))
        print('Quote Volume: {} Base Volume: {}'.format(quote_volume, base_volume))
        print('Quote Profit: {} Base Profit: {}'.format(quote_profit, base_profit))
        relative_base_prof = str((base_profit/initial_base) * 100) + '%'
        relative_quote_prof = str((quote_profit/initial_quote ) * 100) + '%'
        print('Relative Quote Profit: {} Relative Base Profit: {}'.format(relative_quote_prof, relative_base_prof))

        print('*WARNING THIS RESET SHOULD ONLY BE DONE ON AT THE END OF EVERY MONTH, AND WILL REMOVE ALL CURRENT VOLUME*')
        print('*ANY FEE SHOULD BE REMOVED FROM THE ACCOUNT IMMIEDIATELY AFTER*')
        choice_to_continue = input('Would you like to continue? (y/n)')
        should_continue = choice_to_continue == 'y' or choice_to_continue == 'Y'
        if should_continue:
            print('The base profit that will be added to the account is {}'.format(base_profit * .7))
            print('The quote profit that will be added to the account is {}'.format(quote_profit * .7))
            print('The starting_price that will be updated for the merkato is {}'.format(last_trade_price))
            finalize_choice = input('Do these numbers look correct?(y/n)')
            should_execute = finalize_choice == 'y' or choice_to_continue == 'Y'
            if should_execute:
                new_base_profit = merkato['base_profit'] + (base_profit * .7)
                new_quote_profit = merkato['quote_profit'] + (quote_profit * .7)
                update_merkato(UUID, 'base_profit', new_base_profit)
                update_merkato(UUID, 'quote_profit', new_quote_profit)
                update_merkato(UUID, 'base_volume', 0)
                update_merkato(UUID, 'quote_volume', 0)
                update_merkato(UUID, 'starting_price', last_trade_price)
                print('Profits updated new base:{} new quote: {} new starting_price: {}'.format(new_base_profit, new_quote_profit, last_trade_price))
                
if __name__ == '__main__':
    main()