from datetime import datetime
from math import isnan
from collections import defaultdict
from pathlib import Path

import pandas as pd
import numpy as np
import vectorbtpro as vbt
from sklearn.model_selection import KFold

from backtesting.decorators import std_parameterized
from engine.data.data_manager import fetch_datas, get_fastest_timeframe_data, reshape_slow_timeframe_data_to_fast
from engine.optuna_processing import get_suggested_value
from engine.process_study_result import get_standard_result_from_study, get_html_pf_plot, get_signal_dict_from_pf
from indicators.indicator_library import indicator_library, get_indicator_key_value, get_indicator_run_results, \
    get_chart_options_value
from indicators.indicator_run_caching import clear_indicator_run_cache
from models import BtRequest, StratRun, CvResult, StandardResult
import optuna

from splitters.splitter_definitions import get_default_splitter


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

    action_string = action_string.replace('and', '&').replace('or', '|').replace('not', '~')

    fixed_action_string_words = []

    for word in action_string.split():
        left_brack = False
        right_brack = False
        if '(' in word:
            left_brack = True
        if ')' in word:
            right_brack = True

        word = word.replace('(', '').replace(')', '')

        process, process_len = None, None
        if '#' in word:
            word, whole_process = word.split('#')

            if '.' not in whole_process:
                raise ValueError('process not valid, validation at model level failed')

            process, process_len = whole_process.split('.')

        if word in indicator_run_results:
            fixed_word = f'indicator_run_results["{word}"]'
            if process and process_len:
                fixed_word = f'np.array(pd.Series({fixed_word}).{process}({process_len}))'

        elif word in indicator_aliases and '.' not in word:  # then this must intend to reference the default value
            for key in indicator_run_results:
                if word in key:
                    fixed_word = f'indicator_run_results["{key}"]'
                    if process and process_len:
                        fixed_word = f'np.array(pd.Series({fixed_word}).{process}({process_len}))'
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


def get_trial_kwargs(trial, kwargs_to_add, bt_request):
    trial_kwargs = {}

    for kwargs_set in kwargs_to_add:
        for key, value in kwargs_set.items():
            if not isinstance(value, list):
                trial_kwargs[key] = value
                continue

            suggested_value = round(get_suggested_value(trial, suggestion_key=key, value=value), 5)

            trial_kwargs[key] = suggested_value

    if bt_request.sl_stop:
        if isinstance(bt_request.sl_stop, list):
            trial_kwargs['sl_stop'] = round(get_suggested_value(trial, suggestion_key='sl_stop',
                                                                value=bt_request.sl_stop), 5)
        else:
            trial_kwargs['sl_stop'] = bt_request.sl_stop

    if bt_request.tp_stop:
        if isinstance(bt_request.tp_stop, list):
            trial_kwargs['tp_stop'] = round(get_suggested_value(trial, suggestion_key='tp_stop',
                                                                value=bt_request.tp_stop), 5)
        else:
            trial_kwargs['tp_stop'] = bt_request.tp_stop

    if bt_request.fee:
        trial_kwargs['fee'] = bt_request.fee

    if bt_request.slippage:
        trial_kwargs['slippage'] = bt_request.slippage

    return trial_kwargs


def get_pf_objective_value(pf, objective_value):
    if objective_value == 'sharpe_ratio':
        return pf.sharpe_ratio.iloc[0]
    elif objective_value == 'sortino':
        return pf.sortino_ratio.iloc[0]
    elif objective_value == 'calmar':
        return pf.calmar_ratio.iloc[0]
    elif objective_value == 'omega':
        return pf.omega_ratio.iloc[0]
    elif objective_value == 'max_drawdown':
        return pf.max_drawdown.iloc[0]
    elif objective_value == 'total_return':
        return pf.total_return.iloc[0] * 100
    else:
        raise ValueError(f'Objective value {objective_value} not recognized')  # todo <- add all pf.stats values here


def get_direction_from_objective_value(objective_value):
    if objective_value == 'sharpe_ratio':
        return 'maximize'
    elif objective_value == 'sortino':
        return 'maximize'
    elif objective_value == 'calmar':
        return 'maximize'
    elif objective_value == 'omega':
        return 'maximize'
    elif objective_value == 'max_drawdown':
        return 'minimize'
    elif objective_value == 'total_return':
        return 'maximize'
    else:
        raise ValueError(f'Objective value {objective_value} not recognized')  # todo <- add all pf.stats values here


