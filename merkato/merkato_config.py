# Merkato Configuration

import json
import os.path
from merkato.utils.database_utils import get_exchange,insert_exchange, no_exchanges_table_exists, create_exchanges_table, create_merkatos_table, create_exchanges_table, drop_merkatos_table, drop_exchanges_table, get_exchange as get_exchange_from_db, get_all_merkatos, update_merkato
from merkato.exchanges.tux_exchange.utils import validate_credentials
from merkato.exchanges.kraken_exchange.utils import validate_kraken
from merkato.exchanges.binance_exchange.utils import validate_keys
from merkato.constants import EXCHANGE
from merkato.merkato import Merkato
from merkato import merkato as main_merkato
from merkato.utils import load_config, decrypt_keys, update_config_with_credentials, get_exchange, get_config_selection, encrypt, decrypt, ensure_bytes, generate_complete_merkato_configs, get_asset, get_reserve_balance, get_merkato_variable, load_exchange_by_merkato, twilio_wrapper, update_balances
from merkato.utils.monthly_info_db_utils import insert_monthly_info, create_monthly_info_table, drop_monthly_info_table, get_all_monthyly_info
from merkato.merkato_manager import Merkato_Manager

import getpass
import time
from binance.client import Client

BOLD_BEGIN = '\033[1m'
BOLD_END = '\033[0m'

def insert_config_into_exchanges(config):
    limit_only = config["limit_only"]
    public_key = config["public_api_key"]
    private_key = config["private_api_key"]
    exchange = config["exchange"]

    if no_exchanges_table_exists():
        create_exchanges_table()

    insert_exchange(exchange, public_key, private_key, limit_only)


def create_exchange():
    # Create new config
    config = { "limit_only": True }

    while True:
        exchange = get_exchange()
        config[EXCHANGE] = exchange

        if exchange == 'tux':
            update_config_with_credentials(config)
            credentials_are_valid = validate_credentials(config)
            print('credentials_are_valid', credentials_are_valid)

            while not credentials_are_valid:
                update_config_with_credentials(config)
                credentials_are_valid = validate_credentials(config)

            encrypt_keys(config)
            insert_config_into_exchanges(config)
            decrypt_keys(config)
            return config
        
        elif exchange == 'test':
            config[EXCHANGE] = 'test'
            update_config_with_credentials(config)
            encrypt_keys(config)
            insert_config_into_exchanges(config)
            return config

        elif exchange == 'polo':
            print("Currently Unsupported")
            continue

        elif exchange == 'bit':
            print("Currently Unsupported")
            continue

        elif exchange == 'krak':
            update_config_with_credentials(config)
            credentials_are_valid = validate_kraken(config)

            while not credentials_are_valid:
                update_config_with_credentials(config)
                credentials_are_valid = validate_kraken(config)

            encrypt_keys(config)
            insert_config_into_exchanges(config)
            decrypt_keys(config)
            return config
        
        elif exchange == 'bina':
            update_config_with_credentials(config)
            credentials_are_valid = validate_keys(config)
            print('credentials_are_valid', credentials_are_valid)

            while not credentials_are_valid:
                update_config_with_credentials(config)
                credentials_are_valid = validate_keys(config)

            encrypt_keys(config)
            insert_config_into_exchanges(config)
            decrypt_keys(config)
            return config

        else:
            print("Unrecognized Selection")
            continue


def encrypt_keys(config, password=None):
    ''' Encrypts the API keys before storing the config in the database
    '''
    public_key  = config["public_api_key"]
    private_key = config["private_api_key"]

    if password is None:
        password = getpass.getpass("\n\ndatabase password:") # Prompt user for password / get password from Nasa. This should be a popup?

    password, public_key, private_key = ensure_bytes(password, public_key, private_key)

    # encrypt(password, data)
    # Inputs are of type:
    # - password: bytes
    # - data:     bytes

    public_key_encrypted  = encrypt(password, public_key)
    private_key_encrypted = encrypt(password, private_key)
    config["public_api_key"]  = public_key_encrypted
    config["private_api_key"] = private_key_encrypted
    return config

def decrypt_merkato(merkato, password=None):
    ''' Decrypts the API keys inside a merkato dict before storing the config in the database
    '''
    decrypt_keys(merkato["configuration"], password)
    return merkato


def get_config():
    while True:

        selection = get_config_selection()
        if selection =='1':
            # Create new config
            config = create_exchange()
            return config

        elif selection == '2':
            # Load existing config
            config = load_config()
            # decrypt_passwords(config)
            return config

        elif selection == '3':
            return {}

        elif selection == '4':
            # Exit
            return {}

        else:
            print("Unrecognized input.")


