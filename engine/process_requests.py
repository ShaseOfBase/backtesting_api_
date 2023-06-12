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
                run_kwargs[f'{rest_indicator.alias}_{key}'] = vbt.Param(value)

    if bt_request.custom_ranges:
        for key, value in bt_request.custom_ranges.items():
            run_kwargs[key] = vbt.Param(value)

    r = get_parameterized_pf(timeframed_data, **run_kwargs)

    print(1)


@std_parameterized
def get_parameterized_pf(timeframed_data, **kwargs):
    for key, value in kwargs.items():
        print(key, value)
    print(1)

    return np.random.randint(4)
    #timeframed_run_results = get_timeframed_run_results(timeframed_data, bt_request.indicators)
