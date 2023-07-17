import numpy as np
import vectorbtpro as vbt
from engine.data.data_manager import convert_std_timeframe_to_pandas_timeframe, reshape_slow_timeframe_data_to_fast
from indicators.indicator_run_caching import get_cached_indicator_run_result, cache_indicator_run_result


def get_chart_options_value(indicator, data, run_value, shaped_run_result, option: str):
    if option not in ['style', 'y_val', 'add_to_orders']:
        raise ValueError(f'Invalid option: {option}')

    if option in ['style', 'add_to_orders']:
        return indicator_library[indicator]['chart_options'][option][run_value]

    if option == 'y_val':
        if indicator_library[indicator]['chart_options'][option][run_value] == 'self':
            return shaped_run_result
        elif indicator_library[indicator]['chart_options'][option][run_value] in ['close', 'open', 'high',
                                                                                  'low', 'volume']:
            return eval(f"data.{indicator_library[indicator]['chart_options'][option][run_value]}")
        else:
            raise ValueError(f'Invalid value for y_val_types: '
                             f'{indicator_library[indicator]["chart_options"][option][run_value]}')

    else:
        raise ValueError(f'Invalid option: {option}')



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
                'chart_options': {
                    'style': {'lower': 'pure', 'middle': 'pure', 'upper': 'pure', 'bandwidth': 'raw'},
                    'y_val': {'lower': 'close', 'middle': 'close', 'upper': 'close', 'bandwidth': 'self'},
                    'add_to_orders': {'lower': True, 'middle': True, 'upper': True, 'bandwidth': False},

                },
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
             'run_kwargs': {'fast_window': 12, 'slow_window': 26, 'signal_window': 9},
             'chart_options': {
                 'style': {'macd': 'pure', 'signal': 'pure', 'hist': 'pure'},
                 'y_val': {'macd': 'self', 'signal': 'self', 'hist': 'self'},
                 'add_to_orders': {'macd': False, 'signal': False, 'hist': False},
             },
             },
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
           'run_kwargs': {'window': 30},
           'chart_options': {
               'style': {'ma': 'pure'},
               'y_val': {'ma': 'close'},
               'add_to_orders': {'ma': True},
           },
           },
}


def get_indicator_key_value(indicator: str, key_value: str):
    '''Returns the value of the key_value for the indicator,
    key_value options are 'vbt_indicator', 'default_value', 'avlbl_values', 'data_run_kwargs', 'run_kwargs'''
    if key_value not in indicator_library[indicator]:
        raise ValueError(f'key_value must be one of {list(indicator_library[indicator].keys())}')
    return indicator_library[indicator].get(key_value)


def get_indicator_run_results(fastest_timeframe_data, fastest_timeframe,
                              timeframe_data, rest_indicator, run_kwargs: dict = None):
    '''Returns the results of the run_values for the indicator'''
    vbt_indicator = get_indicator_key_value(rest_indicator.indicator, 'vbt_indicator')

    if not run_kwargs:
        run_kwargs = get_indicator_key_value(rest_indicator.indicator, 'run_kwargs')

    data_run_params = get_indicator_key_value(rest_indicator.indicator, 'data_run_params')

    data_run_kwargs = {}
    for param in data_run_params:
        data_run_kwargs[param] = eval(f'timeframe_data.{param}')

    indicator_run_object = get_cached_indicator_run_result(data_instance=timeframe_data,
                                                           indicator=rest_indicator.indicator,
                                                           run_kwargs=run_kwargs)
    if not indicator_run_object:
        indicator_run_object = vbt_indicator.run(**data_run_kwargs, **run_kwargs)

        cache_indicator_run_result(run_result=indicator_run_object,
                                   data_instance=timeframe_data,
                                   indicator=rest_indicator.indicator,
                                   run_kwargs=run_kwargs)

    avlbl_values = get_indicator_key_value(rest_indicator.indicator, 'avlbl_values')

    run_results = {}
    for run_value in avlbl_values:
        pandas_timeframe = convert_std_timeframe_to_pandas_timeframe(fastest_timeframe)
        shaped_run_result = eval(f'indicator_run_object.{run_value}').resample(pandas_timeframe).asfreq().ffill()
        shaped_run_result = reshape_slow_timeframe_data_to_fast(slow_timeframe_data=shaped_run_result,
                                                                fastest_timeframe_index=fastest_timeframe_data.index)

        if rest_indicator.normalize:
            shaped_run_result = shaped_run_result / fastest_timeframe_data.close

        shaped_run_result = np.array(shaped_run_result)
        shaped_run_result = shaped_run_result.reshape(shaped_run_result.shape[0])

        run_results[run_value] = {'shaped_run_result': shaped_run_result,
                                  'indicator_run_object': indicator_run_object,
                                  'data': fastest_timeframe_data}

    return run_results



