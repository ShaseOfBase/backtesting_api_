from indicators.indicator_data import get_indicator_data
from main import app
import pandas as pd
from models import IndicatorDataRequest, BtRequest


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/bt")
async def say_hello(bt_request: BtRequest):
    index = pd.DatetimeIndex(['2021-01-01', '2021-01-02', '2021-01-03'])
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}, index=index)

    return {"message": f"Hello world"}


@app.post("/indicators")
async def get_indicator_data_post(indicator_data_request: IndicatorDataRequest):  # todo <- convert to object
    indicator_data = get_indicator_data(indicator_data_request)
    return