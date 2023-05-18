import configparser

def is_exist(group, name):
    return group in config.keys() and name in config[group].keys()

def get_list(group, name, default=[]):
    value = default
    try:
        if is_exist(group, name):
            value = [x.strip() for x in config[group][name].split(',')]
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_list_float(group, name, default=[]):
    value = default
    try:
        if is_exist(group, name):
            value = [float(x.strip()) for x in config[group][name].split(',')]
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value
    
def get_str(group, name, default=''):
    value = default
    try:
        if is_exist(group, name):
            value = config[group][name]
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_int(group, name, default=0):
    value = default
    try:
        if is_exist(group, name):
            value = int(config[group][name])
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value

def get_float(group, name, default=0.0):
    value = default
    try:
        if is_exist(group, name):
            value = float(config[group][name])
        else:
            print(f'config {group}.{name} not found, set default to {default}')
    except Exception as ex:
        print(type(ex).__name__, str(ex))
        print(f'config {group}.{name} not found, set default to {default}')
    return value

config = configparser.ConfigParser(interpolation=None)
config.optionxform = str
config_file = open("config.ini", mode='r', encoding='utf-8-sig')
config.readfp(config_file)

#------------------------------------------------------------
# MT5
#------------------------------------------------------------
LOGIN = get_str('mt5','login')
PASSWORD = get_str('mt5','password')
SERVER = get_str('mt5','server')

#------------------------------------------------------------
# line
#------------------------------------------------------------
LINE_NOTIFY_TOKEN = get_str('line','notify_token')

#------------------------------------------------------------
# app_config
#------------------------------------------------------------
TIME_SHIFT = get_int('app_config', 'TIME_SHIFT', 5)
CANDLE_LIMIT = get_int('app_config', 'CANDLE_LIMIT', 1000)
CANDLE_PLOT = get_int('app_config', 'CANDLE_PLOT', 100)
LOG_LEVEL = get_int('app_config', 'LOG_LEVEL', 20)
UB_TIMER_MODE = get_int('app_config', 'UB_TIMER_MODE', 4)
if UB_TIMER_MODE < 0 or UB_TIMER_MODE > 5:
    UB_TIMER_MODE = 4
MM_TIMER_MIN = get_float('app_config', 'MM_TIMER_MIN', 0.0)
SWING_TF = get_int('app_config', 'SWING_TF', 5)
SWING_TEST = get_int('app_config', 'SWING_TEST', 2)
TP_FIBO = get_int('app_config', 'TP_FIBO', 2)
CB_AUTO_MODE = get_int('app_config', 'CB_AUTO_MODE', 1)
START_TRADE_TF = get_str('app_config', 'START_TRADE_TF', '4h')

#------------------------------------------------------------
# setting
#------------------------------------------------------------
timeframe = get_str('setting', 'timeframe', '5m')
signal_index = get_int('setting', 'signal_index', -2)
magic_number = get_int('setting', 'magic_number', '999111')

# symbol = get_str('setting', 'symbol', 'XAUUSD')
symbols = get_list('setting', 'symbols', ['XAUUSD'])
lot = get_float('setting', 'lot', 0.01)
deviation = get_int('setting', 'deviation', 20)

atrlen = get_int('setting', 'atrlen', 100)
amplitude = get_int('setting', 'amplitude', 2)
channel_deviation = get_int('setting', 'channel_deviation', 2)

is_martingale = get_str('setting', 'martingale_mode', 'off') == 'on'
martingale_factor = get_float('setting', 'martingale_factor', 2.0)
martingale_max = get_int('setting', 'martingale_max', 8)

is_auto_tpsl = get_str('setting', 'auto_tpsl', 'on') == 'on'
sl = get_int('setting', 'sl', 500)
tp = get_int('setting', 'tp', 1500)