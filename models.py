from dataclasses import dataclass
from typing import Optional, List
import numpy as np
import json
from base_config import BaseConfig
from indicators.indicator_library import indicator_library
from json_parsing.string_library import valid_timeframes, bad_aliases, bad_operators
from json_parsing.validate_sources import valid_sources
from json_parsing.validate_symbols import valid_symbols


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
#				  {'alias': 'ma_fast_daily',
#                   'timeframe': '1d',
#					'indicator': 'ma',
#					'window': 20
#				  },],
#	'parameter_merge': 'concat' # default concat, add the other one(s) at a later date
 #   'entries_t1': ['adx > 25 @4h', 'close < bbands.middle @1d'],
#	'exits_t2': ['adx < adx_long @4h', 'close > bbands.upper * 1.03 @1d'],
#	'exits_t3': ['adx < 16 @4h'],
#	'cross_validation': 'rolling 3',
#	'graph_analysis': true # <- error, graph_analysis requires scalar parameters only. see https://helper for details
#}

# returns all pf results, if graph_analysis -> returns graph_html as well as parameter grid result.
# headers return cost of the call, total


@dataclass
class RestIndicator:
    alias: str
    indicator: str
    timeframe: str
    window: Optional[int] | Optional[float] | Optional[list]
    alpha: Optional[int] | Optional[float] | Optional[list]

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

        # Check window is valid
        # todo

        # Check alpha is valid
        # todo

        return True


@dataclass
class BtRequest:
    source: str
    symbols: list
    timeframes: dict
    indicators: List[RestIndicator]
    parameter_merge: Optional[str]
    entry: str
    exit: str
    sl_stop: Optional[str]
    tp_stop: Optional[str]
    tsl_stop: Optional[str]
    cross_validation: Optional[str]
    graph_analysis: Optional[bool]
    direction: str = 'long'  # 'short | long | both'

    def __post_init__(self):
        if self.source not in valid_sources:
            raise ValueError(f'Invalid source {self.source}, must be one of {valid_sources}')

        if not self.entry:
            raise ValueError('At least one entry condition must be specified')

        if not self.exit:
            raise ValueError('At least one exit condition must be specified')

    def __repr__(self):
        return f'BtRequest: {self.__dict__}'

    def to_json(self):
        return json.dumps(self.__dict__)

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


@dataclass
class IndicatorDataRequest:
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


