import os
from datetime import datetime

import numpy as np
import pandas as pd
import vectorbtpro as vbt

from base_config import BaseConfig
from models import TestingPeriod

data_library = {}


def convert_std_timeframe_to_pandas_timeframe(timeframe: str):
    """ Convert a standard timeframe to a pandas timeframe """
    timeframe = timeframe.lower()
    if 'm' in timeframe:
        return f'{timeframe.replace("m", "T")}'

    return timeframe


def get_minutes_from_timeframe(timeframe: str):
    ''' Get the number of minutes from a timeframe '''
    timeframe = timeframe.lower()
    if 'm' in timeframe:
        return int(timeframe.replace('m', ''))
    elif 'h' in timeframe:
        return int(timeframe.replace('h', '')) * 60
    elif 'd' in timeframe:
        return int(timeframe.replace('d', '')) * 60 * 24


def get_fastest_timeframe_data(timeframed_data: dict):
    """ Get the fastest timeframe data from a dict of timeframed data """
    fastest_timeframe_mins = 0
    fastest_timeframe = None
    for timeframe in timeframed_data:
        if not fastest_timeframe:
            fastest_timeframe_mins = get_minutes_from_timeframe(timeframe)
            fastest_timeframe = timeframe
            continue

        timeframe_minutes = get_minutes_from_timeframe(timeframe)
        if timeframe_minutes < fastest_timeframe_mins:
            fastest_timeframe_mins = timeframe_minutes
            fastest_timeframe = timeframe

    return timeframed_data[fastest_timeframe]


def get_merged_data(testing_period, timeframe, symbol, source='binance'):  # todo customize for sources & different tzs
    base_local_data_folder = BaseConfig.resources.local_data

    testing_period_start = datetime.strptime(testing_period.start, '%Y-%m-%d %H:%M')
    testing_period_end = datetime.strptime(testing_period.end, '%Y-%m-%d %H:%M')

    pd_timeframe = convert_std_timeframe_to_pandas_timeframe(timeframe)

    required_files = set()
    period_index = pd.date_range(start=testing_period_start, end=testing_period_end, freq=pd_timeframe,
                                 inclusive='left')
    periods_required_sr = pd.Series(data=np.full(len(period_index), False), index=period_index)

    symbol_timeframe_data_folder = base_local_data_folder / f'{symbol}/{timeframe}'
    local_data_files = symbol_timeframe_data_folder.glob('*')

    for filename in local_data_files:
        start_str = filename.name.split('_')[0]
        end_str = filename.name.split('_')[1].split('.')[0]
        file_start = datetime.strptime(start_str, '%Y-%m-%d %H-%M-%S')
        file_end = datetime.strptime(end_str, '%Y-%m-%d %H-%M-%S')

        if file_start > testing_period_end or file_end < testing_period_start:
            continue

        file_range = pd.date_range(start=file_start, end=file_end, freq=pd_timeframe)

        file_needed = False
        for period in file_range:
            if period in period_index and periods_required_sr.loc[period] == False:
                file_needed = True
                periods_required_sr.loc[period] = True

        if file_needed:
            required_files.add(symbol_timeframe_data_folder / filename.name)

        if periods_required_sr.all():
            break

    periods_still_needed = periods_required_sr[~periods_required_sr].index

    if len(periods_still_needed):
        end_period = periods_still_needed[-1] + pd.Timedelta(pd_timeframe)
        total_period = pd.date_range(start=periods_still_needed[0], end=end_period, freq=pd_timeframe)

        period_chunks = [total_period[i:i + BaseConfig.data_batch_len] for i in range(0, len(total_period),
                                                                                      BaseConfig.data_batch_len)]

        for period_chunk in period_chunks:
            data = vbt.BinanceData.fetch([symbol],
                                         start=period_chunk[0],
                                         end=period_chunk[-1],
                                         timeframe=timeframe,
                                         execute_kwargs={'engine': 'threadpool'})
            filename = f'{periods_still_needed[0]}_{periods_still_needed[-1]}'.replace(':', '-')
            full_file_path = symbol_timeframe_data_folder / filename
            if not os.path.exists(symbol_timeframe_data_folder):
                full_file_path.mkdir(parents=True)

            data.save(full_file_path)
            required_files.add(full_file_path)

    data_pieces = []
    for full_file_path in required_files:
        data_piece = vbt.BinanceData.load(full_file_path)
        data_pieces.append(data_piece)

    data = vbt.BinanceData.merge(data_pieces)

    return data.loc[testing_period_start.strftime('%Y-%m-%d %H:%M'):testing_period_end.strftime('%Y-%m-%d %H:%M')]


def fetch_datas(source, symbol, timeframes: list, testing_period: TestingPeriod):
    datas = {}

    for timeframe in timeframes:
        data = get_merged_data(testing_period=testing_period,
                               timeframe=timeframe,
                               symbol=symbol,
                               source=source)
        datas[timeframe] = data

    return datas


