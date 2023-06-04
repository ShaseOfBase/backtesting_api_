import vectorbtpro as vbt


indicator_library = {
    'adx': {'indicator': vbt.IF.get_indicator('talib:ADX'),
            'result_param': 'real'},
    'bbands.lower': {'indicator': vbt.IF.get_indicator('vbt:BBANDS'),
                        'result_param': 'lower'},
    'bbands.middle': {'indicator': vbt.IF.get_indicator('vbt:BBANDS'),
                        'result_param': 'middle'},
    'bbands.upper': {'indicator': vbt.IF.get_indicator('vbt:BBANDS'),
                        'result_param': 'upper'},
    'bbands.bandwidth': {'indicator': vbt.IF.get_indicator('vbt:BBANDS'),
                        'result_param': 'bandwidth'},
    'mfi': {'indicator': vbt.IF.get_indicator('talib:MFI'),
            'result_param': 'real'},
    'rsi': {'indicator': vbt.IF.get_indicator('talib:RSI'),
            'result_param': 'real'},
    'sma': {'indicator': vbt.IF.get_indicator('talib:SMA'),
            'result_param': 'real'},
    'mom': {'indicator': vbt.IF.get_indicator('talib:MOM'),
            'result_param': 'real'},
    'macd.hist': {'indicator': vbt.IF.get_indicator('vbt:MACD'),
                    'result_param': 'hist'},
    'macd.macd': {'indicator': vbt.IF.get_indicator('vbt:MACD'),
                    'result_param': 'macd'},
    'macd.signal': {'indicator': vbt.IF.get_indicator('vbt:MACD'),
                    'result_param': 'signal'},
    'ema': {'indicator': vbt.IF.get_indicator('talib:EMA'),
            'result_param': 'real'},
    'atr': {'indicator': vbt.IF.get_indicator('talib:ATR'),
            'result_param': 'real'},
    }


def get_indicator_data():
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