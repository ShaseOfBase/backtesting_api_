from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import pandas as pd
import pytz
from base_config import BaseConfig, valid_sources, valid_symbols, bad_operators, bad_aliases, arithmetic_operators, \
    comparison_operators, flow_operators, valid_timeframes
from engine.utils import get_periods_in_testing_period
from indicators.indicator_library import indicator_library
import json


#{
#	'source': 'binance',
#	'symbols': ['BTCUSDT', 'ETHUSDT'],
#   'testing_period': {'start': '2023-02-01 00:00', 'end': '2023-03-03 14:00', tz='UTC'},
#	'data_periods': [ {'alias': 'my_4h',
#               	'timeframe': '4h',
#                   'start': '2023-02-01 00:00', 'end': '2023-03-03 14:00', tz='UTC'},
#					{'alias': 'my_4h',
#               	'timeframe': '4h',
#                   'start': '2023-02-01 00:00', 'end': '2023-03-03 14:00', tz='UTC'},  # defaults to now - 30 periods
#				  ],
#	'indicators': [{'alias': 'ma_slow',
#                   'timeframe': '4h',
#					'indicator': 'ma',
#					'window': [40, 50, 60]
#				  },
#				  {'alias': 'ma_fast',
#                   'timeframe': '4h',
#					'indicator': 'ma',
#					'window': [12, 15, 18]
#				  },
#				  {'alias': 'bbands',
#                   'timeframe': '1d',
#					'indicator': 'bbands',
#                   'values': [lower, middle, upper, bandwidth],
#					'window': 20
#				  },],
#	'parameter_merge': 'concat' # default concat, add the other one(s) at a later date
 #   'entry': 'adx > 25 @4h', 'close < bbands.middle @1d'],
#	'exits': ['adx < adx_long @4h', 'close > bbands.upper * 1.03 @1d'],
#	'cross_validation': 'rolling 3',
#	'graph_analysis': true # <- error, graph_analysis requires scalar parameters only. see https://helper for details
#}

# returns all pf results, if graph_analysis -> returns graph_html as well as parameter grid result.
# headers return cost of the call, total


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
    data: pd.Series = None
    window: Optional[int] | Optional[float] | Optional[list] = 0
    alpha: Optional[int] | Optional[float] | Optional[list] = 0

    def to_json(self):
        return json.dumps(self.__dict__)

    def __post_init__(self):
        self.indicator = self.indicator.lower()

    def is_valid(self):
        if not self.alias.isalnum():
            raise ValueError(f'Alias {self.alias} must be alphanumeric')

        if len(self.alias) < 3:
            raise ValueError(f'Alias {self.alias} must be at least 3 characters')

        if len(self.alias) > 20:
            raise ValueError(f'Alias {self.alias} must be at most 20 characters')

        # Check indicator is in indicator library
        if self.indicator not in indicator_library:
            raise ValueError(f'Indicator {self.indicator} not in indicator library')

        if self.timeframe not in valid_timeframes:
            raise ValueError(f'Timeframe {self.timeframe} not in valid timeframes')

        # Check alpha is valid
        # todo

        return True


@dataclass
class BtRequest(json.JSONEncoder):
    symbols: list
    testing_period: TestingPeriod | dict
    indicators: List[RestIndicator] | List[dict]
    entry: str
    exit: str
    sl_stop: Optional[str] = 0
    tp_stop: Optional[str] = 0
    tsl_stop: Optional[str] = 0
    fee: Optional[float] = 0.0
    slippage: Optional[float] = 0.0
    parameter_merge: Optional[str] = 'concat'
    cross_validation: Optional[str] = 'none'
    graph_analysis: Optional[bool] = False
    source: str = 'binance'
    direction: str = 'long'  # 'short | long | both'

    def is_valid(self):
        if self.source not in valid_sources:
            raise ValueError(f'Invalid source {self.source}, must be one of {valid_sources}')

        if not self.entry:
            raise ValueError('At least one entry condition must be specified')

        if not self.exit:
            raise ValueError('At least one exit condition must be specified')

        if len(self.indicators) > BaseConfig.max_indicators:
            raise ValueError(f'Too many indicators, max {BaseConfig.max_indicators}')

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
        if not self.entry or not self.exit:
            raise ValueError('At least one entry and one exit condition must be specified')

        known_indicator_aliases = set()
        for indicator in self.indicators:
            if indicator['alias'] in bad_aliases:
                raise ValueError(f'Invalid alias {indicator["alias"]} in indicators')
            known_indicator_aliases.add(indicator['alias'])

        if len(self.entry) > BaseConfig.max_entry_exit_len or len(self.exit) > BaseConfig.max_entry_exit_len:
            raise ValueError(f'Entry or exit conditions exceed max length of {BaseConfig.max_entry_exit_len}')

        for bad_operator in bad_operators:
            if bad_operator in self.entry or bad_operator in self.exit:
                raise ValueError(f'Invalid operator {bad_operator} in entry or exit conditions')

        for word in (self.entry + self.exit).split(' '):
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


