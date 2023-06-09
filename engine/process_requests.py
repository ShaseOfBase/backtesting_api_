from collections import defaultdict

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
                run_results = get_indicator_run_results(rest_indicator.indicator, data, run_kwargs=rest_indicator.run_kwargs)
            else:
                run_results = get_indicator_run_results(rest_indicator.indicator, data)

            timeframed_run_results[timeframe][rest_indicator.alias] = run_results

    return timeframed_run_results


def process_bt_request(bt_request: BtRequest):
    timeframed_data = fetch_datas(source=bt_request.source,
                                  symbols=bt_request.symbols,
                                  timeframes=[indicator.timeframe for indicator in bt_request.indicators],
                                  testing_period=bt_request.testing_period)

    timeframed_run_results = get_timeframed_run_results(timeframed_data, bt_request.indicators)

    print(1)
