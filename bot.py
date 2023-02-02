
#pip install python-binance pandas requests
from binance.client import Client
import pandas as pd
import requests

import time
import sys
import json

#to sync raspberry pi time
def update_time(unix_time_as_string):
    try:
        clk_id = time.CLOCK_REALTIME
        time.clock_settime(clk_id, float(unix_time_as_string))
    except AttributeError:
        pass

#adjust leverage and margin type
def adjust_lev_margtype(client, symbol, lev, marg_type):
    client.futures_change_leverage(symbol=symbol, leverage=lev) #1, 2, 5 10, 20 ...
    try:
        client.futures_change_margin_type(symbol=symbol, marginType=marg_type) #ISOLATED or CROSSED
    except BaseException:
        pass #margin already set

def create_fut_order(client, side, symbol, lev, marg_type, price, qty, stop_price):
    
    adjust_lev_margtype(client, symbol, lev, marg_type)

    if side == "BUY": #if creating a long contract
        side2 = "SELL"
    else: #if creating a short contract
        side2 = "BUY"
    try:
        client.futures_create_order(
            symbol=symbol,
            side=side2, #'SELL' or 'BUY'
            type ='TAKE_PROFIT',
            timeInForce='GTC', #Good until cancelled
            price = stop_price,
            reduceOnly= True,
            quantity = qty,
            stopPrice=stop_price,
            workingType='CONTRACT_PRICE' #or MARK PRICE
            )
        print(f"Take Profit {side2} order created for {qty} {symbol} at TP {stop_price}")

        client.futures_create_order(
            symbol=symbol,
            side=side, #'SELL' or 'BUY'
            type ='LIMIT',
            timeInForce='GTC',
            price = price,
            quantity = qty,
            workingType='CONTRACT_PRICE' #or MARK PRICE
            )
        print(f"{side} order created for {qty} {symbol} at {price}.")
    except BaseException as error:
        print(f"Error creating order. Check: ({error}).")
        sys.exit("Exiting bot...")

#main looping function -> checks balance, opens positions, pulls logic, initiates tardes 
def bot_main(client, lev, tar_profit, symbol, exb, pos_size):

    balance = client.futures_account_balance()

    for check_balance in balance:
        if check_balance["asset"] == "BUSD":
            busd_balance = float(check_balance["balance"])
        elif check_balance["asset"] == "USDT":
            usdt_balance = float(check_balance["balance"])
    
    total_balance = round(busd_balance + usdt_balance, 2)
    if total_balance < exb:
        sys.exit("Funds are too low. Please check. Exiting bot...")
    print(f"Total balance: {total_balance} = BUSD: {busd_balance} + USDT: {usdt_balance}")

    positions = client.futures_account()['positions']
    positions = [position for position in positions if float(position['positionAmt']) > 0]
    
    orders = client.futures_get_open_orders(symbol = symbol)
    if len(orders) == 0:
        
        position_size = pos_size
        position_size_leveraged = position_size * lev
        
        #simple moving averages (for 3,6,12,24 hours) - weighted
        smas = sma_trade_logic(symbol)

        ticker_data = client.futures_symbol_ticker(symbol = symbol)
        current_price = float(ticker_data["price"])
    
        qty = round(position_size_leveraged / current_price, 3)
        cp_adder = float(tar_profit / lev)
        
        if smas > current_price: #open long position
            side = "BUY"
            tp_price = round(current_price * (1 + cp_adder), 2)
        else: #open short position
            tp_price = round(current_price * (1 - cp_adder), 2)
            side = "SELL"

        create_fut_order(client, side, symbol, lev, 'ISOLATED', current_price, qty, tp_price)
    else:
        for order in orders:
            print(f"Open orders: {order['symbol']} -- {order['type']} -- {order['price']} -- TP at {order['stopPrice']}")
        
        cp = client.futures_symbol_ticker(symbol = symbol)
        print(f"Current price: {cp['price']}")

def get_hist_data(symbol):
    starttime = '1 month ago UTC' #starttime = '30 minutes ago UTC' for last 30 mins time # starttime = '1 Dec, 2017','1 Jan, 2018' for last month of 2017
    interval = '1h' #1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    bars = client.get_historical_klines(symbol, interval, starttime)

    for line in bars:
        del line[0:4]
        del line[1:]

    df = pd.DataFrame(bars, columns=['close']) #2 dimensional tabular data #['date', 'open', 'high', 'low', 'close'])
    return df
#simple moving average used for rudimentary side decision logic (short or long?)
def sma_trade_logic(symbol): 
    symbol_df = get_hist_data(symbol)
    symbol_df['3sma'] = symbol_df['close'].rolling(3).mean()
    symbol_df['6sma'] = symbol_df['close'].rolling(6).mean()
    symbol_df['12sma'] = symbol_df['close'].rolling(12).mean()
    symbol_df['24sma'] = symbol_df['close'].rolling(24).mean()

    h3 = symbol_df['3sma'].iloc[-1]
    h6 = symbol_df['6sma'].iloc[-1]
    h12 = symbol_df['12sma'].iloc[-1]
    h24 = symbol_df['24sma'].iloc[-1]

    w_avg = 0.6 * h3 + 0.2 * h6 + 0.1 * h12 + 0.1 * h24

    return w_avg

if __name__ == "__main__":

    print("Starting bot...")
    #change manually-------------------------###############################
    test = True #False for live trading
    symbol = 'ETHUSDT' #override for single selection
    cycle_time = 60 #check orders every x seconds...
    exit_balance = 500 #account terminal value -> when reached script terminates
    leverage = 30
    tar_profit = 0.035 #target profit for TakeProfit execution (in %)
    pos_size = 100 #in USDT, position size (non-leveraged) per trade
    #change manually-------------------------###############################

    url = "https://api.binance.com/api/v1/time"
    if test:
        api_key = "your_testnet_api_key_here"
        secret_key = "your_testnet_secret_key_here"
    else:
        api_key = "your_live_api_key_here"
        secret_key = "your_live_secret_key_here"

    client = Client(api_key, secret_key, testnet = test)

    while True:
        r = requests.get(url)
        result = json.loads(r.content)
        result = result["serverTime"]
        update_time(result)

        bot_main(client, lev = leverage, tar_profit = tar_profit, symbol = symbol, exb = exit_balance, pos_size = pos_size)
        print(f"Starting {cycle_time} second wait cycle. Terminate with Ctrl + C --- {time.ctime()}")
        time.sleep(cycle_time)

