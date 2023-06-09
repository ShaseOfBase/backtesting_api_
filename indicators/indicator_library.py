import vectorbtpro as vbt


indicator_library = {
    'adx': {'indicator': vbt.IF.get_indicator('talib:ADX'),
            'default_param': 'real',
            'avlbl_params': ['real'],
            'data_kwargs': ['high', 'low', 'close'],  # todo continue...
            'param_kwargs': {'timeperiod': 14}},
    'bbands': {'indicator': vbt.IF.get_indicator('vbt:BBANDS'),
                        'default_param': 'lower',
                     'data_kwargs': ['close'],
                     'param_kwargs': {'alpha': 2, 'window': 20}},
    'mfi': {'indicator': vbt.IF.get_indicator('talib:MFI'),
            'default_param': 'real'},
    'rsi': {'indicator': vbt.IF.get_indicator('talib:RSI'),
            'default_param': 'real'},
    'sma': {'indicator': vbt.IF.get_indicator('talib:SMA'),
            'default_param': 'real'},
    'mom': {'indicator': vbt.IF.get_indicator('talib:MOM'),
            'default_param': 'real'},
    'macd.hist': {'indicator': vbt.IF.get_indicator('vbt:MACD'),
                    'default_param': 'hist'},
    'macd.macd': {'indicator': vbt.IF.get_indicator('vbt:MACD'),
                    'default_param': 'macd',},
    'macd.signal': {'indicator': vbt.IF.get_indicator('vbt:MACD'),
                    'default_param': 'signal'},
    'ema': {'indicator': vbt.IF.get_indicator('talib:EMA'),
            'default_param': 'real'},
    'atr': {'indicator': vbt.IF.get_indicator('talib:ATR'),
            'default_param': 'real'},
    'ma': {'indicator': vbt.IF.get_indicator('vbt:MA'),
            'default_param': 'ma'},
    }


def get_indicator_kwargs(indicator: str, data):
    if indicator == ''
    ...


def get_indicator_from_str(indicator_str: str):
    indicator_str = indicator_str.lower()
    indicator_library = {
        'adx' : ..., # todo <- return vbt indicators
        'bbands.lower' : ...,
        'bbands.middle': ...,
        'bbands.upper': ...,
        'bbands.bandwidth': ...,
    }