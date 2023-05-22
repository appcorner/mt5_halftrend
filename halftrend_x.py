# -*- coding: utf-8 -*-

import asyncio
import MetaTrader5 as mt5
import pandas as pd
import os
import pathlib
import pytz
import time
from datetime import datetime
import pandas_ta as ta
from LineNotify import LineNotify

import config

import stupid_share
import stupid_halftrend_mt5

import logging
from logging.handlers import RotatingFileHandler

bot_name = 'HalfTrend'
bot_vesion = '1.0.3'

bot_fullname = f'MT5 {bot_name} version {bot_vesion}'

# ansi escape code
CLS_SCREEN = '\033[2J\033[1;1H' # cls + set top left
CLS_LINE = '\033[0J'
SHOW_CURSOR = '\033[?25h'
HIDE_CURSOR = '\033[?25l'
CRED  = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW  = '\33[33m'
CMAGENTA  = '\33[35m'
CCYAN  = '\33[36m'
CEND = '\033[0m'
CBOLD = '\33[1m'

mt5.initialize() #Open terminal MT5

notify = LineNotify(config.LINE_NOTIFY_TOKEN)

symbol = config.symbols[0]
tf = config.timeframe
lot = config.lot
deviation = config.deviation

magic_number = config.magic_number

user_id = config.LOGIN
server_user = config.SERVER
password_user = config.PASSWORD

TZ_ADJUST = 7
MT_ADJUST = 4

TIMEFRAME_SECONDS = {
    '1m': 60,
    '3m': 60*3,
    '5m': 60*5,
    '15m': 60*15,
    '30m': 60*30,
    '1h': 60*60,
    '2h': 60*60*2,
    '4h': 60*60*4,
    '6h': 60*60*6,
    '8h': 60*60*8,
    '12h': 60*60*12,
    '1d': 60*60*24,
}
UB_TIMER_SECONDS = [
    TIMEFRAME_SECONDS[config.timeframe],
    10,
    15,
    20,
    30,
    60,
    int(TIMEFRAME_SECONDS[config.timeframe]/2)
]

SHOW_COLUMNS = ['symbol', 'identifier', 'type', 'volume', 'price_open', 'sl', 'tp', 'price_current', 'profit', 'comment', 'magic']
RENAME_COLUMNS = ['Symbol', 'Ticket', 'Type', 'Volume', 'Price', 'S/L', 'T/P', 'Last', 'Profit', 'Comment', 'Magic']

ORDER_TYPE = ["buy","sell","buy limit","sell limit","buy stop","sell stop","buy stop limit","sell stop limit","close"]

symbols_list = []
all_stat = {}

def trade_buy(symbol, price, lot=lot, tp=0.0, sl=0.0, magic_number=magic_number, step=0):
    point = mt5.symbol_info(symbol).point
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "deviation": deviation,
        "magic": magic_number,
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    if sl > 0:
        request["sl"] = sl
    if 'sl' in request.keys():
        sl_pips = int(abs(price - request['sl']) / point + 0.5)
        request["comment"] = "HT-{}-{}".format(sl_pips,step)
    else:
        request["comment"] = "HT-{}".format(step)
    if tp > 0:
        request["tp"] = tp
    logger.info(f"{symbol} trade_buy :: request = {request}")
    # send a trading request
    result = mt5.order_send(request)
    position_id_buy = 0
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.info(f"{symbol} trade_buy :: order_send failed, retcode = {result.retcode}")
        logger.debug(f"{symbol} trade_buy :: result = {result}")
    else:
        logger.info(f"{symbol} trade_buy :: order = {result.order}")
        t_req = result.request
        logger.debug(f"{symbol} trade_buy :: result.request = {t_req}")
        notify.Send_Text(f"{symbol}\nTrade Buy\nPrice = {t_req.price}\nLot = {t_req.volume}\nTP = {t_req.tp}\nSL = {t_req.sl}")
        position_id_buy = result.order
    return position_id_buy

