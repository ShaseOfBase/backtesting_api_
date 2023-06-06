from datetime import datetime
import vectorbtpro as vbt
from engine.utils import convert_timeframe_to_seconds
from models import TestingPeriod


data_library = {}

def get_periods_in_testing_period(testing_period: TestingPeriod, timeframe: str):
    """ Returns the number of periods in the given testing period """
    seconds_in_timeframe = convert_timeframe_to_seconds(timeframe)

    start = datetime.strptime(testing_period.start, '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(testing_period.end, '%Y-%m-%d %H:%M:%S')
    seconds_in_testing_period = (end - start).total_seconds()
    periods_in_testing_period = seconds_in_testing_period / seconds_in_timeframe

    return periods_in_testing_period


def fetch_datas(source, symbols, timeframes: list, testing_period: TestingPeriod):

    datas = []
    if source == 'binance':
        for timeframe in timeframes:
            data = vbt.BinanceData.fetch(symbols=symbols,
                                         start=testing_period.start,
                                         end=testing_period.end,
                                         timeframe=timeframe,
                                         tz_convert=testing_period.tz)
    else:
        raise ValueError(f'Invalid source: {source}')

    return data
