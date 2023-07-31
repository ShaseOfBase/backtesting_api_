from datetime import datetime


def convert_timeframe_to_seconds(timeframe: str) -> int:
    """ Convert a string period to time in seconds """
    timeframe = timeframe.lower()
    if 'm' in timeframe:
        return int(timeframe.replace('m', '')) * 60
    elif 'h' in timeframe:
        return int(timeframe.replace('h', '')) * 3600
    elif 'd' in timeframe:
        return int(timeframe.replace('d', '')) * 86400
    else:
        raise ValueError(f'Invalid period: {timeframe}')


def get_periods_in_testing_period(testing_period, timeframe: str):
    """ Returns the number of periods in the given testing period """
    seconds_in_timeframe = convert_timeframe_to_seconds(timeframe)

    start = datetime.strptime(testing_period.start, '%Y-%m-%d %H:%M')
    end = datetime.strptime(testing_period.end, '%Y-%m-%d %H:%M')
    seconds_in_testing_period = (end - start).total_seconds()
    periods_in_testing_period = seconds_in_testing_period / seconds_in_timeframe

    return periods_in_testing_period
