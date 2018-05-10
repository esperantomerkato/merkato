from merkato.merkato_config import load_config, get_config, create_config
from merkato.merkato import Merkato
from merkato.parser import parse
from merkato.utils.database_utils import no_mutex_table_exists, create_mutex_table, insert_mutex, get_all_mutexes
from merkato.exchanges.tux_exchange.utils import translate_ticker
import sqlite3

def main():
    print("Merkato Alpha v0.1.1\n")


    configuration = parse()
    if not configuration:
        configuration= get_config()


    if not configuration:
        raise Exception("Failed to get configuration.")

    base = "BTC"
    coin = "ETH"
    spread = ".1"
    ask_budget = 1
    bid_budget = 1
    pair = translate_ticker(coin, base)
    merkato = Merkato(configuration, coin, base, spread, ask_budget, bid_budget)
    if no_mutex_table_exists():
        create_mutex_table()
    insert_mutex(configuration['exchange'])
    get_all_mutexes()
    merkato.exchange.get_all_orders()


if __name__ == '__main__':
    main()
