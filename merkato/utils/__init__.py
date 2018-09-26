import logging
import json
from merkato.exchanges.test_exchange.exchange import TestExchange
from merkato.exchanges.tux_exchange.exchange import TuxExchange
from merkato.exchanges.binance_exchange.exchange import BinanceExchange
from merkato.constants import known_exchanges, known_assets
from merkato.utils.database_utils import get_exchange as get_exchange_from_db, get_merkatos_by_exchange, get_merkato, update_merkato
import base64
import time
import getpass
import math
import os

from decimal import *
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

getcontext().prec = 8
salt = 'merkato'

def encrypt(password, source):
    kdf = PBKDF2HMAC(
      algorithm=hashes.SHA256(),
      length=32,
      salt=salt.encode(),
      iterations=10,
      backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(source)
    return cipher_text


def decrypt(password, source):
    kdf = PBKDF2HMAC(
      algorithm=hashes.SHA256(),
      length=32,
      salt=salt.encode(),
      iterations=10,
      backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(source)
    return plain_text


def update_config_with_credentials(config):
    print("API Credentials needed")
    public_key  = getpass.getpass("Public Key: ")
    private_key = getpass.getpass("Private Key: ")
    config['public_api_key'] = public_key
    config['private_api_key'] = private_key


def get_exchange():
    print("What exchange is this config file for?")
    print("1. for TuxExchange type 'tux'")
    print("2. for Poloniex type 'polo'")
    print("3. for Bittrex type 'bit'")
    print("3. for TestExchange type 'test'")
    print("4. for BinanceExchange type 'bina'")
    selection = input("Selection: ")
    if selection not in known_exchanges:
        print('selected exchange not supported, try again')
        return get_exchange()
    return selection

def get_asset(type):
    print("Which asset should be the {}?".format(type))
    print("1 -> BTC")
    print("2 -> XMR")
    print("3 -> ETH")
    print("4 -> USDT")
    print("5 -> PEPECASH")
    selection = input("Selection: ")
    if selection not in known_assets:
        print('selected exchange not supported, try again')
        return get_asset()
    return selection

def get_reserve_balance(type):
    print("What quantity of the {} should be used?".format(type))
    print('MUST BE A NUMBER')
    selection = float(input("Selection: "))
    return selection

def get_merkato_variable(type, extra_message=''):
    print("What {} should be used?".format(type))
    print('MUST BE A NUMBER')
    print(extra_message)
    selection = float(input("Selection: "))
    return selection


def get_config_selection():
    print("Please make a selection:")
    print("1 -> Add new exchange")
    print("2 -> Load existing merkato")
    print("3 -> Exit")
    return input("Selection: ")


def get_start_option():
    print("Welcome to Esperanto Merkato! What would you like to do?")
    print("1 -> Run Merkatos")
    print("2 -> Add exchange")
    print("3 -> Add merkato (Requires existing exchanges)")
    print("4 -> Drop tables")
    print("5 -> Add asset to a Merkato")
    print("6 -> change spread of a Merkato")
    print("7 -> Exit")
    return input("Selection: ")

def create_price_data(orders, order):
    price_data             = {}
    price_data['total']    = Decimal(orders[order]["total"])
    price_data['amount']   = Decimal(orders[order]["amount"])
    price_data['id'] = orders[order]["id"]
    price_data['type']     = orders[order]["type"]
    return price_data


def validate_merkato_initialization(configuration, coin, base, spread):
    if len(configuration) == 4:
        return
    raise ValueError('config does not contain needed values.', configuration)


def get_relevant_exchange(exchange_name):
    exchange_classes = {
        'tux': TuxExchange,
        'test': TestExchange,
        'bina': BinanceExchange
    }
    return exchange_classes[exchange_name]


def generate_complete_merkato_configs(merkato_objects):
    merkato_complete_configs = []
    for merkato in merkato_objects:
        complete_config = {}
        config = {"limit_only": True}
        exchange = get_exchange_from_db(merkato['exchange'])
        
        config['exchange'] = merkato['exchange']
        config['public_api_key'] = exchange['public_api_key']
        config['private_api_key'] = exchange['private_api_key']

        complete_config['configuration'] = config
        complete_config['base'] = merkato['base']
        complete_config['coin'] = merkato['alt']
        complete_config['spread'] = merkato['spread']
        complete_config['starting_price'] = merkato['starting_price']
        complete_config['ask_reserved_balance'] = merkato['ask_reserved_balance']
        complete_config['bid_reserved_balance'] = merkato['bid_reserved_balance']
        complete_config['base_profit'] = merkato['base_profit']
        complete_config['quote_profit'] = merkato['quote_profit']
        complete_config['init_quote_balance'] = merkato['init_quote_balance']
        complete_config['init_base_balance'] = merkato['init_base_balance']
        merkato_complete_configs.append(complete_config)
    return merkato_complete_configs

def update_unmade_stack(stack, merkato_uuid):
    string_stack = json.dumps(stack)
    update_merkato(merkato_uuid, 'unmade_stack', string_stack)

def get_allocated_pair_balances(exchange, base, coin):
    allocated_pair_balances = {
        'base': Decimal(0),
        'coin': Decimal(0)
    }

    merkatos = get_merkatos_by_exchange(exchange)
    for merkato in merkatos:
        if merkato['base'] == base:
            allocated_pair_balances['base'] += Decimal(merkato['bid_reserved_balance'])
            allocated_pair_balances['base'] += Decimal(merkato['base_partials_balance'])

        if merkato['alt'] == coin:
            allocated_pair_balances['coin'] += Decimal(merkato['ask_reserved_balance'])
            allocated_pair_balances['coin'] += Decimal(merkato['quote_partials_balance'])

    return allocated_pair_balances


def check_reserve_balances(total_balances, allocated_balances, coin_reserve, base_reserve):
    remaining_balances = {
        'base': Decimal(total_balances['base']['amount']['balance']) - allocated_balances['base'],
        'coin': Decimal(total_balances['coin']['amount']['balance']) - allocated_balances['coin']
    }

    if remaining_balances['base'] < base_reserve:
        return False
        # raise ValueError('Cannot create merkato, the suggested base reserve will exceed the amount of the base asset on the exchange.')
    if remaining_balances['coin'] < coin_reserve:
        return False
        #raise ValueError('Cannot create merkato, the suggested coin reserve will exceed the amount of the coin asset on the exchange.')
    return True


def get_last_order( UUID):
    merkato = get_merkato(UUID)
    last_order = merkato[6]
    return last_order


def get_first_order( UUID):
    merkato = get_merkato(UUID)
    first_order = merkato[7]
    return first_order


def get_new_history(current_history, last_order):
    for index, order in enumerate(current_history):
        is_last_order = str(order['id']) == str(last_order)
        if is_last_order:
            new_history = current_history[:index]
            new_history.reverse() # need to reverse due to the newest order at start of the list, we want oldest
            return new_history
    if last_order == '':
        return current_history
    return []

def get_time_of_last_order(ordered_transactions):
    index_of_last_tx = len(ordered_transactions) -1
    last_tx_data = ordered_transactions[index_of_last_tx]['date']
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(last_tx_data, pattern)))
    return epoch

