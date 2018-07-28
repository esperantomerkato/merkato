import asyncio
import json
import websockets

from merkato.merkato_config import get_config
from merkato.parser import parse
from merkato.utils.database_utils import no_merkatos_table_exists, create_merkatos_table, drop_merkatos_table, \
    no_exchanges_table_exists, create_exchanges_table, drop_exchanges_table

import logging
log = logging.getLogger("client")

"""
Merkato WebSocket CLI client.
This demonstrates the behavior that will eventually be moved to a Javascript GUI client.
Establish a connection to server, get user input, send config to server,
and loop awaiting updates from server. (In the GUI, it'll also loop awaiting user action e.g. button clicks.)
"""


async def client(url):
    async with websockets.connect(url) as ws:
        log.info("Connected.")

        try:
            merkato_params = get_merkato_params_from_user()
            log.info("Sending Merkato params {}".format(merkato_params))
            await ws.send(json.dumps({'merkato_params': merkato_params}))

            while True:
                msg = await ws.recv()
                print("Received {}".format(msg))
        except websockets.ConnectionClosed:
            log.error("Server unexpectedly closed connection, investigate.")
            exit(1)


def get_merkato_params_from_user():
    print("Merkato Alpha v0.1.1\n")

    if no_merkatos_table_exists():
        create_merkatos_table()
    else:
        should_drop_merkatos = input('Do you want to drop merkatos? y/n: ')
        if should_drop_merkatos == 'y':
            drop_merkatos_table()
            create_merkatos_table()

    if no_exchanges_table_exists():
        create_exchanges_table()
    else:
        should_drop_exchanges = input('Do you want to drop exchanges? y/n: ')
        if should_drop_exchanges == 'y':
            drop_exchanges_table()
            create_exchanges_table()

    configuration = parse()

    if not configuration:
        configuration = get_config()

    if not configuration:
        raise Exception("Failed to get configuration.")

    base = input("Base: ")
    coin = input("Coin: ")
    spread = input("Spread: ")
    coin_reserve = input("Coin reserve: ")
    base_reserve = input("Base reserve: ")

    return {
        'configuration': configuration,
        'base': base,
        'coin': coin,
        'spread': float(spread),
        'bid_reserved_balance': float(base_reserve),
        'ask_reserved_balance': float(coin_reserve)
    }


if __name__ == "__main__":
    url = "ws://localhost:5678"
    asyncio.get_event_loop().run_until_complete(client(url))