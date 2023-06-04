import pandas as pd

from models import IndicatorDataRequest


def get_indicator_data(indicator_data_request: IndicatorDataRequest):
    print(indicator_data_request)
    # todo <- get data from source

    return pd.DataFrame().to_json()