import requests
import json

API_URL = 'https://api.binance.com/api/v3/ticker/24hr'


def get_trades_from_binance():
    trades = requests.get(API_URL).json()
    trades_filter = []
    for t in trades:
        if 'USDT' in t['symbol']:
            trades_filter.append(t)
    with open('json/top.json', 'w') as outfile:
        json.dump(trades_filter, outfile)
        print('done')


get_trades_from_binance()
