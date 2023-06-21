import vectorbtpro as vbt

from indicators.indicator_run_caching import get_cached_indicator_run_result, cache_indicator_run_result

indicator_library = {
    'adx': {'vbt_indicator': vbt.IF.get_indicator('talib:ADX'),
            'default_value': 'real',
            'avlbl_values': ['real'],
            'data_run_params': ['high', 'low', 'close'],
            'run_kwargs': {'timeperiod': 14}},
    'bbands': {'vbt_indicator': vbt.IF.get_indicator('vbt:BBANDS'),
               'default_value': 'bandwidth',
               'avlbl_values': ['lower', 'middle', 'upper', 'bandwidth'],
               'data_run_params': ['close'],
               'run_kwargs': {'alpha': 2, 'window': 20}},
    'mfi': {'vbt_indicator': vbt.IF.get_indicator('talib:MFI'),
            'default_value': 'real',
            'avlbl_values': ['real'],
            'data_run_params': ['high', 'low', 'close', 'volume'],
            'run_kwargs': {'timeperiod': 14}},
    'rsi': {'vbt_indicator': vbt.IF.get_indicator('talib:RSI'),
            'default_value': 'real',
            'avlbl_values': ['real'],
            'data_run_params': ['close'],
            'run_kwargs': {'timeperiod': 14}},
    'mom': {'vbt_indicator': vbt.IF.get_indicator('talib:MOM'),
            'default_value': 'real',
            'avlbl_values': ['real'],
            'data_run_params': ['close'],
            'run_kwargs': {'timeperiod': 10}},
    'macd': {'vbt_indicator': vbt.IF.get_indicator('vbt:MACD'),
             'default_value': 'hist',
             'avlbl_values': ['macd', 'signal', 'hist'],
             'data_run_params': ['close'],
             'run_kwargs': {'fast_window': 12, 'slow_window': 26, 'signal_window': 9}},
    'ema': {'vbt_indicator': vbt.IF.get_indicator('talib:EMA'),
            'default_value': 'real',
            'avlbl_values': ['real'],
            'data_run_params': ['close'],
            'run_kwargs': {'timeperiod': 30}},
    'atr': {'vbt_indicator': vbt.IF.get_indicator('talib:ATR'),
            'default_value': 'real',
            'avlbl_values': ['real'],
            'data_run_params': ['high', 'low', 'close'],
            'run_kwargs': {'timeperiod': 14}},
    'ma': {'vbt_indicator': vbt.IF.get_indicator('vbt:MA'),
           'default_value': 'ma',
           'avlbl_values': ['ma'],
           'data_run_params': ['close'],
           'run_kwargs': {'window': 30}},
}


def get_indicator_key_value(indicator: str, key_value: str):
    '''Returns the value of the key_value for the indicator,
    key_value options are 'vbt_indicator', 'default_value', 'avlbl_values', 'data_run_kwargs', 'run_kwargs'''
    if key_value not in indicator_library[indicator]:
        raise ValueError(f'key_value must be one of {list(indicator_library[indicator].keys())}')
    return indicator_library[indicator].get(key_value)


def get_indicator_run_results(timeframe_data, indicator: str, run_kwargs: dict = None):
    '''Returns the results of the run_values for the indicator'''
    vbt_indicator = get_indicator_key_value(indicator, 'vbt_indicator')

    if not run_kwargs:
        run_kwargs = get_indicator_key_value(indicator, 'run_kwargs')

    data_run_params = get_indicator_key_value(indicator, 'data_run_params')

    data_run_kwargs = {}
    for param in data_run_params:
        data_run_kwargs[param] = eval(f'timeframe_data.{param}')

    indicator_run_result = get_cached_indicator_run_result(data_instance=timeframe_data,
                                                           indicator=indicator,
                                                           run_kwargs=run_kwargs)
    if not indicator_run_result:
        indicator_run_result = vbt_indicator.run(**data_run_kwargs, **run_kwargs)
        cache_indicator_run_result(run_result=indicator_run_result,
                                   data_instance=timeframe_data,
                                   indicator=indicator,
                                   run_kwargs=run_kwargs)

    avlbl_values = get_indicator_key_value(indicator, 'avlbl_values')

    run_results = {}
    for run_value in avlbl_values:
        run_results[run_value] = eval(f'indicator_run_result.{run_value}')

    return run_results



