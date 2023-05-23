# -*- coding: utf-8 -*-

import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import mplfinance as mpf
import matplotlib.pyplot as plt
import numpy as np
import pytz
import time
from datetime import datetime

import logging
logger = logging.getLogger('__main__')

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
TIMEFRAME_MT5 = {
    '1m': mt5.TIMEFRAME_M1,
    '3m': mt5.TIMEFRAME_M3,
    '5m': mt5.TIMEFRAME_M5,
    '15m': mt5.TIMEFRAME_M15,
    '30m': mt5.TIMEFRAME_M30,
    '1h': mt5.TIMEFRAME_H1,
    '2h': mt5.TIMEFRAME_H2,
    '4h': mt5.TIMEFRAME_H4,
    '6h': mt5.TIMEFRAME_H6,
    '8h': mt5.TIMEFRAME_H8,
    '12h': mt5.TIMEFRAME_H12,
    '1d': mt5.TIMEFRAME_D1,
}

TZ_ADJUST = 7
MT_ADJUST = 4

CANDLE_LIMIT = 200
CANDLE_PLOT = 100
CANDLE_SAVE = CANDLE_PLOT + 100

all_candles = {}

indicator_config = {
    "RSI_PERIOD": 14,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "atrlen": 100,
    "amplitude": 3,
    "channel_deviation": 2,
}

# //@version=4
# // Copyright (c) 2021-present, Alex Orekhov (everget)
# study("HalfTrend", overlay=true)

# amplitude = input(title="Amplitude", defval=2)
# channelDeviation = input(title="Channel Deviation", defval=2)
# showArrows = input(title="Show Arrows", defval=true)
# showChannels = input(title="Show Channels", defval=true)

# var int trend = 0
# var int nextTrend = 0
# var float maxLowPrice = nz(low[1], low)
# var float minHighPrice = nz(high[1], high)

# var float up = 0.0
# var float down = 0.0
# float atrHigh = 0.0
# float atrLow = 0.0
# float arrowUp = na
# float arrowDown = na

# atr2 = atr(100) / 2
# dev = channelDeviation * atr2

# highPrice = high[abs(highestbars(amplitude))]
# lowPrice = low[abs(lowestbars(amplitude))]
# highma = sma(high, amplitude)
# lowma = sma(low, amplitude)

# if nextTrend == 1
# 	maxLowPrice := max(lowPrice, maxLowPrice)

# 	if highma < maxLowPrice and close < nz(low[1], low)
# 		trend := 1
# 		nextTrend := 0
# 		minHighPrice := highPrice
# else
# 	minHighPrice := min(highPrice, minHighPrice)

# 	if lowma > minHighPrice and close > nz(high[1], high)
# 		trend := 0
# 		nextTrend := 1
# 		maxLowPrice := lowPrice

# if trend == 0
# 	if not na(trend[1]) and trend[1] != 0
# 		up := na(down[1]) ? down : down[1]
# 		arrowUp := up - atr2
# 	else
# 		up := na(up[1]) ? maxLowPrice : max(maxLowPrice, up[1])
# 	atrHigh := up + dev
# 	atrLow := up - dev
# else
# 	if not na(trend[1]) and trend[1] != 1 
# 		down := na(up[1]) ? up : up[1]
# 		arrowDown := down + atr2
# 	else
# 		down := na(down[1]) ? minHighPrice : min(minHighPrice, down[1])
# 	atrHigh := down + dev
# 	atrLow := down - dev

# ht = trend == 0 ? up : down

# var color buyColor = color.blue
# var color sellColor = color.red

# htColor = trend == 0 ? buyColor : sellColor
# htPlot = plot(ht, title="HalfTrend", linewidth=2, color=htColor)

# atrHighPlot = plot(showChannels ? atrHigh : na, title="ATR High", style=plot.style_circles, color=sellColor)
# atrLowPlot = plot(showChannels ? atrLow : na, title="ATR Low", style=plot.style_circles, color=buyColor)

# fill(htPlot, atrHighPlot, title="ATR High Ribbon", color=sellColor)
# fill(htPlot, atrLowPlot, title="ATR Low Ribbon", color=buyColor)

# buySignal = not na(arrowUp) and (trend == 0 and trend[1] == 1)
# sellSignal = not na(arrowDown) and (trend == 1 and trend[1] == 0)

