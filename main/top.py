import requests
import json
from decimal import Decimal
import sqlite3
import datetime
import sys
import logging

logging.basicConfig(
    filename='logs/top.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S',)

CON = sqlite3.connect('data/top.db')
API_URL = 'https://api.binance.com/api/v3/ticker/24hr'


def get_trades_from_binance():
    try:
        trades = requests.get(API_URL).json()
        trades_filter = []
        position = 0
        for t in trades:
            position += 1
            if 'USDT' in t['symbol']:
                t['position'] = position
                trades_filter.append(t)
        with open('json/top.json', 'w') as outfile:
            json.dump(trades_filter, outfile)
            logging.info('get trades done')
            return True
    except Exception as e:
        logging.error(e)
        return False


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
                vwap_price = Decimal(t['weightedAvgPrice'])
                if ask_price > 0.0 and ask_price > vwap_price:
                    t['position'] = len(top_trades) + 1
                    top_trades.append(t)
                if len(top_trades) >= 10:
                    break
            logging.info("### current top 10 - 24h change")
            for t in top_trades:
                logging.info('-' * 20)
                logging.info("symbol: %s", str(t['symbol']))
                logging.info("24hr change: %s", str(t['priceChangePercent']))
                logging.info("askPrice: %s", str(t['askPrice']))
                logging.info("vwap: %s", str(t['weightedAvgPrice']))
                logging.info("position: %s", str(t['position']))
                logging.info('-' * 20)
            return top_trades
    except Exception as e:
        logging.error(e)
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


def buy_selected(selected_buys):
    cur = CON.cursor()
    for i in selected_buys:
        cur.execute(
            """
                INSERT INTO gainers
                VALUES ('%s','%s','%s','%s','%s','%s','%s')
            """ % (
                i.get('symbol'),
                i.get('priceChangePercent'),
                i.get('askPrice'),
                0,
                i.get('weightedAvgPrice'),
                datetime.datetime.now(),
                i.get('position')))
    CON.commit()


def choose_sell_buy(top_change):
    cur = CON.cursor()
    cur.execute(
        """
            SELECT symbol, buy FROM gainers WHERE sell == 0.0;
        """)
    symbols = cur.fetchall()
    symbol_list = [i[0] for i in symbols]
    logging.info("### current buys in database")
    logging.info("symbol | buy price")
    for ix in symbols:
        logging.info(
            "{symbol} | {buy_price}".format(symbol=ix[0], buy_price=ix[1]))
    tc_symbol_list = []
    for tc in top_change:
        tc_symbol_list.append(tc['symbol'])
    will_sell = list(set(symbol_list) - set(tc_symbol_list))

    # modificar will_sell para agregar los que esten por debajo del VWAP
    not_selling = list(set(symbol_list) - set(will_sell))
    with open('json/top.json') as trades_file:
        trades = json.load(trades_file)
        for t in trades:
            curr_symbol = t['symbol']
            if curr_symbol in not_selling:
                vwap_price = Decimal(t['weightedAvgPrice'])
                askPrice = Decimal(t['askPrice'])
                if vwap_price > askPrice:
                    will_sell.append(curr_symbol)
    will_buy_symbols = list(set(tc_symbol_list) - set(symbol_list))
    will_buy = []
    for tc in top_change:
        if (len(symbol_list) - len(will_sell)) + len(will_buy) >= 5:
            break
        if tc.get('symbol') in will_buy_symbols:
            will_buy.append(tc)
    logging.info("### selling:")
    for ws in will_sell:
        logging.info(ws)
    logging.info("### buying:")
    for wb in will_buy:
        logging.info(wb.get('symbol'))
    sell_selected(will_sell)
    buy_selected(will_buy)


def clean_database():
    cur = CON.cursor()
    cur.execute(
        """
            delete FROM gainers;
        """)
    CON.commit()
    logging.info('clean database done')


def recreate_database():
    cur = CON.cursor()
    cur.execute(
        """
            DROP TABLE IF EXISTS gainers;
        """)
    cur.execute(
        """
            CREATE TABLE gainers (
               symbol TEXT NOT NULL,
               change REAL NOT NULL,
               buy REAL NOT NULL,
               sell REAL NOT NULL DEFAULT 0,
               weight REAL NOT NULL DEFAULT 0,
               date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               position INTEGER NOT NULL DEFAULT 0
            );
        """)
    CON.commit()
    logging.info('drop/create database gainers done')


def main():
    if get_trades_from_binance():
        top_price_change = get_top_price_change()
        choose_sell_buy(top_price_change)


if __name__ == '__main__':
    if '--clean' in sys.argv:
        logging.info("cleaning database")
        clean_database()
    if '--zap' in sys.argv:
        logging.info("recreating database")
        recreate_database()
    else:
        logging.info("#" * 80)
        logging.info("call main")
        main()
        logging.info("#" * 80)
