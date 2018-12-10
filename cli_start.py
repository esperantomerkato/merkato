from merkato.merkato_config import get_config, create_exchange, process_start_option, start_merkatos
from merkato.parser import parse
from merkato.utils.database_utils import no_merkatos_table_exists, create_merkatos_table,\
     no_exchanges_table_exists, create_exchanges_table
from merkato.utils import generate_complete_merkato_configs, get_start_option, load_config
from merkato.utils.monthly_info_db_utils import no_monthly_info_table_exists, create_monthly_info_table
import sqlite3
import time
import pprint
import logging
import logging.config


root_log = logging.getLogger("myapp")
log = root_log.getChild(__name__)

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
    d = {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s\t%(levelname)s\t%(name)s:%(lineno)d\t%(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },
            "outfile": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "filename": "tx_logs.log",
                "formatter": "simple",
            }
        },
        "loggers": {
            "logfile": {
                "handlers": ["outfile"]
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "outfile"]
        },
        'disable_existing_loggers': False
    }
    logging.config.dictConfig(d)

    main()