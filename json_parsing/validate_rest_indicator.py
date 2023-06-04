from indicators.indicator_library import indicator_library
from models import RestIndicator


def validate_rest_indicator(rest_indicator: RestIndicator):
    # Check alias contains only letters and numbers and has at least 3 letters and
# is at least length 3 and at most length 20
    if not rest_indicator.alias.isalnum():
        raise ValueError(f'Alias {rest_indicator.alias} must be alphanumeric')

    if len(rest_indicator.alias) < 3:
        raise ValueError(f'Alias {rest_indicator.alias} must be at least 3 characters')

    if len(rest_indicator.alias) > 20:
        raise ValueError(f'Alias {rest_indicator.alias} must be at most 20 characters')

    # Check indicator is in indicator library
    if rest_indicator.indicator.lower() not in indicator_library:
        raise ValueError(f'Indicator {rest_indicator.indicator} not in indicator library')

    # Check window is valid
    # todo

    # Check alpha is valid
    # todo

    return True