def get_market_results(history): 
    results = {
        'amount_executed': 0, # This is in the quote asset
        'initial_amount': 0, # This is in the base asset
        'price_numerator': 0
    }
    print('get market reseults', history)
    for order in history:
        results['amount_executed'] += Decimal(order['amount'])
        results['initial_amount'] += Decimal(order['initamount'])
        results['price_numerator'] += Decimal(order['amount']) * Decimal(order['price'])
    results['last_txid'] = history[-1]['id']
    results['price_numerator'] /= results['amount_executed']
    return results

def ensure_bytes(password, public_key, private_key):
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(public_key, str):
        public_key = public_key.encode('utf-8')
    if isinstance(private_key, str):
        private_key = private_key.encode('utf-8')
    return (password, public_key, private_key)


def log_on_call(f):
    def wrapped(self, *args, **kwargs):
        log = logging.getLogger()
        log.debug("Entering {}".format(f.__name__))
        return f(self, *args, **kwargs)
    return wrapped


def log_all_methods(cls):
    for name in cls.__dict__:
        attr = getattr(cls, name)
        if callable(attr):
            setattr(cls, name, log_on_call(attr))
    return cls


def log_new_cointrackr_transactions(newTransactionHistory, coin, base, name):
    path="{}my_merkato_tax_audit_logs.csv".format(name)
    scrubbed_history = []
    for dirty_tx in newTransactionHistory:
        scrubbed_tx = []
        scrubbed_tx.append(dirty_tx['date'])
        if dirty_tx['type'] == 'buy':
            scrubbed_tx.append(dirty_tx['amount'])
            scrubbed_tx.append(coin)
            scrubbed_tx.append(dirty_tx['total'])
            scrubbed_tx.append(base)
        else:
            scrubbed_tx.append(dirty_tx['total'])
            scrubbed_tx.append(base)
            scrubbed_tx.append(dirty_tx['amount'])
            scrubbed_tx.append(coin)
        scrubbed_history.append(scrubbed_tx)

    headers_needed = not os.path.exists(path)

    with open(path, 'a+') as csvfile:
        fieldnames = ['Date', 'Recieved Quantity', "Currency", "Sent Quantity", "Currency"]
        writer = csv.writer(csvfile)
        if headers_needed:
            writer.writerow(fieldnames)
        for tx in scrubbed_history:
            writer.writerow(tx)

def calculate_scaling_factor(scaling_log_factor, step, total_orders):
    scaling_factor = 0
    current_order = 0
    
    # Calculate scaling factor
    while current_order < total_orders:
        scaling_factor += Decimal(1/(step**current_order))
        current_order += 1
    
    return scaling_factor

def calculate_remaining_reserve(total_reserve, orders_to_increase, step, scaling_factor):
    current_order = 0
    remaining_reserve = total_reserve
    while current_order < orders_to_increase:
        step_adjusted_factor = Decimal(step**current_order)
        current_ask_amount = total_reserve/(scaling_factor * step_adjusted_factor) * Decimal(.5)
        remaining_reserve -= current_ask_amount
        current_order += 1
    return remaining_reserve
