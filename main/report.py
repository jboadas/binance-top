import sqlite3
from decimal import Decimal
from datetime import datetime


con = sqlite3.connect('data/top.db')


def collect_sells(invested_amount):
    cur = con.cursor()
    cur.execute(
        """
            SELECT symbol, buy, sell, weight, date, position
            FROM gainers
            WHERE sell != 0.0
            ORDER BY date;
        """)
    trades = cur.fetchall()
    total_earnings = Decimal(0.0)
    print_date = "00-00-0000"
    for t in trades:
        symbol = t[0]
        share_price_buy = Decimal(t[1])
        share_price_sell = Decimal(t[2])
        weight = Decimal(t[3])
        curr_date = datetime.strptime(t[4], '%Y-%m-%d %H:%M:%S.%f')
        curr_date_str = curr_date.strftime('%d-%m-%Y %H:%M')
        position = int(t[5])
        if print_date != curr_date_str:
            print_date = curr_date_str
            print(" " * 80)
            print("%" * 80)
            print(print_date)
            print("%" * 80)
        share_amount_buyed = invested_amount / share_price_buy
        # share_amount_selled = invested_amount / share_price_sell
        curr_earnings = (
            share_amount_buyed * share_price_sell) - invested_amount
        # curr_earnings = (
        # share_amount_selled - share_amount_buyed) * share_price_sell
        print("-" * 80)
        print("symbol:", symbol)
        print('ganancias:', curr_earnings)
        print('posision', position)
        print('precio de compra:', share_price_buy)
        print('precio de venta:', share_price_sell)
        print('weight', weight)
        total_earnings += curr_earnings
    print("-" * 80)
    print("#" * 80)
    print("Total Earnings:", total_earnings)
    print("#" * 80)


invested_amount = Decimal(5)
collect_sells(invested_amount)