def process_start_option(option):
    while True:
        if option =='1':
            start_merkatos()

        elif option == '2':
            create_exchange()
            return 

        elif option == '3':
            password = create_new_merkato()
            return password

        elif option == '4':
            handle_drop_selection()
            return

        elif option == '5':
            handle_add_asset()
            return

        elif option == '6':
            handle_view_month_datas()
            return
        
        elif option == '7':
            update_monthly_datas()
            return

        elif option == '8':
            handle_save_merkato_orderbook()
            return

        elif option == '9':
            return False

        else:
            return False

def handle_save_merkato_orderbook():
    complete_merkato = select_and_get_complete_merkato()
    password = getpass.getpass('Enter password for merkato: ')
    decrypt_keys(config=complete_merkato['configuration'], password=password)
    manager = Merkato_Manager(**complete_merkato)
    manager.save_orderbook_to_txt()

def select_and_get_complete_merkato():
    merkatos = get_all_merkatos()
    complete_merkato_configs = generate_complete_merkato_configs(merkatos)

    print('Select Merkato from available IDs')
    for counter, complete_config in enumerate(complete_merkato_configs):
        exchange_name = complete_config['configuration']['exchange'] + '_' + complete_config['base'] + '_' + complete_config['coin']
        print('{} -> {}'.format(counter + 1,  exchange_name))
    selection = input('Selection: ')
    num_selection = int(selection) - 1
    selection_exists = len(complete_merkato_configs) > num_selection

    if selection_exists:
        return complete_merkato_configs[num_selection]
    else:
        return handle_save_merkato_orderbook()

def handle_view_month_datas():
    monthly_infos = get_all_monthyly_info()
    for info in monthly_infos:
        merkato_name = info['exchange_pair']
        human_time = time.strftime("%Z - %Y/%m/%d, %H:%M:%S", time.localtime(info['date']))
        spread = info['spread']
        step = info['step']
        start_base = info['start_base']
        start_quote = info['start_quote']
        abs_base_profit = info['end_base'] - info['start_base']
        abs_quote_profit = info['end_quote'] - info['start_quote']
        base_overall_profit = abs_base_profit + (abs_quote_profit * info['last_price'])
        quote_overall_profit = abs_quote_profit + (abs_base_profit / info['last_price'])
        relative_profit = (quote_overall_profit/ (start_quote + (start_base / info['last_price']))) * 100
        title = 'Monthly Data for {} at {}'.format(merkato_name, human_time)
        print(BOLD_BEGIN + title + BOLD_END)
        print('Spread: {} Step: {} Start Base: {} Start Quote: {}'.format(spread, step, start_base, start_quote))
        print('End Numbers base: {} quote: {}'.format(info['end_base'], info['end_quote']))
        print('MM profit -> base: {} quote: {}'.format(info['mm_base_profit'], info['mm_quote_profit']))
        print('ABS crypto profit base: {} quote: {}'.format(abs_base_profit, abs_quote_profit))
        print('ABS Comparison to previous month total base: {} total quote: {}  relative: {}% '.format(base_overall_profit, quote_overall_profit, relative_profit))
        print('Volume base: {} quote: {}'.format(info['base_volume'], info['quote_volume']))
        print('USD Value: {} \n'.format(info['ending_usd_val']))

def update_monthly_datas():
    merkatos = get_all_merkatos()
    for merkato in merkatos:
        generate_complete_monthly_data(merkato)

def generate_complete_monthly_data(merkato):
    monthly_data = {}
    monthly_data['spread'] = merkato['spread']
    monthly_data['step'] = merkato['step']
    monthly_data['mm_base_profit'] = merkato['base_profit']
    monthly_data['mm_quote_profit'] = merkato['quote_profit']
    monthly_data['start_quote'] = merkato['init_quote_balance']
    monthly_data['start_base'] = merkato['init_base_balance']
    monthly_data['exchange_pair'] = merkato['exchange_pair']
    exchange = load_exchange_by_merkato(merkato)
    
    absolute_balances = exchange.get_balances()
    (absolute_base, absolute_quote) = get_current_balances(monthly_data, absolute_balances)
    monthly_data['last_price'] = float(exchange.get_last_trade_price())
    monthly_data['base_volume'] = merkato['buy_volume']
    monthly_data['quote_volume'] = merkato['sell_volume']
    monthly_data['end_base'] = absolute_base
    monthly_data['end_quote'] = absolute_quote
    monthly_data['date'] = round(time.time())
    add_usd_values(merkato, monthly_data)
    insert_monthly_info (**monthly_data)
    reset_merkato_metrics(merkato, absolute_base, absolute_quote)

