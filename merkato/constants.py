tuxURL  = "https://tuxexchange.com/api"
poloURL = "https://poloniex.com/public"
BUY = 'buy'
SELL = 'sell'
ID = 'id'
PRICE = 'price'
USER_ID = 'user_id'
AMOUNT = 'amount'
known_exchanges = {
    'tux': 'tux',
    'polo': 'polo',
    'bit': 'bit',
    'test': 'test',
    'bina': 'bina',
    'krak': 'krak'
}
known_assets = {
    'XMR': 'XMR',
    'BTC': 'BTC',
    'PEPECASH': 'PEPECASH',
    'USDT': 'USDT',
    'ETH': 'ETH'
}
implemented_exchanges = ["tux", "test"]
LAST_ORDER = 'last_order'
FIRST_ORDER = 'first_order'

ASK_RESERVE = 'ask_reserved_balance'
BID_RESERVE = 'bid_reserved_balance'

EXCHANGE = 'exchange'
ONE_SATOSHI = 0.00000001
ONE_BITCOIN = 1
MARKET = 'market'
TYPE = 'type'
STARTING_PRICE = 'starting_price'
INIT_QUOTE_BALANCE = 'init_quote_balance'
INIT_BASE_BALANCE = 'init_base_balance'
BASE_PROFIT = 'base_profit'
QUOTE_PROFIT = 'quote_profit'
LIMIT = 'limit'
BUY_VOLUME = 'buy_volume'
SELL_VOLUME = 'sell_volume'

round_trip_exchange_fees = {
    'krak': .0032,
    'bina': .002
}