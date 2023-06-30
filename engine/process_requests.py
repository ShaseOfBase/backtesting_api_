from math import isnan
from collections import defaultdict
import pandas as pd
import numpy as np
import vectorbtpro as vbt
from backtesting.decorators import std_parameterized
from engine.data.data_manager import fetch_datas, get_fastest_timeframe_data, reshape_slow_timeframe_data_to_fast
from engine.optuna_processing import get_suggested_value
from indicators.indicator_library import indicator_library, get_indicator_key_value, get_indicator_run_results
from indicators.indicator_run_caching import clear_indicator_run_cache
from models import BtRequest, StratRun
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
    operator_string = operator_string.replace('(', '( ').replace(')', ' )')
    split_string = operator_string.split()
    for i, word in enumerate(split_string):
        if word == '|>':
            split_string[i - 1] = 'pd.Series(' + split_string[i - 1] + f').vbt.crossed_above({split_string[i + 1]})'
            split_string[i] = ''
            split_string[i + 1] = ''

        elif word == '<|':
            split_string[i - 1] = 'pd.Series(' + split_string[i - 1] + f').vbt.crossed_below({split_string[i + 1]})'
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
    fastest_timeframe_data, fastest_timeframe = get_fastest_timeframe_data(timeframed_data)

    for timeframe, timeframe_data in timeframed_data.items():
        for rest_indicator in rest_indicators:
            if rest_indicator.timeframe != timeframe:
                continue

            run_results = get_indicator_run_results(fastest_timeframe_data=fastest_timeframe_data,
                                                    fastest_timeframe=fastest_timeframe,
                                                    timeframe_data=timeframe_data,
                                                    rest_indicator=rest_indicator,
                                                    run_kwargs=rest_indicator.run_kwargs)

            timeframed_run_results[timeframe][rest_indicator.alias] = run_results

    return timeframed_run_results


def run_study(bt_request: BtRequest):
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

                    suggested_value = round(get_suggested_value(trial, suggestion_key=key, value=value), 5)

                    run_kwargs[key] = suggested_value

            if bt_request.sl_stop:
                if isinstance(bt_request.sl_stop, list):
                    run_kwargs['sl_stop'] = round(get_suggested_value(trial, suggestion_key='sl_stop',
                                                                      value=bt_request.sl_stop), 5)
                else:
                    run_kwargs['sl_stop'] = bt_request.sl_stop

            if bt_request.tp_stop:
                if isinstance(bt_request.tp_stop, list):
                    run_kwargs['tp_stop'] = round(get_suggested_value(trial, suggestion_key='tp_stop',
                                                                      value=bt_request.tp_stop), 5)
                else:
                    run_kwargs['tp_stop'] = bt_request.tp_stop

            if bt_request.tsl_stop:
                if isinstance(bt_request.tsl_stop, list):
                    run_kwargs['tsl_stop'] = round(get_suggested_value(trial, suggestion_key='tsl_stop',
                                                                       value=bt_request.tsl_stop), 5)
                else:
                    run_kwargs['tsl_stop'] = bt_request.tsl_stop

            if bt_request.fee:
                run_kwargs['fee'] = bt_request.fee

            if bt_request.slippage:
                run_kwargs['slippage'] = bt_request.slippage

            pf = get_pf(timeframed_data, bt_request=bt_request, **run_kwargs)
            trial.set_user_attr('pf', pf)

            if isnan(pf.sharpe_ratio):
                return -100000

            if bt_request.objective_value == 'sharpe_ratio':
                return pf.sharpe_ratio.values[0]
            elif bt_request.objective_value == 'total_return':
                return pf.total_return.values[0]
            else:
                raise ValueError(f'Invalid objective value: {bt_request.objective_value}')

        study.optimize(objective, n_trials=bt_request.n_trials)
        clear_indicator_run_cache()

        return study

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


def get_indicator_from_alias(alias: str, rest_indicators):
    for rest_indicator in rest_indicators:
        if rest_indicator.alias == alias:
            return rest_indicator

    raise ValueError(f'Invalid indicator alias: {alias}')


def get_strat_run(indicator_alias, shaped_run_result: np.array , indicator_run_object, data, bt_request_indicators):
    alias_indicator_map = {rest_indicator.alias: rest_indicator.indicator for rest_indicator in bt_request_indicators}

    add_to_orders = ... # todo <- determine from indicator library
    style = ... # todo <- determine from indicator library
    y_val = ... # todo <- determine from indicator library with data passed to function...

    strat_run = StratRun(style='pure', run_object=indicator_run_object, y_val=y_val, add_to_orders= False)

    return ...


def get_pf(timeframed_data, bt_request, **kwargs):
    live_run_indicators = get_live_run_indicators(bt_request, kwargs)
    live_run_aliases = [indicator.alias for indicator in live_run_indicators]
    timeframed_run_results = get_timeframed_run_results(timeframed_data, live_run_indicators)

    entry_string = bt_request.entries
    exit_string = bt_request.exits
    for key, value in kwargs.items():
        entry_string = entry_string.replace(key, str(value))
        exit_string = exit_string.replace(key, str(value))

    indicator_run_results = {}
    indicator_run_objects = {}
    for timeframe, indicator_results in timeframed_run_results.items():
        for indicator_alias, run_results in indicator_results.items():
            for run_value, run_result in run_results.items():
                key_val = f'{indicator_alias}.{run_value}'
                indicator_run_results[key_val] = run_result['shaped_run_result']
                indicator_run_objects[key_val] = get_strat_run(indicator_alias=indicator_alias,
                                                               indicator_run_object=run_result['indicator_run_object'],
                                                               y_val=run_result['y_val'],
                                                               bt_request_indicators=bt_request.indicators)

    entry_string = format_action_string(entry_string, indicator_aliases=live_run_aliases,
                                        indicator_run_results=indicator_run_results)

    exit_string = format_action_string(exit_string, indicator_aliases=live_run_aliases,
                                       indicator_run_results=indicator_run_results)

    entry_string = handle_crossed_operator(entry_string)
    exit_string = handle_crossed_operator(exit_string)

    entries = np.where(eval(entry_string), True, False)
    exits = np.where(eval(exit_string), True, False)

    fastest_timeframed_data, fastest_timeframe = get_fastest_timeframe_data(timeframed_data)

    pf = vbt.Portfolio.from_signals(fastest_timeframed_data, entries=entries, exits=exits,
                                    freq=fastest_timeframe)

    return pf

    # todo - get fee, slippage and stops from kwargs else default
    # todo - delete stops that are 0 or negative from new pf run_kwargs - still to be built