def run_study(bt_request: BtRequest) -> StandardResult | CvResult:
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

    def std_objective(trial, action_data):
        run_kwargs = get_trial_kwargs(trial=trial, kwargs_to_add=kwargs_to_add, bt_request=bt_request)

        pf, strat_runs = get_pf_and_strat_runs(action_data, bt_request=bt_request, **run_kwargs)
        trial.set_user_attr('pf', pf)
        trial.set_user_attr('strat_runs', strat_runs)

        if isnan(pf.sharpe_ratio.iloc[0]):
            return -100000

        if bt_request.objective_value == 'sharpe_ratio':
            return pf.sharpe_ratio.values[0]
        elif bt_request.objective_value == 'total_return':
            return pf.total_return.values[0]
        else:
            raise ValueError(f'Invalid objective value: {bt_request.objective_value}')

    study_direction = get_direction_from_objective_value(bt_request.objective_value)

    if not bt_request.cross_validate:
        study_name = 'cool_study12'
        study = optuna.create_study(study_name=study_name, direction=study_direction)
        # storage = "sqlite:///{}.db".format(study_name)
        study.optimize(lambda trial: std_objective(trial, action_data=timeframed_data), n_trials=bt_request.n_trials)
        return get_standard_result_from_study(study=study, bt_request=bt_request)

    else:
        timeframed_splitters = {}
        for timeframe, timeframe_data in timeframed_data.items():
            timeframed_splitters[timeframe] = get_default_splitter(timeframe_data.index)
        # Apply splitter to data

        train_studies = []
        test_studies = []

        cv_results = []
        actual_test_result_pfs = []
        actual_test_result_strat_runs = []

        for i in range(len(timeframed_splitters) + 1):
            train_data = {}
            test_data = {}
            for timeframe, timeframe_data in timeframed_data.items():
                timeframed_train_slice = timeframed_splitters[timeframe].splits['train'].iloc[i]
                timeframed_test_slice = timeframed_splitters[timeframe].splits['test'].iloc[i]

                train_data[timeframe] = timeframe_data[timeframed_train_slice]
                test_data[timeframe] = timeframe_data[timeframed_test_slice]

            train_study = optuna.create_study(direction=study_direction)
            train_study.optimize(lambda trial: std_objective(trial, action_data=train_data),
                                 n_trials=bt_request.n_trials)
            train_studies.append(train_study)

            test_study = optuna.create_study(direction=study_direction)
            test_study.optimize(lambda trial: std_objective(trial, action_data=test_data),
                                n_trials=bt_request.n_trials)
            test_studies.append(test_study)

            actual_test_result_pf, strat_runs = get_pf_and_strat_runs(test_data,
                                                                      bt_request=bt_request,
                                                                      **train_study.best_params)
            actual_pf_objective_value = get_pf_objective_value(actual_test_result_pf, bt_request.objective_value)

            actual_test_result_pfs.append(actual_test_result_pf)
            actual_test_result_strat_runs.append(strat_runs)

            actual_value_equals_best_train_value = actual_pf_objective_value == test_study.best_value

            cv_results.append({
                'train_best': train_study.best_value,
                'test_actual': actual_pf_objective_value,
                'train_best_params': train_study.best_params,
                'test_best': test_study.best_value,
                'test_best_params': test_study.best_params if not actual_value_equals_best_train_value
                else train_study.best_params,
            })

        cv_df = pd.DataFrame(cv_results)

        final_test_actual_pf = actual_test_result_pfs[-1]
        final_test_actual_strat_run = actual_test_result_strat_runs[-1]

        signal_dict = get_signal_dict_from_pf(final_test_actual_pf, bt_request.get_signal)

        clear_indicator_run_cache()

        best_trial_pf_visuals_html = get_html_pf_plot(final_test_actual_pf, final_test_actual_strat_run)
        if __debug__:
            Path('temp').mkdir(exist_ok=True)
            with open(f'temp/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_pf_visuals.html', 'wb') as f:
                f.write(best_trial_pf_visuals_html.encode('utf-8'))

        return CvResult(cv_df=cv_df,
                        final_test_best_pf=test_studies[-1].best_trial.user_attrs['pf'],
                        final_test_actual_pf=final_test_actual_pf,
                        final_test_visuals_html=get_html_pf_plot(final_test_actual_pf, final_test_actual_strat_run),
                        signal=signal_dict)