def reset_merkato_metrics(merkato, base_balance, quote_balance):
    UUID = merkato['exchange_pair']
    update_merkato(UUID, 'buy_volume', 0)
    update_merkato(UUID, 'sell_volume', 0)
    update_merkato(UUID, 'init_base_balance', base_balance)
    update_merkato(UUID, 'init_quote_balance', quote_balance)
    update_merkato(UUID, 'quote_profit', 0)
    update_merkato(UUID, 'base_profit', 0)

def get_current_balances(data, balances):
    absolute_base = float(balances['base']['amount']['balance'])
    absolute_quote = float(balances['coin']['amount']['balance'])
    return (absolute_base, absolute_quote)

def add_usd_values(merkato, monthly_data):
    client = Client('', '')
    base_price = float(client.get_ticker(symbol=merkato['base'] + 'USDT')["lastPrice"])
    quote_price = float(client.get_ticker(symbol=merkato['alt'] + merkato['base'])["lastPrice"]) * base_price
    monthly_data['ending_usd_val'] = monthly_data['end_base'] * base_price
    monthly_data['ending_usd_val'] += monthly_data['end_quote'] * quote_price


def handle_drop_selection():
    should_drop_merkatos = input('Do you want to drop merkatos? y/n: ')
    if should_drop_merkatos == 'y':
        drop_merkatos_table()
        create_merkatos_table()
    
    should_drop_exchanges = input('Do you want to drop exchanges? y/n: ')
    if should_drop_exchanges == 'y':
        drop_exchanges_table()
        create_exchanges_table()

    should_drop_monthly_info = input('Do you want to drop monthly info? y/n: ')
    if should_drop_monthly_info == 'y':
        drop_monthly_info_table()
        create_monthly_info_table()

def handle_add_asset():

    complete_config = select_and_get_complete_merkato()
    asset_to_add = input('Do you want to add to {} or {}: '.format(complete_config['coin'], complete_config['base']))
    while asset_to_add != complete_config['coin'] and asset_to_add != complete_config['base']:
        print('Wrong Asset, try again')
        asset_to_add = input('Do you want to add to {} or {}: '.format(complete_config['coin'], complete_config['base']))

    amount_to_add = input('How much {} do you want to add: '.format(asset_to_add))

    password = getpass.getpass('Enter password for merkato: ')
    decrypt_keys(config=complete_config['configuration'], password=password)
    initialized_merkato = main_merkato.Merkato(**complete_config)
    initialized_merkato.update_orders(asset_to_add, amount_to_add)



def start_merkatos(password=None):
    if password == None:
        password = getpass.getpass()
    merkatos = get_all_merkatos()
    complete_merkato_configs = generate_complete_merkato_configs(merkatos)

    initialized_merkatos = []

    for complete_config in complete_merkato_configs:
        decrypt_keys(config=complete_config['configuration'], password=password)
        merkato_instance = main_merkato.Merkato(**complete_config)
        initialized_merkatos.append(merkato_instance)

    last_balance_update = 0
    while True:
        faulty_merkatos = []

        epoch = int(time.time())
        time_since_balance_update = epoch - last_balance_update
        should_update_balances = False # reset the flag

        if time_since_balance_update > 60*60: # 1 hour, tweak this to desired rate of balance storage. Maybe break out into a config.
            should_update_balances = True
            last_balance_update = epoch

        for merkato_instance in initialized_merkatos:
            twilio_wrapper(merkato_instance, faulty_merkatos)

            if should_update_balances:
                # Run an update for every merkato instance, even though there will be duplicates.
                # We use timestamp as the unique field, so subsequent inserts will replace
                update_balances(merkato_instance, epoch)

            time.sleep(8)


def create_new_merkato():
    password = getpass.getpass()
    exchange_name = get_exchange()
    exchange = get_exchange_from_db(exchange_name)

    merkato_args = {}
    merkato_args['configuration'] = decrypt_keys(exchange, password)
    merkato_args['coin'] = get_asset('quote')
    merkato_args['base'] = get_asset('base')
    merkato_args['ask_reserved_balance'] = get_reserve_balance('quote')
    merkato_args['bid_reserved_balance'] = get_reserve_balance('base')
    merkato_args['spread'] = get_merkato_variable('spread', 'for 5% spread use .05')
    merkato_args['profit_margin'] = get_merkato_variable('profit margin')
    merkato_args['step'] = get_merkato_variable('step', 'for 5% step use "1.05"')
    merkato_args['distribution_strategy'] = get_merkato_variable('distribution strategy', 'Input "1 for aggressive, "2" for neutral, "3" for hyper aggro:')
    merkato_args['increased_orders'] = get_merkato_variable('Increased Orders', 'SUGGESTED IS 0, 1, or 2')
    Merkato(**merkato_args)
    return password

