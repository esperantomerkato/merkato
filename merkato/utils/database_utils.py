import sqlite3

def drop_merkatos_table():
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))
        
    finally:
        c = conn.cursor()
        c.execute('''DROP TABLE merkatos''')
        conn.commit()
        conn.close()

def drop_exchanges_table():
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))
        
    finally:
        c = conn.cursor()
        c.execute('''DROP TABLE exchanges''')
        conn.commit()
        conn.close()


def create_merkatos_table():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))
        
    finally:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS merkatos
                    (exchange text, exchange_pair text, base text, alt text, spread float, profit_limit integer, last_order text, 
                    first_order text, starting_price float, ask_reserved_balance float, bid_reserved_balance float, profit_margin integer, 
                    base_partials_balance integer, quote_partials_balance integer, init_base_balance integer, init_quote_balance integer, step float,
                    base_profit float, quote_profit float, buy_volume float, sell_volume float)''')
        c.execute('''CREATE UNIQUE INDEX id_exchange_pair ON merkatos (exchange_pair)''')
        conn.commit()
        conn.close()


def no_merkatos_table_exists():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT count(*) FROM sqlite_master WHERE type="table" AND name="merkatos"''')
        number_of_mutex_tables = c.fetchall()[0][0]
        conn.commit()
        conn.close()

        return number_of_mutex_tables == 0


def insert_merkato(exchange, exchange_pair='tuxBTC_ETH', base='BTC', alt='XMR', spread='.1', 
    bid_reserved_balance=0, ask_reserved_balance=0, first_order='', starting_price=.018, profit_limit=10, last_order='', 
    profit_margin=0, step=1.0033, base_partials_balance=0, quote_partials_balance=0, init_base_balance=0, init_quote_balance=0, base_profit=0, quote_profit=0, buy_volume=0, sell_volume=0):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute("""REPLACE INTO merkatos 
                    (exchange, exchange_pair, base, alt, spread, profit_limit, last_order, first_order, starting_price, ask_reserved_balance, bid_reserved_balance, profit_margin, base_partials_balance, quote_partials_balance, starting_price, init_quote_balance, init_base_balance, step, base_profit, quote_profit, buy_volume, sell_volume) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (exchange, exchange_pair, base, alt, spread, profit_limit, last_order, first_order, starting_price, ask_reserved_balance, bid_reserved_balance, profit_margin, base_partials_balance, quote_partials_balance, starting_price, init_quote_balance, init_base_balance, step, base_profit, quote_profit, buy_volume, sell_volume))
        conn.commit()
        conn.close()


def update_merkato(exchange_pair, key, value):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        query = "UPDATE merkatos SET {} = ? WHERE exchange_pair = ?".format(key)
        c.execute(query, (value, exchange_pair) )
        conn.commit()
        conn.close()


def kill_merkato(UUID):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''DELETE FROM merkatos WHERE exchange_pair = ?''', (UUID,))
        conn.commit()
        conn.close()


def get_all_merkatos():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')
        conn.row_factory = dict_factory

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute("SELECT * FROM merkatos")
        all_merkatos = c.fetchall()
        conn.commit()
        conn.close()

        return all_merkatos


def create_exchanges_table():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS exchanges
                    (exchange text, public_api_key text, private_api_key text, limit_only text  )''')
        c.execute('''CREATE UNIQUE INDEX id_exchange ON exchanges (exchange)''')
        conn.commit()
        conn.close()


def insert_exchange(exchange, public_api_key='', private_api_key='', limit_only=True):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute("""REPLACE INTO exchanges 
                    (exchange, public_api_key, private_api_key, limit_only) VALUES (?,?,?,?)""", 
                    (exchange, public_api_key, private_api_key, limit_only))
        conn.commit()
        conn.close()


def update_exchange(exchange, key, value):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        query = "UPDATE exchanges SET {} = ? WHERE exchange = ?".format(key)
        c.execute(query, (value, exchange) )
        conn.commit()
        conn.close()


def get_all_exchanges():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')
        conn.row_factory = sqlite3.Row

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute("SELECT * FROM exchanges")
        all_exchanges = c.fetchall()
        conn.commit()
        conn.close()
        exchange_index = {config["exchange"]:dict(config) for config in all_exchanges}
        exchange_menu = [name for name,config in exchange_index.items()]

        return exchange_menu, exchange_index


def get_exchange(exchange):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')
        conn.row_factory = dict_factory

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT * FROM exchanges WHERE exchange = ?''', (exchange,))
        exchange = c.fetchall()[0]
        conn.commit()
        conn.close()

        return exchange


def exchange_exists(exchange):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT * FROM exchanges WHERE exchange = ?''', (exchange,))
        result = len(c.fetchall())

        conn.commit()
        conn.close()

        return result > 0


def merkato_exists(UUID):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT * FROM merkatos WHERE exchange_pair = ?''', (UUID,))
        result = len(c.fetchall())
        conn.commit()
        conn.close()

        return result > 0


def no_exchanges_table_exists():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT count(*) FROM sqlite_master WHERE type="table" AND name="exchanges"''')
        number_of_exchange_tables = c.fetchall()[0][0]
        conn.commit()
        conn.close()

        return number_of_exchange_tables == 0


def get_merkato(exchange_name_pair):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT * FROM merkatos WHERE exchange_pair = ?''', (exchange_name_pair,))
        exchange = c.fetchall()[0]
        conn.commit()
        conn.close()

        return exchange


def get_merkatos_by_exchange(exchange):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')
        conn.row_factory = dict_factory

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT * FROM merkatos WHERE exchange = ?''', (exchange,))
        exchanges = c.fetchall()
        conn.commit()
        conn.close()

        return exchanges


def dict_factory(cursor, row):
    ''' TODO: Function Comment
    '''
    d = {}

    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]

    return d


def create_balances_table():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS balances
                    (exchanges_foreign_key integer, balance_string text, timestamp integer)''')
        c.execute('''CREATE UNIQUE INDEX id_balances ON balances (timestamp)''')
        conn.commit()
        conn.close()


def insert_balance(exchanges_foreign_key, balance_string, timestamp):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute("""REPLACE INTO balances 
                    (exchanges_foreign_key, balance_string, timestamp) VALUES (?,?,?)""",
                    (exchanges_foreign_key, balance_string, timestamp))
        conn.commit()
        conn.close()


def get_balances(exchanges_foreign_key, timestamp=0):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')
        conn.row_factory = dict_factory

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()

        if timestamp == 0:
            # Retrieve all records
            c.execute('''SELECT * FROM balances WHERE exchanges_foreign_key = ?''', (exchanges_foreign_key,))
            balances = c.fetchall()


        else:
            # Retrieve specific record
            c.execute('''SELECT * FROM balances WHERE exchanges_foreign_key = ? AND timestamp = ?''', (exchanges_foreign_key,timestamp))
            balances = c.fetchall()

        conn.commit()
        conn.close()

        return balances


def no_balances_table_exists():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT count(*) FROM sqlite_master WHERE type="table" AND name="balances"''')
        number_of_balances_tables = c.fetchall()[0][0]
        conn.commit()
        conn.close()

        return number_of_balances_tables == 0