# plotshape(showArrows and buySignal ? atrLow : na, title="Arrow Up", style=shape.triangleup, location=location.absolute, size=size.tiny, color=buyColor)
# plotshape(showArrows and sellSignal ? atrHigh : na, title="Arrow Down", style=shape.triangledown, location=location.absolute, size=size.tiny, color=sellColor)

# alertcondition(buySignal, title="Alert: HalfTrend Buy", message="HalfTrend Buy")
# alertcondition(sellSignal, title="Alert: HalfTrend Sell", message="HalfTrend Sell")

def nz(value, default):
	return default if pd.isnull(value) else value
def na(value):
    return pd.isnull(value)

def set_config(config):
    global indicator_config
    for key in indicator_config.keys():
        if key in config.keys():
            indicator_config[key] = config[key]

def halftrend(df, atrlen, amplitude, channelDeviation):
    out = []
    trend = 0
    nextTrend = 0
    up = 0.0
    down = 0.0
    atrHigh = 0.0
    atrLow = 0.0
    direction = None

    atr = ta.atr(df.high, df.low, df.close, atrlen)
    highma = ta.sma(df.high, amplitude)
    lowma = ta.sma(df.low, amplitude)
    highestbars = df.rolling(amplitude, min_periods=1)['high'].max()
    lowestbars = df.rolling(amplitude, min_periods=1)['low'].min()
    df['highestbars'] = highestbars
    df['lowestbars'] = lowestbars

    arrTrend = [None] * len(df)
    arrUp = [None] * len(df)
    arrDown = [None] * len(df)

    maxLowPrice = df.iloc[atrlen-1]['low']
    minHighPrice = df.iloc[atrlen-1]['high']
    # print('maxLowPrice', maxLowPrice, 'minHighPrice', minHighPrice)

    if df['close'][0] > df['low'][atrlen]:
        trend = 1
        nextTrend = 1

    for i in range(1, len(df)):      
        atr2 = atr[i] / 2.0
        dev = channelDeviation * atr2

        highPrice = highestbars[i]
        lowPrice = lowestbars[i]

        # print(i, trend, nextTrend)

        if nextTrend == 1:
            maxLowPrice = max(lowPrice, maxLowPrice)
            # print(i, highma[i], maxLowPrice, df['close'][i], df['low'][i-1])
            if highma[i] < maxLowPrice and df['close'][i] < nz(df['low'][i-1], df['low'][i]):
                # print(i, 'trend = 1')
                trend = 1
                nextTrend = 0
                minHighPrice = highPrice
        else:
            minHighPrice = min(highPrice, minHighPrice)
            # print(i, lowma[i], minHighPrice, df['close'][i], df['high'][i-1])
            if lowma[i] > minHighPrice and df['close'][i] > nz(df['high'][i-1], df['high'][i]):
                # print(i, 'trend = 0')
                trend = 0
                nextTrend = 1
                maxLowPrice = lowPrice
        arrTrend[i] = trend

        if trend == 0:
            if not na(arrTrend[i-1]) and arrTrend[i-1] != 0:
                up = down if na(arrDown[i-1]) else arrDown[i-1]
            else:
                up = maxLowPrice if na(arrUp[i-1]) else max(maxLowPrice, arrUp[i-1])
            direction = 'long'
            atrHigh = up + dev
            atrLow = up - dev
            arrUp[i] = up
        else:
            if not na(arrTrend[i-1]) and arrTrend[i-1] != 1:
                down = up if na(arrUp[i-1]) else arrUp[i-1]
            else:
                down = minHighPrice if na(arrDown[i-1]) else min(minHighPrice, arrDown[i-1])
            direction = 'short'
            atrHigh = down + dev
            atrLow = down - dev
            arrDown[i] = down

        # print(i, arrUp[i], arrDown[i], atrHigh, atrLow)
        if trend == 0:
            out.append([atrHigh, up, atrLow, direction, arrUp[i], arrDown[i]])
        else:
            out.append([atrHigh, down, atrLow, direction, arrUp[i], arrDown[i]])
    return out