def close_buy(symbol, position_id, lot, price_open):
    price = mt5.symbol_info_tick(symbol).bid
    profit = 0.0
    if price_open > 0.0:
        profit = (price - price_open)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "position": position_id,
        "price": price,
        "deviation": deviation,
        "magic": magic_number,
        "comment": "HT",
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    # send a trading request
    result = mt5.order_send(request)
    position_id_close_buy = 0
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.info(f"{symbol} close_buy :: order_send failed, retcode = {result.retcode}")
        logger.debug(f"{symbol} close_buy :: result = {result}")
    else:
        logger.info(f"{symbol} close_buy :: order = {result.order}")
        t_req = result.request
        logger.debug(f"{symbol} close_buy :: result.request = {t_req}")
        notify.Send_Text(f"{symbol}\nTrade Close Buy\nPrice = {t_req.price}\nProfit = {profit:.2f}")
        position_id_close_buy = result.order
    return position_id_close_buy

def trade_sell(symbol, price, lot=lot, tp=0.0, sl=0.0, magic_number=magic_number, step=0):
    point = mt5.symbol_info(symbol).point 
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "deviation": deviation,
        "magic": magic_number,
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    if sl > 0:
        request["sl"] = sl
    if 'sl' in request.keys():
        sl_pips = int(abs(price - request['sl']) / point + 0.5)
        request["comment"] = "HT-{}-{}".format(sl_pips,step)
    else:
        request["comment"] = "HT-{}".format(step)
    if tp > 0:
        request["tp"] = tp
    logger.info(f"{symbol} trade_sell :: request = {request}")
    # send a trading request
    result = mt5.order_send(request)
    position_id_sell = 0
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.info(f"{symbol} trade_sell :: order_send failed, retcode = {result.retcode}")
        logger.debug(f"{symbol} trade_sell :: result = {result}")
    else:
        logger.info(f"{symbol} trade_sell :: order = {result.order}")
        t_req = result.request
        logger.debug(f"{symbol} trade_sell :: result.request = {t_req}")
        notify.Send_Text(f"{symbol}\nTrade Sell\nPrice = {t_req.price}\nLot = {t_req.volume}\nTP = {t_req.tp}\nSL = {t_req.sl}")
        position_id_sell = result.order
    return position_id_sell  

def close_sell(symbol, position_id, lot, price_open):
    price = mt5.symbol_info_tick(symbol).ask
    profit = 0.0
    if price_open > 0.0:
        profit = (price_open - price)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "position": position_id,
        "price": price,
        "deviation": deviation,
        "magic": magic_number,
        "comment": "HT",
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    # send a trading request
    result = mt5.order_send(request)
    position_id_close_sell = 0
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.info(f"{symbol} close_sell :: order_send failed, retcode = {result.retcode}")
        logger.debug(f"{symbol} close_sell :: result = {result}")
    else:
        logger.info(f"{symbol} close_sell :: order = {result.order}")
        t_req = result.request
        logger.debug(f"{symbol} close_sell :: result.request = {t_req}")
        notify.Send_Text(f"{symbol}\nTrade Close Sell\nPrice = {t_req.price}\nProfit = {profit:0.2f}")
        position_id_close_sell = result.order
    return position_id_close_sell

# Function to modify an open position
def modify_position(symbol, position_id, new_sl, new_tp, trailing_stop_pips, step=0, magic_number=magic_number):
    # Create the request
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "sl": new_sl,
        "tp": new_tp,
        "position": position_id,
        "magic": magic_number,
    }
    # Send order to MT5
    result = mt5.order_send(request)
    logger.debug(f"{symbol} modify_position :: retcode = {result.retcode}")
    logger.debug(f"{symbol} modify_position :: result = {result}")
    if result[0] == 10009:
        logger.info(f"{symbol} modify_position :: order = {result.order}")
        return True
    else:
        return False
