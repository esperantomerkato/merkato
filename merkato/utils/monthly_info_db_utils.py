import sqlite3

def drop_monthly_info_table():
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))
        
    finally:
        c = conn.cursor()
        c.execute('''DROP TABLE monthly_info''')
        conn.commit()
        conn.close()


def create_monthly_info_table():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))
        
    finally:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS monthly_info
                    (exchange_pair text, spread float, step float, start_base float, start_quote float, end_base float, end_quote float, 
                    mm_base_profit float, mm_quote_profit float, ending_usd_val float, last_price float, base_volume float, quote_volume float)''')
        conn.commit()
        conn.close()


def no_monthly_info_table_exists():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''SELECT count(*) FROM sqlite_master WHERE type="table" AND name="monthly_info"''')
        number_of_mutex_tables = c.fetchall()[0][0]
        conn.commit()
        conn.close()

        return number_of_mutex_tables == 0


def insert_monthly_info(exchange_pair='tuxBTC_ETH', spread='.1', last_price=.018, step=1.0033, start_base=0, start_quote=0, 
    end_base=0, end_quote=0, mm_base_profit=0, mm_quote_profit=0, ending_usd_val=0, base_volume=0, quote_volume=0):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute("""INSERT INTO monthly_info 
                    (exchange_pair, spread, step, start_base, start_quote, end_base, end_quote, mm_base_profit, mm_quote_profit, ending_usd_val, last_price, base_volume, quote_volume) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (exchange_pair, spread, step, start_base, start_quote, end_base, end_quote, mm_base_profit, mm_quote_profit, ending_usd_val, last_price, base_volume, quote_volume))
        conn.commit()
        conn.close()


def update_monthly_info(exchange_pair, key, value):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        query = "UPDATE monthly_info SET {} = ? WHERE exchange_pair = ?".format(key)
        c.execute(query, (value, exchange_pair) )
        conn.commit()
        conn.close()


def kill_monthly_info(UUID):
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute('''DELETE FROM monthly_info WHERE exchange_pair = ?''', (UUID,))
        conn.commit()
        conn.close()


def get_all_monthyly_info():
    ''' TODO: Function Comment
    '''
    try:
        conn = sqlite3.connect('merkato.db')
        conn.row_factory = dict_factory

    except Exception as e:
        print(str(e))

    finally:
        c = conn.cursor()
        c.execute("SELECT * FROM monthly_info")
        all_merkatos = c.fetchall()
        conn.commit()
        conn.close()

        return all_merkatos

def dict_factory(cursor, row):
    ''' TODO: Function Comment
    '''
    d = {}

    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]

    return d