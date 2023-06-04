import re

from indicators.indicator_library import indicator_library
from json_parsing.string_library import bad_operators, arithmetic_operators, comparison_operators, flow_operators, \
    valid_timeframes

max_len = 50


def get_validated_entry_exit_str(entry_exit_str: str, indicators: list[dict]) -> tuple:
    # bt_str eg. 'adx < adx_long or close > bbands.upper * 1.03'
    # split away from the @
    entry_exit_str = entry_exit_str.strip()


    if len(entry_exit_str) > max_len:
        raise ValueError(f'bt_str too long: {entry_exit_str}')


    split_ee_string = entry_exit_str.split(' ')
    for word in split_ee_string:
        if word in known_indicator_aliases:
            continue
        if word in arithmetic_operators or word in comparison_operators or word in flow_operators or \
                word.isnumeric() or word in indicator_library:
            continue
        else:
            raise ValueError(f'Invalid word {word} in {entry_exit_str}')

    return ' '.join(split_ee_string), timeframe


def get_signal_string()