# Function to update trailing stop if needed
def update_trailing_stop(position):
    symbol = position['symbol']
    symbol_info = mt5.symbol_info(symbol)
    symbol_digits = symbol_info.digits
    pip_size = symbol_info.point
    comment_info = position["comment"].split("-")
    if len(comment_info) != 3:
        # logger.debug(f"{symbol} skip update_trailing_stop :: comment_info = {comment_info}")
        return
    step = int(comment_info[-1])
    trailing_stop_pips = int(comment_info[-2])

    # Convert trailing_stop_pips into pips
    trailing_stop_price = trailing_stop_pips * pip_size
    # Determine if Red or Green
    # A Green Position will have a take_profit > stop_loss
    if position['tp'] > position['sl']:
        # If Green, new_stop_loss = current_price - trailing_stop_price
        new_stop_loss = position['price_current'] - trailing_stop_price
        # Test to see if new_stop_loss > current_stop_loss
        if new_stop_loss > position['sl']:
            # Create updated values for order
            position_id = position['ticket']
            # New take_profit will be the difference between new_stop_loss and old_stop_loss added to take profit
            new_take_profit = position['tp'] + new_stop_loss - position['sl']
            logger.debug(f"{symbol} buy :: pip_size={pip_size:.8f} trailing_stop_pips={trailing_stop_pips}")
            logger.debug(f"{symbol} buy :: {position['sl']:.8f}/{position['tp']:.8f} new sl/tp={new_stop_loss:.8f}/{new_take_profit:.8f}")
            # Send order to modify_position
            modify_position(symbol, position_id, round(new_stop_loss, symbol_digits) , round(new_take_profit, symbol_digits), trailing_stop_pips, step)
    # A Red Position will have a take_profit < stop_loss
    elif position['tp'] < position['sl']:
        # If Red, new_stop_loss = current_price + trailing_stop_price
        new_stop_loss = position['price_current'] + trailing_stop_price
        # Test to see if new_stop_loss < current_stop_loss
        if new_stop_loss < position['sl']:
            # Create updated values for order
            position_id = position['ticket']
            # New take_profit will be the difference between new_stop_loss and old_stop_loss subtracted from old take_profit
            new_take_profit = position['tp'] - new_stop_loss + position['sl']
            logger.debug(f"{symbol} sell :: pip_size={pip_size:.8f} trailing_stop_pips={trailing_stop_pips}")
            logger.debug(f"{symbol} sell :: {position['sl']:.8f}/{position['tp']:.8f} new sl/tp={new_stop_loss:.8f}/{new_take_profit:.8f}")
            # Send order to modify_position
            modify_position(symbol, position_id, round(new_stop_loss, symbol_digits), round(new_take_profit, symbol_digits), trailing_stop_pips, step)
    
def show_bid_ask(symbol):
    symbol_tick = mt5.symbol_info_tick(symbol)
    ask_price = symbol_tick.ask
    bid_price = symbol_tick.bid
    print(f"\rAsk Price : {ask_price} Bid Price : {bid_price}")

def positions_check(positions, old_position_ids):
    if len(positions) == 0:
        return
    current_position_ids = positions["ticket"].tolist()
    position_ids = [id for id in old_position_ids if id not in current_position_ids]
    for position_id in position_ids:
        position_history_orders = mt5.history_orders_get(position=position_id)
        if position_history_orders != None and len(position_history_orders) >= 2:
            logger.debug(f"position_id = {position_id}")
            df = pd.DataFrame(list(position_history_orders),columns=position_history_orders[0]._asdict().keys())
            # df.drop(['time_setup','time_setup_msc','time_expiration','type_time','state','position_by_id','reason','volume_current','price_stoplimit','sl','tp'], axis=1, inplace=True)
            # df['time_setup'] = pd.to_datetime(df['time_setup'], unit='s')
            # df['time_done'] = pd.to_datetime(df['time_done'], unit='s')
            # logger.debug(f"\n{df.columns}")
            symbol = df['symbol'].iloc[0]
            point = mt5.symbol_info(symbol).point
            logger.debug(f"{symbol}\n{df[['position_id', 'type', 'type_filling', 'volume_initial', 'price_open', 'price_current', 'comment']]}")
            close_by = ''
            price_current = 0.0
            profit = 0.0
            for idx, row in df.iterrows():
                profit += (-1 if row['type'] == 0 else 1) * row['price_current'] * row['volume_initial'] / point
                if 'tp' in row['comment']:
                    close_by = 'TP'
                    price_current = row['price_current']
                elif 'sl' in row['comment']:
                    close_by = 'SL'
                    price_current = row['price_current']
                # logger.debug(f"profit = {profit}")
            all_stat[symbol]["summary_profit"] += round(profit , 2)
            if profit > 0:
                all_stat[symbol]["win"] += 1
                all_stat[symbol]["last_loss"] = 0
            elif profit < 0:
                all_stat[symbol]["loss"] += 1
                all_stat[symbol]["last_loss"] += 1
            if close_by != '':
                notify.Send_Text(f"{symbol}\nTrade {close_by}\nPrice = {price_current}\nProfit = {profit:.2f}")

