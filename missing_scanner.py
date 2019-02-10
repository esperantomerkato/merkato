from binance.client import Client
from binance.enums import *
from matplotlib.ticker import FuncFormatter
from decimal import Decimal
import matplotlib.pyplot as plt
import numpy as np

client = Client()

orders = client.get_open_orders(symbol='XMRBTC', recvWindow=10000000)
s_o = sorted(orders, key=lambda order: order['price'])


def sort_orders(order):
    return float(order['price'])

def find_problems(orders, step, spread):
    orders.sort(key=sort_orders, reverse=True)
    for i, order in enumerate(orders):
        not_last_order = i != len(orders) -1
        if not_last_order:
            big = float(orders[i]['price'])
            small = float(orders[i + 1]['price'])
            gap = abs((big-small)/small)
            if gap < (step / 2):
                print('ERROR DOUBLED UP')
                print('small', small)
                print('big', big)
            if 1+gap > (1+step) * (1+spread):
                print('ERROR GAP')
                print('small', small)
                print('big', big)

find_problems(orders, .0175, .025)

def get_filtered_amounts(orders):
    return list(map(lambda x: x['origQty'], orders))

def get_filtered_prices(orders):
    return list(map(lambda x: round(float(x['price']) * 100000), orders))

my_input = input('which section of orders? 1, 2, or 3? ')
if my_input == '1':
    list_to_present = s_o[:round(len(s_o)/3)]
elif my_input == '2':
    list_to_present = s_o[round(len(s_o)/3):round(len(s_o)/3*2)]
elif my_input == '3':
    list_to_present = s_o[round(len(s_o)/3*2):]

x = np.arange(len(list_to_present))
filterted_prices = get_filtered_prices(list_to_present)
filtered_amounts = get_filtered_amounts(list_to_present)
amounts = filtered_amounts
fig, ax = plt.subplots()
plt.bar(x, amounts)
plt.xticks(x, filterted_prices)
plt.show()
