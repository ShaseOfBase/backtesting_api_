from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import pytz
from base_config import BaseConfig, valid_sources, valid_symbols, bad_operators, bad_aliases, arithmetic_operators, \
    comparison_operators, flow_operators, valid_timeframes
from engine.utils import get_periods_in_testing_period
from indicators.indicator_library import indicator_library, get_indicator_key_value
import json


@dataclass
class TestingPeriod(json.JSONEncoder):
    start: str
    end: str
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
    normalize: bool = True
    run_kwargs: Optional[dict] = None

    def to_json(self):
        return json.dumps(self.__dict__)

    def __post_init__(self):
        self.indicator = self.indicator.lower()

    def is_valid(self):
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
class BtRequest(json.JSONEncoder):
    symbol: str
    testing_period: TestingPeriod | dict
    indicators: List[RestIndicator] | List[dict]
    custom_ranges: Optional[dict]
    entries: str
    exits: str
    sl_stop: Optional[float] = 0.0
    tp_stop: Optional[float] = 0.0
    tsl_stop: Optional[float] = 0.0
    fee: Optional[float] = 0.0
    slippage: Optional[float] = 0.0
    n_trials: Optional[int] = 10
    objective_value: Optional[str] = 'sharpe_ratio'
    parameter_merge: Optional[str] = 'concat'
    cross_validation: Optional[str] = 'none'
    graph_analysis: Optional[bool] = False
    source: str = 'binance'
    direction: str = 'long' # 'short | long | both'
    get_signal: bool = False

    def is_valid(self):
        if self.source not in valid_sources:
            raise ValueError(f'Invalid source {self.source}, must be one of {valid_sources}')

        if not self.entries:
            raise ValueError('At least one entry condition must be specified')

        if not self.exits:
            raise ValueError('At least one exit condition must be specified')

        if len(self.indicators) > BaseConfig.max_indicators:
            raise ValueError(f'Too many indicators, max {BaseConfig.max_indicators}')

        for key, value in self.custom_ranges.items():
            if len(value) not in [2, 3]:
                raise ValueError(f'Custom range {key} must have 2 or 3 values')


    def __repr__(self):
        return f'BtRequest: {self.__dict__}'

    def to_json(self):
        indicator_dicts = []
        for indicator in self.indicators:
            indicator_dicts.append(indicator.__dict__)

        self.indicators = indicator_dicts
        self.testing_period = self.testing_period.__dict__

        result = json.dumps(self.__dict__)
        return result

    def validate(self):
        if not self.entries or not self.exits:
            raise ValueError('At least one entry and one exit condition must be specified')

        known_indicator_aliases = set()
        for indicator in self.indicators:
            if indicator['alias'] in bad_aliases:
                raise ValueError(f'Invalid alias {indicator["alias"]} in indicators')
            known_indicator_aliases.add(indicator['alias'])

        if len(self.entries) > BaseConfig.max_entry_exit_len or len(self.exits) > BaseConfig.max_entry_exit_len:
            raise ValueError(f'Entry or exit conditions exceed max length of {BaseConfig.max_entry_exit_len}')

        for bad_operator in bad_operators:
            if bad_operator in self.entries or bad_operator in self.exits:
                raise ValueError(f'Invalid operator {bad_operator} in entry or exit conditions')

        for word in (self.entries + self.exits).split(' '):
            if word in known_indicator_aliases:
                raise ValueError(f'Invalid alias {word} in entry or exit conditions')
            if word in arithmetic_operators or word in comparison_operators or word in flow_operators or \
                    word.isnumeric() or word in indicator_library:
                continue
            else:
                raise ValueError(f'Invalid word {word} in entry or exit conditions')

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