def positions_getall(symbols_list):
    res = mt5.positions_get()
    if(res is not None and res != ()):
        all_columns = res[0]._asdict().keys()
        df = pd.DataFrame(list(res),columns=all_columns)
        # df["time"] = pd.to_datetime(df["time"], unit="s")
        df["time"] = pd.to_datetime(df["time"], unit="s").map(
            lambda x: x+pd.Timedelta(hours=MT_ADJUST)
        )
        df["type"] = df["type"].map(lambda x: ORDER_TYPE[x])
        df.drop(df[df["symbol"].isin(symbols_list) == False].index, inplace=True)
        # logger.debug(df.columns)
        return df
    
    return pd.DataFrame()
def positions_get(symbol):
    res = mt5.positions_get(symbol=symbol)
    if(res is not None and res != ()):
        all_columns = res[0]._asdict().keys()
        df = pd.DataFrame(list(res),columns=all_columns)
        # df["time"] = pd.to_datetime(df["time"], unit="s")
        df["time"] = pd.to_datetime(df["time"], unit="s").map(
            lambda x: x+pd.Timedelta(hours=MT_ADJUST)
        )
        df["type"] = df["type"].map(lambda x: ORDER_TYPE[x])
        # logger.debug(df.columns)
        return df
    
    return pd.DataFrame()

def cal_martingal_lot(symbol):
    cal_lot = config.lot
    if config.is_martingale and config.martingale_max > 0:
        if all_stat[symbol]["last_loss"] < config.martingale_max:
            if config.martingale_factor == 1:
                cal_lot = round(config.lot * (all_stat[symbol]["last_loss"]+1), 2)
            else:
                cal_lot = round(config.lot * (config.martingale_factor ** all_stat[symbol]["last_loss"]), 2)
        else:
            if config.martingale_factor == 1:
                cal_lot = round(config.lot * config.martingale_max, 2)
            else:
                cal_lot = round(config.lot * (config.martingale_factor ** config.martingale_max), 2)
    return cal_lot