def get_indicator_from_alias(alias: str, rest_indicators):
    for rest_indicator in rest_indicators:
        if rest_indicator.alias == alias:
            return rest_indicator

    raise ValueError(f'Invalid indicator alias: {alias}')


def get_strat_run(indicator_alias, run_value, shaped_run_result: np.array, indicator_run_object, data,
                  bt_request_indicators):
    alias_indicator_map = {rest_indicator.alias: rest_indicator.indicator for rest_indicator in bt_request_indicators}
    base_kwargs = {
        'indicator': alias_indicator_map[indicator_alias],
        'run_value': run_value,
        'data': data,
        'shaped_run_result': shaped_run_result,
    }

    add_to_orders = get_chart_options_value(option='add_to_orders',
                                            **base_kwargs)
    style = get_chart_options_value(option='style',
                                    **base_kwargs)
    y_val = get_chart_options_value(option='y_val',
                                    **base_kwargs)

    return StratRun(style=style, run_object=indicator_run_object, y_val=y_val, add_to_orders=add_to_orders)


def get_pf_and_strat_runs(timeframed_data, bt_request, **kwargs):
    live_run_indicators = get_live_run_indicators(bt_request, kwargs)
    live_run_aliases = [indicator.alias for indicator in live_run_indicators]
    timeframed_run_results = get_timeframed_run_results(timeframed_data, live_run_indicators)

    entry_string = bt_request.entries
    exit_string = bt_request.exits
    for key, value in kwargs.items():
        entry_string = entry_string.replace(key, str(value))
        exit_string = exit_string.replace(key, str(value))

    indicator_run_results = {}
    indicator_strat_runs = {}
    indicator_aliases_added = set()
    for timeframe, indicator_results in timeframed_run_results.items():
        for indicator_alias, run_results in indicator_results.items():
            for run_value, run_result in run_results.items():
                key_val = f'{indicator_alias}.{run_value}'
                indicator_run_results[key_val] = run_result['shaped_run_result']
                if bt_request.get_visuals_html:
                    entry_string_primary_words = [word.split('.')[0] for word in entry_string.split()]
                    exit_string_primary_words = [word.split('.')[0] for word in exit_string.split()]

                    add_conditions = [
                        indicator_alias in entry_string_primary_words,
                        indicator_alias in exit_string_primary_words,
                    ]
                    if any(add_conditions) and indicator_alias not in indicator_aliases_added:
                        indicator_strat_runs[key_val] = get_strat_run(indicator_alias=indicator_alias,
                                                                      indicator_run_object=run_result[
                                                                          'indicator_run_object'],
                                                                      run_value=run_value,
                                                                      data=timeframed_data[timeframe],
                                                                      shaped_run_result=run_result['shaped_run_result'],
                                                                      bt_request_indicators=bt_request.indicators)
                        indicator_aliases_added.add(indicator_alias)

    entry_string = format_action_string(entry_string, indicator_aliases=live_run_aliases,
                                        indicator_run_results=indicator_run_results)

    exit_string = format_action_string(exit_string, indicator_aliases=live_run_aliases,
                                       indicator_run_results=indicator_run_results)

    fastest_timeframed_data, fastest_timeframe = get_fastest_timeframe_data(timeframed_data)

    open = fastest_timeframed_data.open.to_numpy().reshape(len(fastest_timeframed_data.close))
    high = fastest_timeframed_data.high.to_numpy().reshape(len(fastest_timeframed_data.high))
    low = fastest_timeframed_data.low.to_numpy().reshape(len(fastest_timeframed_data.low))
    close = fastest_timeframed_data.close.to_numpy().reshape(len(fastest_timeframed_data.close))
    volume = fastest_timeframed_data.volume.to_numpy().reshape(len(fastest_timeframed_data.volume))

    entry_string = handle_crossed_operator(entry_string)
    exit_string = handle_crossed_operator(exit_string)

    entries = np.where(eval(entry_string), True, False)
    exits = np.where(eval(exit_string), True, False)

    pf = vbt.Portfolio.from_signals(fastest_timeframed_data, entries=entries, exits=exits,
                                    freq=fastest_timeframe)

    return pf, indicator_strat_runs

    # todo - delete stops that are 0 or negative from new pf run_kwargs - still to be built