def set_indicator(symbol, bars, config=indicator_config):
    df = pd.DataFrame(
        bars, columns=["time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
    )
    df["time"] = pd.to_datetime(df["time"], unit="s").map(
        lambda x: (x+pd.Timedelta(hours=MT_ADJUST))
    )
    # df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")
    df.rename({'tick_volume': 'volume'}, axis=1, inplace=True)

    # เอาข้อมูลใหม่ไปต่อท้าย ข้อมูลที่มีอยู่
    if symbol in all_candles.keys() and len(df) < CANDLE_LIMIT:
        df = pd.concat([all_candles[symbol], df], ignore_index=False)

        # เอาแท่งซ้ำออก เหลืออันใหม่สุด
        df = df[~df.index.duplicated(keep='last')].tail(CANDLE_LIMIT)

    df = df.tail(CANDLE_LIMIT)

    if len(df) < CANDLE_SAVE:
        print(f'less candles for {symbol}, skip add_indicator')
        return df
    
    # คำนวนค่าต่างๆใหม่
    df['MACD'] = 0
    df['MACDs'] = 0
    df['MACDh'] = 0
    df["RSI"] = 0

    try:
        atrlen = config['atrlen']
        amplitude = config['amplitude']
        channel_deviation = config['channel_deviation']
        # print(df[['high','close','low']])
        # data = np.array(df[['high','close','low']].values)
        # print(data)
        halfTrend = np.array(halftrend(df, atrlen, amplitude, channel_deviation)).transpose((1, 0))
        # return atrHigh, atrLow, upTmp, downTmp, direction
        # print(halfTrend)
        # df_HalfTrend = pd.DataFrame(halfTrend, columns=['fast', 'mid', 'slow', 'trend'])
        df['atrHigh'] = np.pad(halfTrend[0].astype(float), (df.shape[0] - len(halfTrend[0]), 0), mode='constant', constant_values=np.nan)
        df['atrLow'] = np.pad(halfTrend[2].astype(float), (df.shape[0] - len(halfTrend[2]), 0), mode='constant', constant_values=np.nan)
        df['value'] = np.pad(halfTrend[1].astype(float), (df.shape[0] - len(halfTrend[1]), 0), mode='constant', constant_values=np.nan)
        df['trend'] = np.pad(halfTrend[3], (df.shape[0] - len(halfTrend[4]), 0), mode='constant', constant_values=np.nan)
        df['up'] = np.pad(halfTrend[4].astype(float), (df.shape[0] - len(halfTrend[4]), 0), mode='constant', constant_values=np.nan)
        df['down'] = np.pad(halfTrend[5].astype(float), (df.shape[0] - len(halfTrend[5]), 0), mode='constant', constant_values=np.nan)

        # print(df.tail(10))

        # cal MACD
        ewm_fast     = df['close'].ewm(span=config['MACD_FAST'], adjust=False).mean()
        ewm_slow     = df['close'].ewm(span=config['MACD_SLOW'], adjust=False).mean()
        df['MACD']   = ewm_fast - ewm_slow
        df['MACDs']  = df['MACD'].ewm(span=config['MACD_SIGNAL']).mean()
        df['MACDh']  = df['MACD'] - df['MACDs']

        # cal RSI
        df["RSI"] = ta.rsi(df['close'],config['RSI_PERIOD'])

    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))
        logger.error(ex)

    return df

"""
fetch_ohlcv - อ่านแท่งเทียน
exchange: mt5 connect
symbol: coins symbol
timeframe: candle time frame
limit: จำนวนแท่งที่ต้องการ, ใส่ 0 หากต้องการให้เอาแท่งใหม่ที่ไม่มาครบ
timestamp: ระบุเวลาปัจจุบัน ถ้า limit=0
"""
async def fetch_ohlcv(exchange, symbol, timeframe, limit=CANDLE_LIMIT, timestamp=0, config=indicator_config):
    global all_candles
    if not exchange:
        print("No MT5 Connect")
        return
    try:
        # กำหนดการอ่านแท่งเทียนแบบไม่ระบุจำนวน
        if limit == 0 and symbol in all_candles.keys():
            timeframe_secs = TIMEFRAME_SECONDS[timeframe]
            ts_adjust_secs = TZ_ADJUST*60*60
            last_candle_time = int(pd.Timestamp(all_candles[symbol].index[-1]).timestamp()) - ts_adjust_secs
            # ให้อ่านแท่งสำรองเพิ่มอีก 2 แท่ง
            cal_limit = round(1.5+(timestamp-last_candle_time)/timeframe_secs)
            limit = cal_limit if cal_limit < CANDLE_LIMIT else CANDLE_LIMIT
            logger.debug(f"fetch_ohlcv {symbol} {timestamp} {last_candle_time} {timestamp-last_candle_time} {ts_adjust_secs} {cal_limit} {limit}")
            
        ohlcv_bars  = mt5.copy_rates_from_pos(symbol, TIMEFRAME_MT5[timeframe], 0, limit)
        logger.info(f"{symbol} fetch_ohlcv, limit:{limit}, len:{len(ohlcv_bars)}")
        if len(ohlcv_bars):
            all_candles[symbol] = set_indicator(symbol, ohlcv_bars, config=config)
    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))
        if limit == 0 and symbol in all_candles.keys():
            print('----->', timestamp, last_candle_time, timestamp-last_candle_time, round(1.5+(timestamp-last_candle_time)/timeframe_secs))
        # if '"code":-1130' in str(ex):
        #     watch_list.remove(symbol)
        #     print(f'{symbol} is removed from watch_list')