async def trade(symbol, next_ticker):
    await stupid_halftrend_mt5.fetch_ohlcv(trade_mt5, symbol, tf, limit=0, timestamp=next_ticker)
    logger.debug(f'{symbol}::\n{stupid_halftrend_mt5.all_candles[symbol].tail(3)}')
    try:
        is_long, is_short = stupid_halftrend_mt5.get_signal(symbol, config.signal_index)
        logger.info(f'{symbol} :: is_long={is_long}, is_short={is_short}')

        symbol_info = mt5.symbol_info(symbol)
        symbol_digits = symbol_info.digits
        symbol_point = symbol_info.point
        fibo_data = None
        msg = ""
        if is_long:
            # close all sell
            all_positions = positions_get(symbol)
            for index, position in all_positions.iterrows():
                if position["symbol"] == symbol and position["type"] == ORDER_TYPE[1] and position["magic"] == magic_number:
                    position_id = close_sell(symbol, position['identifier'], position['volume'], position['price_open'])
                    all_stat[symbol]["summary_profit"] += position['profit']
                    if position['profit'] > 0:
                        all_stat[symbol]["win"] += 1
                        all_stat[symbol]["last_loss"] = 0
                        # all_stat[symbol]["martingale_profit"] = 0
                    else:
                        all_stat[symbol]["loss"] += 1
                        all_stat[symbol]["last_loss"] += 1
                        # all_stat[symbol]["martingale_profit"] += position['profit']
            # calculate fibo
            price_buy = mt5.symbol_info_tick(symbol).ask
            cal_lot = cal_martingal_lot(symbol)
            tp = 0.0
            sl = 0.0
            if config.is_auto_tpsl:
                fibo_data = stupid_share.cal_minmax_fibo(symbol, stupid_halftrend_mt5.all_candles[symbol], stupid_share.Direction.LONG, entryPrice=price_buy, digits=symbol_digits)
                tp = fibo_data['tp']
                sl = fibo_data['sl']
            else:
                fibo_data = {
                    'position' : 'BUY',
                    'price': round(price_buy, symbol_digits),
                    'price_txt': 'Price: @{}'.format(round(price_buy, symbol_digits)),
                }
                if config.tp > 0:
                    if config.is_tp_percent:
                        tp = round(price_buy + (price_buy * config.tp), symbol_digits)
                        tp_mode = '{:.2f}%'.format(config.tp * 100)
                    else:
                        tp = round(price_buy + config.tp * symbol_point, symbol_digits)
                        tp_mode = ''
                    fibo_data['tp'] = tp
                    fibo_data['tp_txt'] = 'TP: {} @{}'.format(tp_mode, round(tp, symbol_digits))
                if config.sl > 0:
                    if config.is_sl_percent:
                        sl = round(price_buy - (price_buy * config.sl), symbol_digits)
                        sl_mode = '{:.2f}%'.format(config.sl * 100)
                    else:
                        sl = round(price_buy - config.sl * symbol_point, symbol_digits)
                        sl_mode = ''
                    fibo_data['sl'] = sl
                    fibo_data['sl_txt'] = 'SL: {} @{}'.format(sl_mode, round(sl, symbol_digits))
            position_id = trade_buy(symbol, price_buy, lot=cal_lot, tp=tp, sl=sl, step=all_stat[symbol]["last_loss"])
            msg = f"Signal Long {symbol}\nticker: {position_id}"
            print(msg)
        elif is_short:
            # close all buy
            all_positions = positions_get(symbol)
            for index, position in all_positions.iterrows():
                if position["symbol"] == symbol and position["type"] == ORDER_TYPE[0] and position["magic"] == magic_number:
                    position_id = close_buy(symbol, position['identifier'], position['volume'], position['price_open'])
                    all_stat[symbol]["summary_profit"] += position['profit']
                    if position['profit'] > 0:
                        all_stat[symbol]["win"] += 1
                        all_stat[symbol]["last_loss"] = 0
                        # all_stat[symbol]["martingale_profit"] = 0
                    else:
                        all_stat[symbol]["loss"] += 1
                        all_stat[symbol]["last_loss"] += 1
                        # all_stat[symbol]["martingale_profit"] += position['profit']
            # calculate fibo
            price_sell = mt5.symbol_info_tick(symbol).bid
            cal_lot = cal_martingal_lot(symbol)
            tp = 0.0
            sl = 0.0
            if config.is_auto_tpsl:
                fibo_data = stupid_share.cal_minmax_fibo(symbol, stupid_halftrend_mt5.all_candles[symbol], stupid_share.Direction.SHORT, entryPrice=price_sell, digits=symbol_digits)
                tp = fibo_data['tp']
                sl = fibo_data['sl']
            else:
                fibo_data = {
                    'position' : 'SELL',
                    'price': round(price_sell, symbol_digits),
                    'price_txt': 'Price: @{}'.format(round(price_sell, symbol_digits)),
                }
                if config.tp > 0:
                    if config.is_tp_percent:
                        tp = round(price_sell - (price_sell * config.tp), symbol_digits)
                        tp_mode = '{:.2f}%'.format(config.tp * 100)
                    else:
                        tp = round(price_sell - config.tp * symbol_point, symbol_digits)
                        tp_mode = ''
                    fibo_data['tp'] = tp
                    fibo_data['tp_txt'] = 'TP: {} @{}'.format(tp_mode, round(tp, symbol_digits))
                if config.sl > 0:
                    if config.is_sl_percent:
                        sl = round(price_sell + (price_sell * config.sl), symbol_digits)
                        sl_mode = '{:.2f}%'.format(config.sl * 100)
                    else:
                        sl = round(price_sell + config.sl * symbol_point, symbol_digits)
                        sl_mode = ''
                    fibo_data['sl'] = sl
                    fibo_data['sl_txt'] = 'SL: {} @{}'.format(sl_mode, round(sl, symbol_digits))
            position_id = trade_sell(symbol, price_sell, lot=cal_lot, tp=tp, sl=sl, step=all_stat[symbol]["last_loss"])
            msg = f"Signal Short {symbol}\nticker: {position_id}"
            print(msg)

        if is_long or is_short:
            filename = ''
            if fibo_data:
                filename = await stupid_halftrend_mt5.chart(symbol, tf, showMACDRSI=True, fiboData=fibo_data)
            else:
                filename = await stupid_halftrend_mt5.chart(symbol, tf, showMACDRSI=True)
            notify.Send_Image(msg, image_path=filename)

    except Exception as ex:
        print(f"{symbol} found error:", type(ex).__name__, str(ex))
        logger.exception(f'trade - {symbol}')
        pass

