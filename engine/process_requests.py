from collections import defaultdict

import numpy as np
import vectorbtpro as vbt
from backtesting.decorators import std_parameterized
from engine.data.data_manager import fetch_datas
from indicators.indicator_library import indicator_library, get_indicator_key_value, get_indicator_run_results
from models import BtRequest


def get_timeframed_run_results(timeframed_data, rest_indicators):
    timeframed_run_results = defaultdict(dict)
    for timeframe, data in timeframed_data.items():
        for rest_indicator in rest_indicators:
            if rest_indicator.timeframe != timeframe:
                continue

            if rest_indicator.run_kwargs:
                run_results = get_indicator_run_results(rest_indicator.indicator, data,
                                                        run_kwargs=rest_indicator.run_kwargs)
            else:
                run_results = get_indicator_run_results(rest_indicator.indicator, data)

            timeframed_run_results[timeframe][rest_indicator.alias] = run_results

    return timeframed_run_results


def process_bt_request(bt_request: BtRequest):
    timeframed_data = fetch_datas(source=bt_request.source,
                                  symbols=bt_request.symbols,
                                  timeframes=[indicator.timeframe for indicator in bt_request.indicators],
                                  testing_period=bt_request.testing_period)

    #1. Create dict of all kwargs to be used in the sim in vbt params,
    # thats the run_kwargs from each rest_indicator and the custom_ranges from bt_request
    #

    run_kwargs = {}

    for rest_indicator in bt_request.indicators:
        if rest_indicator.run_kwargs:
            for key, value in rest_indicator.run_kwargs.items():
                run_kwargs[f'{rest_indicator.alias}__{key}'] = vbt.Param(value)

    if bt_request.custom_ranges:
        for key, value in bt_request.custom_ranges.items():
            run_kwargs[key] = vbt.Param(value)

    if bt_request.sl_stop:
        run_kwargs['sl_stop'] = vbt.Param(bt_request.sl_stop)

    if bt_request.tp_stop:
        run_kwargs['tp_stop'] = vbt.Param(bt_request.tp_stop)

    if bt_request.tsl_stop:
        run_kwargs['tsl_stop'] = vbt.Param(bt_request.tsl_stop)

    if bt_request.fee:
        run_kwargs['fee'] = vbt.Param(bt_request.fee)

    if bt_request.slippage:
        run_kwargs['slippage'] = vbt.Param(bt_request.slippage)

    r = get_parameterized_pf(timeframed_data, bt_request=bt_request, **run_kwargs)

    print(1)


def set_rest_indicator_live_run_kwargs(bt_request, kwargs):
    for rest_indicator in bt_request.indicators:
        if not rest_indicator.run_kwargs:
            continue

        rest_indicator_live_run_kwargs = {}
        for key in kwargs:
            if key.startswith(rest_indicator.alias):
                rest_indicator_live_run_kwargs[key.split('__')[1]] = kwargs[key]

        rest_indicator.run_kwargs = rest_indicator_live_run_kwargs


def handle_crossed_operator(operator_string):
    split_string = operator_string.split()
    for i, word in enumerate(split_string):
        if word == '|>':
            split_string[i - 1] = split_string[i - 1] + f'.vbt.crossed_above({split_string[i + 1]})'
            split_string[i] = ''
            split_string[i + 1] = ''

        elif word == '<|':
            split_string[i - 1] = split_string[i - 1] + f'.vbt.crossed_below({split_string[i + 1]})'
            split_string[i] = ''
            split_string[i + 1] = ''

    return ' '.join(split_string)

@std_parameterized
def get_parameterized_pf(timeframed_data, bt_request, **kwargs):

    set_rest_indicator_live_run_kwargs(bt_request, kwargs)
    timeframed_run_results = get_timeframed_run_results(timeframed_data, bt_request.indicators)

    for key, value in kwargs.items():
        bt_request.entries = bt_request.entries.replace(key, str(value))
        bt_request.exits = bt_request.exits.replace(key, str(value))

    indicator_run_results = {}
    for timeframe, indicator_results in timeframed_run_results.items():
        for indicator_alias, run_results in indicator_results.items():
            for run_value, run_result in run_results.items():
                indicator_run_results[f'{indicator_alias}.{run_value}'] = run_result

    for word in bt_request.entries.split():
        if word in indicator_run_results:
            bt_request.entries = bt_request.entries.replace(word, f'indicator_run_results["{word}"]')

    for word in bt_request.exits.split():
        if word in indicator_run_results:
            bt_request.exits = bt_request.exits.replace(word, f'indicator_run_results["{word}"]')

    bt_request.entries = handle_crossed_operator(bt_request.entries)
    bt_request.exits = handle_crossed_operator(bt_request.exits)

    entries = eval(bt_request.entries)
    exits = eval(bt_request.exits)


    if BtRequest.test_var == 'sharpe_ratio':
        return 1
    # todo - get fee, slippage and stops from kwargs else default
    # todo - delete stops that are 0 or negative from new pf run_kwargs - still to be built

    return np.random.randint(4)
    #
