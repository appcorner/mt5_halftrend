# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime
from enum import Enum

import logging
logger = logging.getLogger('__main__')

CANDLE_PLOT = 100
CB_AUTO_MODE = 1
SWING_TF = 5
SWING_TEST = 2
TP_FIBO = 2
SIGNAL_INDEX = -2

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S' 
# DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S%z'

class Direction(Enum):
    LONG = "long"
    SHORT = "short"

def cal_callback_rate(symbol, entryPrice, targetPrice):
    rate = round(abs(entryPrice - targetPrice) / entryPrice * 100.0, 1)
    logger.debug(f'{symbol} closePrice:{entryPrice}, targetPrice:{targetPrice}, callback_rate:{rate}')
    if rate > 5.0:
        return 5.0
    elif rate < 0.1:
        return 0.1
    else:
        return rate

def cal_minmax_fibo(symbol, df, positionType=Direction.LONG, entryPrice=0.0, digits=5):
    iday = df.tail(CANDLE_PLOT)

    entryPrice = iday['close'].iloc[-1] if entryPrice == 0.0 else entryPrice

    # swing low
    periods = 3
    lows_list = list(iday['low'])
    lows_list.reverse()
    # logger.debug(lows_list)
    # swing_low = lows_list[0]
    swing_lows = []
    for i in range(len(lows_list)):
        if i >= periods:
            # Check if the current price is the lowest in the last `periods` periods
            if min(lows_list[i-periods:i+1]) == lows_list[i]:
                swing_lows.append(lows_list[i])
    # logger.debug(swing_lows)

    iday_minmax = iday[:CANDLE_PLOT+SIGNAL_INDEX]
    minimum_index = iday_minmax['low'].idxmin()
    minimum_price = iday_minmax['low'].min()
    maximum_index = iday_minmax['high'].idxmax()
    maximum_price = iday_minmax['high'].max()
    #Calculate the max high and min low price
    difference = maximum_price - minimum_price #Get the difference

    # fibo_values = [0,0.1618,0.236,0.382,0.5,0.618,0.786,1,1.382]
    fibo_values = [0,0.236,0.382,0.5,0.618,0.786,1,1.382]

    isFiboRetrace = True
    minmax_points = []
    fibo_levels = []
    periods = SWING_TF
    swing_lows = []
    swing_highs = []
    tp = 0.0
    sl = 0.0

    # logger.debug(minimum_index)
    # logger.debug(maximum_index)

    # iday_minmax['sw_low'] = np.nan
    # iday_minmax['sw_high'] = np.nan
    for i in range(len(iday_minmax)):
        if i >= periods:
            if min(iday_minmax['low'].iloc[i-periods:i+1+periods]) == iday_minmax['low'].iloc[i]:
                swing_lows.append(iday_minmax['low'].iloc[i])
                # iday_minmax['sw_low'].iloc[i] =  iday_minmax['low'].iloc[i]
            if max(iday_minmax['high'].iloc[i-periods:i+1+periods]) == iday_minmax['high'].iloc[i]:
                swing_highs.append(iday_minmax['high'].iloc[i])
                # iday_minmax['sw_high'].iloc[i] =  iday_minmax['low'].iloc[i]

    if positionType == Direction.LONG:
        isFiboRetrace = datetime.strptime(str(minimum_index), DATETIME_FORMAT) > datetime.strptime(str(maximum_index), DATETIME_FORMAT)
        # print(isFiboRetrace)

        if isFiboRetrace:
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((minimum_index,minimum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = minimum_price + difference * fibo_val
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice < fibo_level:
                    tp_fibo = min(idx+TP_FIBO, len(fibo_values)-1)
                    tp = minimum_price + difference * fibo_values[tp_fibo]
        else:
            # maxidx = np.where(iday_minmax.index==maximum_index)[0][0]
            maxidx = iday_minmax.index.get_loc(maximum_index)
            # print(maxidx)
            if maxidx < len(iday_minmax)-1:
                new_minimum_index = iday_minmax['low'].iloc[maxidx+1:].idxmin()
                new_minimum_price = iday_minmax['low'].iloc[maxidx+1:].min()
            else:
                new_minimum_index = iday_minmax['low'].iloc[maxidx:].idxmin()
                new_minimum_price = iday_minmax['low'].iloc[maxidx:].min()
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((new_minimum_index,new_minimum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = new_minimum_price + difference * fibo_val
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice < fibo_level:
                    tp_fibo = min(idx+TP_FIBO, len(fibo_values)-1)
                    tp = new_minimum_price + difference * fibo_values[tp_fibo]

        sl_fibo = entryPrice - difference * fibo_values[1]
        sl_sw = min(swing_lows[-SWING_TEST:])
        sl = min(sl_fibo, sl_sw)

    elif positionType == Direction.SHORT:
        isFiboRetrace = datetime.strptime(str(minimum_index), DATETIME_FORMAT) < datetime.strptime(str(maximum_index), DATETIME_FORMAT)
        # print(isFiboRetrace)

        if isFiboRetrace:
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((maximum_index,maximum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = maximum_price - difference * fibo_val
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice > fibo_level:
                    tp_fibo = min(idx+TP_FIBO, len(fibo_values)-1)
                    tp = maximum_price - difference * fibo_values[tp_fibo]
        else:
            # minidx = np.where(iday_minmax.index==minimum_index)[0][0]
            minidx = iday_minmax.index.get_loc(minimum_index)
            # print(maxidx)
            if minidx < len(iday_minmax)-1:
                new_maximum_index = iday_minmax['high'].iloc[minidx+1:].idxmax()
                new_maximum_price = iday_minmax['high'].iloc[minidx+1:].max()
            else:
                new_maximum_index = iday_minmax['high'].iloc[minidx:].idxmax()
                new_maximum_price = iday_minmax['high'].iloc[minidx:].max()
            minmax_points.append((maximum_index,maximum_price))
            minmax_points.append((minimum_index,minimum_price))
            minmax_points.append((new_maximum_index,new_maximum_price))
            for idx, fibo_val in enumerate(fibo_values):
                fibo_level = new_maximum_price - difference * fibo_val
                fibo_levels.append(fibo_level)
                if tp == 0.0 and entryPrice > fibo_level:
                    tp_fibo = min(idx+TP_FIBO, len(fibo_values)-1)
                    tp = new_maximum_price - difference * fibo_values[tp_fibo]

        sl_fibo = entryPrice + difference * fibo_values[1]
        sl_sw = max(swing_highs[-SWING_TEST:])
        sl = max(sl_fibo, sl_sw)

    if CB_AUTO_MODE == 1:
        callback_rate = cal_callback_rate(symbol, entryPrice, tp)
    else:
        callback_rate = cal_callback_rate(symbol, entryPrice, sl)

    return {
        'position' : 'BUY' if positionType == Direction.LONG else 'SELL',
        'fibo_type': 'retractment' if isFiboRetrace else 'extension',
        'difference': difference,
        'min_max': minmax_points, 
        'fibo_values': fibo_values,
        'fibo_levels': fibo_levels,
        'swing_highs': swing_highs,
        'swing_lows': swing_lows,
        'tp': round(tp, digits),
        'sl': round(sl, digits),
        'price': round(entryPrice, digits),
        'tp_txt': 'TP: (AUTO) @{}'.format(round(tp, digits)),
        'sl_txt': 'SL: (AUTO) @{}'.format(round(sl, digits)),
        'price_txt': 'Price: @{}'.format(round(entryPrice, digits)),
        'callback_rate': callback_rate
    }
