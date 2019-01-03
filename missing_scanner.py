from binance.client import Client
from binance.enums import *

client = Client()

orders = client.get_open_orders(symbol='XMRBTC', recvWindow=10000000)
sorted_orders = sorted(orders, key=lambda order: order['price'])

# print('ord	ers', orders)

def sort_orders(order):
    return float(order['price'])

def find_problems(orders, step):
    for i, order in enumerate(orders):
        not_last_order = i != len(orders) -1
        if not_last_order:
            small = float(orders[i]['price'])
            big = float(orders[i + 1]['price'])
            small_big_div = big/small
            if small_big_div > 1 + (step * 1.50):
                print('ERROR GAP')
                print('small', small)
                print('big', big)

    orders.sort(key=sort_orders, reverse=True)
    for i, order in enumerate(orders):
        not_last_order = i != len(orders) -1
        if not_last_order:
            big = float(orders[i]['price'])
            small = float(orders[i + 1]['price'])
            gap = (big-small)/small
            if gap < (step / 2):
                print('ERROR DOUBLED UP')
                print('small', small)
                print('big', big)

find_problems(orders, .025)

trades = client.get_my_trades(symbol='XMRBTC', recvWindow=10000000)

print('treades', trades)