async def init_symbol_ohlcv(symbol):
    logger.info(f"init_symbol_ohlcv - {symbol}")
    symbol_info = mt5.symbol_info(symbol)
    symbol_digits = symbol_info.digits
    symbol_point = symbol_info.point
    symbol_info_tick = mt5.symbol_info_tick(symbol)
    await stupid_halftrend_mt5.fetch_ohlcv(trade_mt5, symbol, tf, limit=stupid_halftrend_mt5.CANDLE_LIMIT)
    trend_direction = stupid_share.Direction.SHORT
    price_entry = symbol_info_tick.bid
    if stupid_halftrend_mt5.all_candles[symbol]['trend'][-1] == 'long':
        trend_direction = stupid_share.Direction.LONG
        price_entry = symbol_info_tick.ask
    if config.is_auto_tpsl:
        fibo_data = stupid_share.cal_minmax_fibo(symbol, stupid_halftrend_mt5.all_candles[symbol], trend_direction, entryPrice=price_entry, digits=symbol_digits)
    else:
        fibo_data = {
            'position' : 'BUY' if trend_direction == stupid_share.Direction.LONG else 'SELL',
            'price': round(price_entry, symbol_digits),
            'price_txt': 'Price: @{}'.format(round(price_entry, symbol_digits)),
        }
        if config.tp > 0:
            tp_mode = '{:.2f}%'.format(config.tp * 100) if config.is_tp_percent else ''
            if config.is_tp_percent:
                tp_price = price_entry * config.tp
            else:
                tp_price = config.tp * symbol_point
            if trend_direction == stupid_share.Direction.LONG:
                tp = round(price_entry + tp_price, symbol_digits)
            else:
                tp = round(price_entry - tp_price, symbol_digits)
            fibo_data['tp'] = tp
            fibo_data['tp_txt'] = 'TP: {} @{}'.format(tp_mode, round(tp, symbol_digits))
        if config.sl > 0:
            sl_mode = '{:.2f}%'.format(config.sl * 100) if config.is_sl_percent else ''
            if config.is_sl_percent:
                sl_price = price_entry * config.sl
            else:
                sl_price = config.sl * symbol_point
            if trend_direction == stupid_share.Direction.LONG:
                sl = round(price_entry - sl_price, symbol_digits)
            else:
                sl = round(price_entry + sl_price, symbol_digits)
            fibo_data['sl'] = sl
            fibo_data['sl_txt'] = 'SL: {} @{}'.format(sl_mode, round(sl, symbol_digits))
    await stupid_halftrend_mt5.chart(symbol, tf, showMACDRSI=True, fiboData=fibo_data)

