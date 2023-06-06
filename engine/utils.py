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