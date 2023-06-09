from pathlib import Path

valid_sources = {'binance'}
valid_symbols = {'BTCUSDT', 'ETHUSDT'}
bad_operators = {'!', '&', '|', '&&', '||', 'in', 'not in', 'not is', 'not is not', 'xor', '^'}
bad_aliases = {'and', 'or', 'not', 'is', 'is not', 'in', 'not in', 'not is', 'not is not', 'xor', '^', 'eval',
               'exec', 'import', 'from', 'as', 'global', 'nonlocal', 'assert', 'async', 'await', 'break', 'class',
               'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'if', 'lambda', 'pass',
               'raise', 'return', 'try', 'while', 'with', 'yield', 'True', 'False', 'None', 'self', 'cls',
               'indicator', 'window', 'alpha', 'alias', 'timeframe', 'timeframes'}
arithmetic_operators = {'+', '-', '*', '/', '%'}
comparison_operators = {'<', '>', '==', '>=', '<=', '!=', '|>', '<|'}
flow_operators = {'and', 'or', 'not', 'is', 'is not', '|', '&'}
valid_timeframes = {'1m', '5m', '15m', '30m', '1h', '2h', '4h', '8h', '12h', '1d'}
valid_timezones = {'UTC', 'Africa/Johannesburg'}


class SubConfig:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return str(self.__dict__)

class BaseConfig:
    max_param_combinations = 1000
    max_entry_exit_len = 50
    max_periods_in_testing_period = 1000
    max_indicators = 10
    data_batch_len = 200

    resources = SubConfig(
        local_data=Path('resources/local_data')
    )



