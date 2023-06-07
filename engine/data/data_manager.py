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


def get_merged_data(testing_period, timeframe, symbols, source='binance'):  # todo customize for sources & different tzs
    base_local_data_folder = BaseConfig.resources.local_data

    testing_period_start = datetime.strptime(testing_period.start, '%Y-%m-%d %H:%M')
    testing_period_end = datetime.strptime(testing_period.end, '%Y-%m-%d %H:%M')

    pd_timeframe = convert_std_timeframe_to_pandas_timeframe(timeframe)

    required_files = set()
    for symbol in symbols:
        symbol_timeframe_data_folder = base_local_data_folder / f'{symbol}/{timeframe}'
        local_data_files = symbol_timeframe_data_folder.glob('*.csv')

        period_index = pd.date_range(start=testing_period_start, end=testing_period_end, freq=pd_timeframe)
        periods_required_sr = pd.Series(data=np.full(len(period_index), False), index=period_index)

        for full_filename in local_data_files:
            start_str = full_filename.name.split('_')[0]
            end_str = full_filename.name.split('_')[1].split('.')[0]
            file_start = datetime.strptime(start_str, '%Y-%m-%d-%H-%M')
            file_end = datetime.strptime(end_str, '%Y-%m-%d-%H-%M')

            file_range = pd.date_range(start=file_start, end=file_end, freq=pd_timeframe)

            if file_range[0] in period_index or file_range[-1] in period_index:
                required_files.add(symbol_timeframe_data_folder / full_filename.name)
                periods_required_sr.loc[file_range] = True

            if periods_required_sr.all():
                break

        periods_still_needed = periods_required_sr[~periods_required_sr].index

        if len(periods_still_needed):
            data = vbt.BinanceData.fetch(symbols=symbols,
                                         start=periods_still_needed[0],
                                         end=periods_still_needed[-1],
                                         timeframe=timeframe,
                                         execute_kwargs={'engine': 'threadpool'},)
            full_filename = f'{periods_still_needed[0]}_{periods_still_needed[-1]}' # todo <- file type?
            data.save(symbol_timeframe_data_folder / full_filename)
            required_files.add(symbol_timeframe_data_folder / full_filename)

    data_pieces = []
    for full_filename in required_files:
        data_piece = vbt.BinanceData.load(full_filename)
        data_pieces.append(data_piece)

    data = vbt.BinanceData.merge(data_pieces)

    return data

def fetch_datas(source, symbols, timeframes: list, testing_period: TestingPeriod):
    datas = {}

    for timeframe in timeframes:
        data = get_merged_data(testing_period=testing_period,
                               timeframe=timeframe,
                               symbols=symbols,
                               source=source)
        datas[timeframe] = data


    return data