async def main():
    for symbol in config.symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(symbol, "not found, can not call order_check()")
            # mt5.shutdown()
            # quit()
            continue
            
        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            print(symbol, "is not visible, trying to switch on")
            if not mt5.symbol_select(symbol,True):
                print("symbol_select({}}) failed, exit",symbol)
                # mt5.shutdown()
                # quit()
                continue
        symbols_list.append(symbol)

    if len(symbols_list) == 0:
        print("Empty symbols list")
        mt5.shutdown()
        quit()

    # orders = mt5.orders_total()
    # if orders > 0:
    #     print("Total orders=",orders)
    # else:
    #     print("Orders not found")

    indy_config = stupid_halftrend_mt5.indicator_config
    indy_config["atrlen"] = config.atrlen
    indy_config["amplitude"] = config.amplitude
    indy_config["channel_deviation"] = config.channel_deviation
    logger.debug(indy_config)
    stupid_halftrend_mt5.set_config(indy_config)

    # init all symbol ohlcv
    call_inits = [init_symbol_ohlcv(symbol) for symbol in symbols_list]
    await asyncio.gather(*call_inits)

    logger.debug(f'{symbol}::\n{stupid_halftrend_mt5.all_candles[symbol].tail(3)}')

    # init all symbol stat
    all_positions = positions_getall(symbols_list)
    for symbol in symbols_list:
        if symbol not in all_stat.keys():
            all_stat[symbol] = {
                "win": 0,
                "loss": 0,
                "last_loss": 0,
                "summary_profit": 0,
                # "trailing_stop_pips": 0,
            }
    for index, position in all_positions.iterrows():
        if position["magic"] == magic_number and '-' in position["comment"]:
            step = int(position["comment"].split("-")[-1])
            all_stat[position['symbol']]["last_loss"] = step

    time_wait = TIMEFRAME_SECONDS[tf]
    next_ticker = time.time()
    next_ticker -= next_ticker % time_wait
    next_ticker += time_wait

    time_update = UB_TIMER_SECONDS[config.UB_TIMER_MODE]
    next_update =  time.time()
    next_update -= next_update % time_update
    next_update += time_update
    
    while True:

        t1 = time.time()
        seconds = time.time()
        local_time = time.ctime(seconds)

        if seconds >= next_update:  # ครบรอบ ปรับปรุงข้อมูล
            next_update += time_update
            # if os.name == "posix":
            #     os.system("clear")
            # else:
            #     os.system("cls")

            print(CLS_SCREEN+f"{bot_fullname}\nBot start process {local_time}\nTime Frame = {tf}, Martingale = {'on' if config.is_martingale else 'off'}")
            
            # prepare old position ids
            old_position_ids = []
            for index, position in all_positions.iterrows():
                if position["symbol"] in symbols_list and position["magic"] == magic_number:
                    old_position_ids.append(position["ticket"])
            
            # get new positions
            all_positions = positions_getall(symbols_list)

            # update trailing stop
            if config.is_trailing_stop:
                for index, position in all_positions.iterrows():
                    if position["symbol"] in symbols_list and position["magic"] == magic_number and '-' in position["comment"]:
                        update_trailing_stop(position)

            # check all close positions
            positions_check(all_positions, old_position_ids)

            if len(all_positions) > 0:
                all_positions.sort_values(by=['profit'], ignore_index=True, ascending=False, inplace=True)
                all_positions.index = all_positions.index + 1
                display_positions = all_positions[SHOW_COLUMNS]
                display_positions.columns = RENAME_COLUMNS
                print(display_positions)
                print(f"Total Profit   : {sum(display_positions['Profit']):,.2f}")
            else:
                print("No Positions")
            summary_columns = ["Symbol", "Win", "Loss", "Gale", "Profit"]
            summary_rows = []
            for symbol in all_stat.keys():
                summary_rows.append([symbol,all_stat[symbol]["win"],all_stat[symbol]["loss"],all_stat[symbol]["last_loss"],'{:0.2f}'.format(all_stat[symbol]["summary_profit"])])
            summary_df = pd.DataFrame(summary_rows,columns=summary_columns)
            summary_df.sort_values(by=['Profit'], ignore_index=True, ascending=False, inplace=True)
            summary_df.index = summary_df.index + 1
            print(summary_df)

        if seconds >= next_ticker + config.TIME_SHIFT:  # ครบรอบ
            # trade all symbol
            call_trades = [trade(symbol, next_ticker) for symbol in symbols_list]
            await asyncio.gather(*call_trades)
            next_ticker += time_wait

        await asyncio.sleep(1)
        # show_bid_ask(symbol)
        # print(positions_get(symbol))

async def waiting():
    count = 0
    status = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    while True:
        await asyncio.sleep(1)
        print('\r'+CCYAN+CBOLD+status[count%len(status)]+' waiting...\r'+CEND, end='')
        count += 1
        count = count%len(status)

if __name__ == "__main__":
    try:
        pathlib.Path('./plots').mkdir(parents=True, exist_ok=True)
        pathlib.Path('./logs').mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(__name__)
        logger.setLevel(config.LOG_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler = RotatingFileHandler('./logs/app.log', maxBytes=250000, backupCount=10)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info(f"===== Start :: HalfTrend :: {tf} =====")

        # display data on the MetaTrader 5 package
        print("MetaTrader5 package author: ", mt5.__author__)
        print("MetaTrader5 package version: ", mt5.__version__)

        trade_mt5 = mt5.login(login=int(user_id),server=server_user,password=password_user) # Login
        if trade_mt5:
            #print(mt5.account_info())#information from server
            account_info_dict = mt5.account_info()._asdict()#information()to{}
            #print(account_info_dict)
            account_info_list=list(account_info_dict.items())#Change {} to list
            #print(account_info_list)
            # df=pd.DataFrame(account_info_list,columns=['property','value'])#Convert list to data list table
            # print(df)
        else:
            print("No Connect")
            quit()
        
        os.system("color") # enables ansi escape characters in terminal
        print(HIDE_CURSOR, end="")
        loop = asyncio.get_event_loop()
        # แสดง status waiting ระหว่างที่รอ...
        loop.create_task(waiting())
        loop.run_until_complete(main())

    except KeyboardInterrupt:
        print(CLS_LINE+'\rbye')

    except Exception as ex:
        print(type(ex).__name__, str(ex))
        logger.exception('app')
        notify.Send_Text(f'{bot_name} bot stop')

    finally:
        print(SHOW_CURSOR, end="")