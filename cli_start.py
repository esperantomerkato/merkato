from merkato.merkato_config import load_config, get_config, create_exchange, process_start_option, start_merkatos
from merkato.merkato import Merkato
from merkato.parser import parse
from merkato.utils.database_utils import no_merkatos_table_exists, create_merkatos_table,\
     no_exchanges_table_exists, create_exchanges_table
from merkato.utils import generate_complete_merkato_configs, get_start_option
from merkato.utils.monthly_info_db_utils import no_monthly_info_table_exists, create_monthly_info_table
import sqlite3
import time
import pprint

def main():
    print("Merkato Alpha v0.1.1\n")

    if no_merkatos_table_exists():
        create_merkatos_table()
    if no_exchanges_table_exists():
        create_exchanges_table()
    if no_monthly_info_table_exists():
        create_monthly_info_table()

    option = get_start_option()
    process_result = process_start_option(option)

    if process_result == False:
        return
    elif process_result != None:
        start_merkatos(process_result)
    else:
        main()



if __name__ == '__main__':
    main()