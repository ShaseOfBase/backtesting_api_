from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import vectorbtpro as vbt
import pandas as pd
import pytz
from base_config import BaseConfig, valid_sources, valid_symbols, bad_operators, bad_aliases, arithmetic_operators, \
    comparison_operators, flow_operators, valid_timeframes
from engine.utils import get_periods_in_testing_period
from indicators.indicator_library import indicator_library, get_indicator_key_value
import json


@dataclass
class TestingPeriod(json.JSONEncoder):
    start: str
    end: str = None
    tz: str = 'Africa/Johannesburg'

    def to_json(self):
        return json.dumps(self.__dict__)

    def is_valid(self):
        # check start and end dates are of the right format
        try:
            datetime.strptime(self.start, '%Y-%m-%d %H:%M')
            datetime.strptime(self.end, '%Y-%m-%d %H:%M')
        except ValueError:
            raise ValueError(f'Incorrect data format, should be YYYY-MM-DD HH:MM')

        if self.tz not in pytz.all_timezones:
            raise ValueError(f'Timezone {self.tz} not valid')


@dataclass
class RestIndicator(json.JSONEncoder):
    alias: str
    indicator: str
    timeframe: str
    normalize: Optional[bool] = True
    run_kwargs: Optional[dict] = None

    def to_json(self):
        return json.dumps(self.__dict__)

    def __post_init__(self):
        self.indicator = self.indicator.lower()

    def is_valid(self):
        if self.process:
            if '.' not in self.process:
                raise ValueError(f'Process {self.process} must contain a dot followed by a value (e.g. diff.3)')
            process = self.process.split('.')[0]
            if process not in ['diff', 'mean', 'median']:
                raise ValueError(f'Process {self.process} not valid, expecting diff, mean or median')

        if not self.alias.isalnum():
            raise ValueError(f'Alias {self.alias} must be alphanumeric')

        if '__' in self.alias:
            raise ValueError(f'Alias {self.alias} cannot contain double underscores')

        if len(self.alias) < 3:
            raise ValueError(f'Alias {self.alias} must be at least 3 characters')

        if len(self.alias) > 20:
            raise ValueError(f'Alias {self.alias} must be at most 20 characters')

        # Check indicator is in indicator library
        if self.indicator not in indicator_library:
            raise ValueError(f'Indicator {self.indicator} not in indicator library')

        if self.timeframe not in valid_timeframes:
            raise ValueError(f'Timeframe {self.timeframe} not in valid timeframes')

        if self.run_kwargs:
            if not isinstance(self.run_kwargs, dict):
                raise ValueError(f'run_values must be a dictionary')

            if not all(isinstance(value, (int, float)) for key, value in self.run_kwargs.items()):
                raise ValueError(f'run_kwargs value must be an int or float')

            avlbl_run_kwargs = get_indicator_key_value(self.indicator, 'run_kwargs')
            avlbl_run_keys = avlbl_run_kwargs.keys()

            for key, value in self.run_kwargs.items():
                if key not in avlbl_run_keys:
                    raise ValueError(f'run_kwargs key {key} not in available keys {avlbl_run_keys}')

                if len(self.run_kwargs[key]) not in [2, 3]:
                    raise ValueError(f'run_kwargs value must be 2 or 3 values')

        return True


@dataclass
class TriggerPair(json.JSONEncoder):
    alias: str
    entry: str
    exit: str

    def __post_init__(self):
        self.validate()

    def validate(self):
        for trigger in [self.entry, self.exit]:
            if '#' in trigger:
                for word in trigger.split():
                    if '#' not in word:
                        continue
                    split_word = word.split('#')

                    if '.' not in split_word[1]:
                        raise ValueError('Process must be in the format of indicator_alias<.indicator_specifier>'
                                         '#process.process_len (e.g. my_macd.hist#diff.2)')
                    process = split_word[1].split('.')[0]
                    if process not in ['diff', 'mean', 'median']:
                        raise ValueError(f'Process {process} not valid, expecting diff, mean or median')

            if len(trigger) > BaseConfig.max_trigger_len:
                raise ValueError(f'Entry or exit conditions exceed max length of {BaseConfig.max_trigger_len}')

            for bad_operator in bad_operators:
                if bad_operator in trigger or bad_operator in trigger:
                    raise ValueError(f'Invalid operator {bad_operator} in entry or exit conditions')

        if len(self.alias) > 30:
            raise ValueError(f'Alias {self.alias} must be at most 30 characters')

    @classmethod
    def from_dict(self, d):
        return TriggerPair(**d)


