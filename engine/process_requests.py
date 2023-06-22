from collections import defaultdict

import numpy as np
import vectorbtpro as vbt
from backtesting.decorators import std_parameterized
from engine.data.data_manager import fetch_datas, get_fastest_timeframe_data
from engine.optuna_processing import get_suggested_value
from indicators.indicator_library import indicator_library, get_indicator_key_value, get_indicator_run_results
from indicators.indicator_run_caching import clear_indicator_run_cache
from models import BtRequest
import optuna


def get_live_run_indicators(bt_request, kwargs):
    live_run_indicators = bt_request.indicators.copy()
    for rest_indicator in live_run_indicators:
        if not rest_indicator.run_kwargs:
            continue

        rest_indicator_live_run_kwargs = {}
        for key in kwargs:
            if key.startswith(rest_indicator.alias):
                rest_indicator_live_run_kwargs[key.split('__')[1]] = kwargs[key]

        rest_indicator.run_kwargs = rest_indicator_live_run_kwargs

    return live_run_indicators


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


def format_action_string(action_string: str, indicator_aliases: list, indicator_run_results: dict):
    '''Converts user-friendly action string to one that can be evaluated by eval()'''
    fixed_action_string_words = []

    for word in action_string.split():
        left_brack = False
        right_brack = False
        if '(' in word:
            left_brack = True
        if ')' in word:
            right_brack = True

        word = word.replace('(', '').replace(')', '')

        if word in indicator_run_results:
            fixed_word = f'indicator_run_results["{word}"]'

        elif word in indicator_aliases and '.' not in word:  # then this must intend to reference the default value
            for key in indicator_run_results:
                if word in key:
                    fixed_word = f'indicator_run_results["{key}"]'
                    break
        else:
            fixed_word = word

        if left_brack:
            fixed_word = '(' + fixed_word
        if right_brack:
            fixed_word = fixed_word + ')'

        fixed_action_string_words.append(fixed_word)

    fixed_action_string = ' '.join(fixed_action_string_words)
    return fixed_action_string


def get_timeframed_run_results(timeframed_data, rest_indicators):
    timeframed_run_results = defaultdict(dict)
    for timeframe, timeframe_data in timeframed_data.items():
        for rest_indicator in rest_indicators:
            if rest_indicator.timeframe != timeframe:
                continue

            if rest_indicator.run_kwargs:
                run_results = get_indicator_run_results(timeframe_data, rest_indicator.indicator,
                                                        run_kwargs=rest_indicator.run_kwargs)
            else:
                run_results = get_indicator_run_results(timeframe_data, rest_indicator.indicator)

            timeframed_run_results[timeframe][rest_indicator.alias] = run_results

    return timeframed_run_results


def process_bt_request(bt_request: BtRequest):
    timeframed_data = fetch_datas(source=bt_request.source,
                                  symbol=bt_request.symbol,
                                  timeframes=[indicator.timeframe for indicator in bt_request.indicators],
                                  testing_period=bt_request.testing_period)

    renamed_indicators = {}

    for rest_indicator in bt_request.indicators:
        if not rest_indicator.run_kwargs:
            continue
        for key, value in rest_indicator.run_kwargs.items():
            renamed_indicators[f'{rest_indicator.alias}__{key}'] = value

    kwargs_to_add = [renamed_indicators]
    kwargs_to_add.append(bt_request.custom_ranges)

    use_optuna = True
    if use_optuna:
        study_name = 'cool_study12'
        # storage = "sqlite:///{}.db".format(study_name)
        study = optuna.create_study(study_name=study_name, direction='maximize')

        def objective(trial):
            run_kwargs = {}

            for kwargs_set in kwargs_to_add:
                for key, value in kwargs_set.items():
                    if not isinstance(value, list):
                        run_kwargs[key] = value
                        continue

                    suggested_value = get_suggested_value(trial, suggestion_key=key, value=value)

                    run_kwargs[key] = suggested_value

            if bt_request.sl_stop:
                if isinstance(bt_request.sl_stop, list):
                    run_kwargs['sl_stop'] = get_suggested_value(trial, suggestion_key='sl_stop',
                                                                value=bt_request.sl_stop)
                else:
                    run_kwargs['sl_stop'] = bt_request.sl_stop

            if bt_request.tp_stop:
                if isinstance(bt_request.tp_stop, list):
                    run_kwargs['tp_stop'] = get_suggested_value(trial, suggestion_key='tp_stop',
                                                                value=bt_request.tp_stop)
                else:
                    run_kwargs['tp_stop'] = bt_request.tp_stop

            if bt_request.tsl_stop:
                if isinstance(bt_request.tsl_stop, list):
                    run_kwargs['tsl_stop'] = get_suggested_value(trial, suggestion_key='tsl_stop',
                                                                 value=bt_request.tsl_stop)
                else:
                    run_kwargs['tsl_stop'] = bt_request.tsl_stop

            if bt_request.fee:
                run_kwargs['fee'] = bt_request.fee

            if bt_request.slippage:
                run_kwargs['slippage'] = bt_request.slippage

            pf = get_pf(timeframed_data, bt_request=bt_request, **run_kwargs)

            if bt_request.objective_value == 'sharpe_ratio':
                return pf.sharpe_ratio[0]
            elif bt_request.objective_value == 'total_return':
                return pf.total_return[0]
            else:
                raise ValueError(f'Invalid objective value: {bt_request.objective_value}')

        study.optimize(objective, n_trials=bt_request.n_trials)
        clear_indicator_run_cache()
        print(1)

    '''else:
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

        r = get_pf(timeframed_data, bt_request=bt_request, **run_kwargs)  # todo <- this will need to be paramaterized
    '''


def get_pf(timeframed_data, bt_request, **kwargs):
    live_run_indicators = get_live_run_indicators(bt_request, kwargs)
    live_run_aliases = [indicator.alias for indicator in live_run_indicators]
    timeframed_run_results = get_timeframed_run_results(timeframed_data, live_run_indicators)  # todo <- resample slower timeframes to fastest timeframe

    entry_string = bt_request.entries
    exit_string = bt_request.exits
    for key, value in kwargs.items():
        entry_string = entry_string.replace(key, str(value))
        exit_string = exit_string.replace(key, str(value))

    indicator_run_results = {}
    for timeframe, indicator_results in timeframed_run_results.items():
        for indicator_alias, run_results in indicator_results.items():
            for run_value, run_result in run_results.items():
                indicator_run_results[f'{indicator_alias}.{run_value}'] = run_result

    entry_string = format_action_string(entry_string, indicator_aliases=live_run_aliases,
                                        indicator_run_results=indicator_run_results)

    exit_string = format_action_string(exit_string, indicator_aliases=live_run_aliases,
                                       indicator_run_results=indicator_run_results)

    entry_string = handle_crossed_operator(entry_string)
    exit_string = handle_crossed_operator(exit_string)

    entries = np.where(eval(entry_string), True, False)
    exits = np.where(eval(exit_string), True, False)

    fastest_timeframed_data = get_fastest_timeframe_data(timeframed_data)

    return vbt.Portfolio.from_signals(close=fastest_timeframed_data, entries=entries, exits=exits)

    # todo - get fee, slippage and stops from kwargs else default
    # todo - delete stops that are 0 or negative from new pf run_kwargs - still to be built

    #
