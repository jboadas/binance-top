import requests
import json
from decimal import Decimal
import sqlite3
from collections import OrderedDict
import datetime

CON = sqlite3.connect('data/top.db')
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
                if len(top_trades) >= 10:
                    break
            for t in top_trades:
                print(t['symbol'], t['priceChangePercent'], t['askPrice'], t['bidPrice'])
            return top_trades
    except Exception as e:
        print(e)
        return []


def sell_selected(selected_sells):
    cur = CON.cursor()
    with open('json/top.json') as trades_file:
        trades = json.load(trades_file)
        sell_prices = []
        for trade in trades:
            if trade.get('symbol') in selected_sells:
                curr_sell = {}
                curr_sell['symbol'] = trade.get('symbol')
                curr_sell['sell_price'] = trade.get('bidPrice')
                sell_prices.append(curr_sell)
                cur.execute(
                    """
                        UPDATE gainers
                        SET sell = '%s'
                        WHERE symbol = '%s';
                    """ % (
                        trade.get('bidPrice'),
                        trade.get('symbol')))
                CON.commit()

        print(sell_prices)


def buy_selected(selected_buys):
    cur = CON.cursor()
    for i in selected_buys:
        cur.execute(
            """
                INSERT INTO gainers
                VALUES ('%s','%s','%s','%s','%s','%s')
            """ % (
                i.get('symbol'),
                i.get('priceChangePercent'),
                i.get('askPrice'),
                0,
                i.get('weightedAvgPrice'),
                datetime.datetime.now()))
    CON.commit()


def choose_sell_buy(top_change):
    cur = CON.cursor()
    cur.execute(
        """
            SELECT symbol FROM gainers WHERE sell == 0.0;
        """)
    symbols = cur.fetchall()
    symbol_list = [i[0] for i in symbols]
    print("current buys", symbol_list)
    tc_symbol_list = []
    for tc in top_change:
        tc_symbol_list.append(tc['symbol'])
    print("current top change", tc_symbol_list)

    print("symbol_list", symbol_list)
    print("tc_symbol_list", tc_symbol_list)
    will_sell = list(set(symbol_list) - set(tc_symbol_list))
    will_buy_symbols = list(set(tc_symbol_list) - set(symbol_list))
    print("will_buy_symbols", will_buy_symbols)

    will_buy = []
    for tc in top_change:
        if tc.get('symbol') in will_buy_symbols:
            will_buy.append(tc)
        if len(will_sell) + len(will_buy) >= 5:
            break
    print("will sell:", will_sell)
    print("will buy:", will_buy_symbols)
    sell_selected(will_sell)
    buy_selected(will_buy)


def clean_database():
    cur = CON.cursor()
    cur.execute(
        """
            delete FROM gainers;
        """)
    CON.commit()


# get_trades_from_binance()
top_price_change = get_top_price_change()
choose_sell_buy(top_price_change)
# clean_database()