@dataclass
class BtRequest(json.JSONEncoder):
    symbol: str
    testing_period: TestingPeriod | dict
    indicators: List[RestIndicator] | List[dict]
    custom_ranges: Optional[dict]
    trigger_pairs: List[TriggerPair] | List[dict]
    sl_stop: Optional[float] = 0.0
    tp_stop: Optional[float] = 0.0
    tsl_stop: Optional[float] = 0.0
    fee: Optional[float] = 0.0
    slippage: Optional[float] = 0.0
    n_trials: Optional[int] = 10
    objective_value: Optional[str] = 'sharpe_ratio'
    parameter_merge: Optional[str] = 'concat'
    cross_validate: Optional[str] = 'none'
    get_visuals_html: Optional[bool] = False
    source: str = 'binance'
    direction: str = 'long' # 'short | long | both'
    get_signal: bool = False

    def __repr__(self):
        return f'BtRequest: {self.__dict__}'

    # todo <- create jsonify and de-jsonify methods

    def __post_init__(self):
        self.trigger_pairs = [TriggerPair.from_dict(trigger_pair) for trigger_pair in self.trigger_pairs]
        self.validate()
        print(1)

    def to_json(self):
        indicator_dicts = []
        for indicator in self.indicators:
            indicator_dicts.append(indicator.__dict__)

        self.indicators = indicator_dicts
        self.testing_period = self.testing_period.__dict__

        self.trigger_pairs = [trigger_pair.__dict__ for trigger_pair in self.trigger_pairs]

        result = json.dumps(self.__dict__)
        return result

    def validate(self):
        trigger_aliases = set()
        for trigger in self.trigger_pairs:
            if trigger.alias in trigger_aliases:
                raise ValueError(f'Trigger alias "{trigger.alias}" must be unique')
            trigger.validate()
            trigger_aliases.add(trigger.alias)

        if self.source not in valid_sources:
            raise ValueError(f'Invalid source {self.source}, must be one of {valid_sources}')

        if not self.trigger_pairs:
            raise ValueError('At least one set of triggers with an entry and exit must be specified')

        if len(self.indicators) > BaseConfig.max_indicators:
            raise ValueError(f'Too many indicators, max {BaseConfig.max_indicators}')

        for key, value in self.custom_ranges.items():
            if len(value) not in [2, 3]:
                raise ValueError(f'Custom range {key} must have 2 or 3 values')

        known_indicator_aliases = set()
        for indicator in self.indicators:
            if indicator.alias in bad_aliases:
                raise ValueError(f'Invalid alias {indicator.alias} in indicators')
            known_indicator_aliases.add(indicator.alias)

        for timeframe in {indicator.timeframe for indicator in self.indicators}:
            periods_in_testing_period = get_periods_in_testing_period(testing_period=self.testing_period,
                                                                      timeframe=timeframe)
            if periods_in_testing_period > BaseConfig.max_periods_in_testing_period:
                raise ValueError(f'Testing period exceeds max periods in testing period of '
                                 f'{BaseConfig.max_periods_in_testing_period} for timeframe {timeframe}')

@dataclass
class IndicatorDataRequest(json.JSONEncoder):
    source: str
    symbols: list
    timeframes: dict
    indicators: list
    graph_analysis: Optional[bool]

    def to_json(self):
        return json.dumps(self.__dict__)

    def is_valid(self):
        if self.source not in valid_sources:
            raise ValueError(f'Invalid source {self.source}, must be one of {valid_sources}')

        for symbol in self.symbols:
            if not isinstance(symbol, str):
                raise ValueError(f'Invalid symbol {symbol}, must be a string')

            if symbol not in valid_symbols:
                raise ValueError(f'Invalid symbol {symbol}, must be one of {valid_symbols}')


@dataclass
class CvResult:
    '''Consists of multiple study results and test results'''
    cv_df: pd.DataFrame
    final_test_best_pf: vbt.Portfolio
    final_test_actual_pf: pd.DataFrame
    html_visuals: dict
    signal: Optional[dict] = None


@dataclass
class StandardResult:
    optuna_df: pd.DataFrame
    best_params: dict
    best_objective_value: float
    best_trial_pf_stats: dict
    best_trial_pf_visuals_html: str
    signal: Optional[dict] = None


class StratRun:
    def __init__(self, style: str, run_object, y_val, add_to_orders=False):
        if style not in ['raw', 'pure']:
            raise ValueError(f'Invalid style: {style}')
        self.style = style
        self.run_object = run_object
        self.y_val = y_val
        self.add_to_orders = add_to_orders