def get_signal(symbol, idx):
    df = all_candles[symbol]
    is_long = False
    is_short = False
    if df['trend'][idx] == 'long' and df['trend'][idx-1] == 'short':
        is_long = True
    elif df['trend'][idx] == 'short' and df['trend'][idx-1] == 'long':
        is_short = True
    return is_long, is_short

async def chart(symbol, timeframe, config=indicator_config, showMACDRSI=False, fiboData=None):
    filename = f"./plots/order_{str(symbol).lower()}.png"
    try:
        print(f"{symbol} create line_chart")
        df = all_candles[symbol]
        data = df.tail(CANDLE_PLOT)

        showFibo = fiboData != None

        gap = (max(data['high']) - min(data['low'])) * 0.1
        # print(gap)

        long_markers = []
        short_markers = []
        has_long = False
        has_short = False

        for i in range(len(data)):
            long_markers.append(np.nan)
            short_markers.append(np.nan)
            is_long, is_short = get_signal(symbol, CANDLE_PLOT+i)
            if is_long:
                has_long = True
                long_markers[i] = data['value'][i] - gap
            elif is_short:
                has_short = True
                short_markers[i] = data['value'][i] + gap

        added_plots = [
            # mpf.make_addplot(['Trailingsl'],color='green',width=1),
            mpf.make_addplot(data['atrHigh'],color='red',width=.5),
            mpf.make_addplot(data['atrLow'],color='blue',width=.5),
            mpf.make_addplot(data['up'],color='blue',width=2),
            mpf.make_addplot(data['down'],color='red',width=2),
        ]
        if has_long:
            added_plots.append(mpf.make_addplot(long_markers, type='scatter', marker='^', markersize=100, color='green',panel=0))
        if has_short:
            added_plots.append(mpf.make_addplot(short_markers, type='scatter', marker='v', markersize=100, color='red',panel=0))
 
        if showMACDRSI:
            rsi30 = [30 for i in range(0, CANDLE_PLOT)]
            rsi50 = [50 for i in range(0, CANDLE_PLOT)]
            rsi70 = [70 for i in range(0, CANDLE_PLOT)]
            added_plots += [ 
                mpf.make_addplot(data['RSI'],ylim=(10, 90),panel=2,color='blue',width=0.75,
                    ylabel=f"RSI ({config['RSI_PERIOD']})", y_on_right=False),
                mpf.make_addplot(rsi30,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),
                mpf.make_addplot(rsi50,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),
                mpf.make_addplot(rsi70,ylim=(10, 90),panel=2,color='red',linestyle='-.',width=0.5),
            ]
            colors = ['green' if value >= 0 else 'red' for value in data['MACDh']]
            added_plots += [
                mpf.make_addplot(data['MACDh'],type='bar',width=0.5,panel=3,color=colors,
                    ylabel=f"MACD ({config['MACD_FAST']})", y_on_right=True),
                mpf.make_addplot(data['MACD'],panel=3,color='orange',width=0.75),
                mpf.make_addplot(data['MACDs'],panel=3,color='blue',width=0.75),
            ]

        kwargs = dict(
            figscale=1.2,
            figratio=(8, 7),
            panel_ratios=(8,2,2,2) if showMACDRSI else (4,1),
            addplot=added_plots,
            scale_padding={'left': 0.5, 'top': 0.6, 'right': 1.0, 'bottom': 0.5},
            )
        
        fibo_title = ''

        if showFibo:
            logger.debug(f"{symbol} {fiboData}")

            tpsl_colors = []
            tpsl_data = []
            if 'tp' in fiboData.keys() and fiboData['tp'] > 0:
                tpsl_colors.append('g')
                tpsl_data.append(fiboData['tp'])
            if 'sl' in fiboData.keys() and fiboData['sl'] > 0:
                tpsl_colors.append('r')
                tpsl_data.append(fiboData['sl'])
            if 'price' in fiboData.keys():
                tpsl_colors.append('b')
                tpsl_data.append(fiboData['price'])
            if len(tpsl_data) > 0:
                tpsl_lines = dict(
                    hlines=tpsl_data,
                    colors=tpsl_colors,
                    alpha=0.5,
                    linestyle='-.',
                    linewidths=1,
                    )
                kwargs['hlines']=tpsl_lines

            if 'min_max' in fiboData.keys():
                minmax_lines = dict(
                    alines=fiboData['min_max'],
                    colors='black',
                    linestyle='--',
                    linewidths=0.1,
                    )
                kwargs['alines']=minmax_lines

            if 'fibo_type' in fiboData.keys():
                fibo_title = ' fibo-'+fiboData['fibo_type'][0:2]

        myrcparams = {'axes.labelsize':10,'xtick.labelsize':8,'ytick.labelsize':8}
        mystyle = mpf.make_mpf_style(base_mpf_style='charles',rc=myrcparams)

        title = f'{symbol} :: HalfTrend :: {fiboData["position"]} :: ({timeframe} @ {data.index[-1]})'
        print(title)

        fig, axlist = mpf.plot(
            data,
            volume=True,volume_panel=1,
            **kwargs,
            type="candle",
            xrotation=0,
            ylabel='Price',
            style=mystyle,
            returnfig=True,
            # axtitle=title,
        )
        ax1,*_ = axlist

        title = ax1.set_title(f'{title}{fibo_title})')
        title.set_fontsize(14)

        if showFibo:
            if 'difference' in fiboData.keys():
                difference = fiboData['difference']
            else:
                difference = 0.0
            if 'fibo_levels' in fiboData.keys():
                fibo_colors = ['red','brown','orange','gold','green','blue','gray','purple','purple','purple']
                fibo_levels = fiboData['fibo_levels']
                for idx, fibo_val in enumerate(fiboData['fibo_values']):
                    if idx < len(fibo_levels)-1:
                        ax1.fill_between([0, CANDLE_PLOT] ,fibo_levels[idx],fibo_levels[idx+1],color=fibo_colors[idx],alpha=0.1)
                    ax1.text(0,fibo_levels[idx] + difference * 0.02,f'{fibo_val}({fibo_levels[idx]:.2f})',fontsize=8,color=fibo_colors[idx],horizontalalignment='left')

            none_tpsl_txt = []
            if 'tp' in fiboData.keys() and fiboData['tp'] > 0:
                fibo_tp = fiboData['tp']
                fibo_tp_txt = fiboData['tp_txt']
                ax1.text(CANDLE_PLOT,fibo_tp - difference * 0.06,fibo_tp_txt,fontsize=8,color='g',horizontalalignment='right')
            else:
                none_tpsl_txt.append('No TP')

            if 'sl' in fiboData.keys() and fiboData['sl'] > 0:
                fibo_sl = fiboData['sl']
                fibo_sl_txt = fiboData['sl_txt']
                ax1.text(CANDLE_PLOT,fibo_sl - difference * 0.06,fibo_sl_txt,fontsize=8,color='r',horizontalalignment='right')
            else:
                none_tpsl_txt.append('No SL')
                
            if 'price' in fiboData.keys():
                fibo_price = fiboData['price']
                fibo_price_txt = fiboData['price_txt'] + (' [' + ','.join(none_tpsl_txt) + ']' if len(none_tpsl_txt) > 0 else '')
                ax1.text(CANDLE_PLOT,fibo_price - difference * 0.06,fibo_price_txt,fontsize=8,color='b',horizontalalignment='right')

        fig.savefig(filename)

        plt.close(fig)

        # open(plot_file, 'rb')

    except Exception as ex:
        print(type(ex).__name__, symbol, str(ex))

    return filename