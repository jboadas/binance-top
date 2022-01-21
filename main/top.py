import requests
import json
from decimal import Decimal

API_URL = 'https://api.binance.com/api/v3/ticker/24hr'


def get_trades_from_binance():
    try:
        trades = requests.get(API_URL).json()
        trades_filter = []
        for t in trades:
            if 'USDT' in t['symbol']:
                trades_filter.append(t)
        with open('json/top.json', 'w') as outfile:
            json.dump(trades_filter, outfile)
            print('done')
    except Exception as e:
        print(e)


def order_key(e):
    return float(e['priceChangePercent'])


def get_top_price_change():
    try:
        with open('json/top.json') as trades_file:
            trades = json.load(trades_file)
            trades.sort(reverse=True, key=order_key)
            top_trades = []
            for t in trades:
                ask_price = Decimal(t['askPrice'])
                if ask_price > 0.0:
                    top_trades.append(t)
                if len(top_trades) >= 15:
                    break
            for t in top_trades:
                print(t['symbol'], t['priceChangePercent'], t['askPrice'], t['bidPrice'])
            return top_trades
    except Exception as e:
        print(e)
        return []


# get_trades_from_binance()
get_top_price_change()
