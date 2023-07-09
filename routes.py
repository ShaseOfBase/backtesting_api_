from engine.process_requests import run_study
from engine.process_study_result import get_standard_result_from_study
from indicators.indicator_data import get_indicator_data
from main import app
import pandas as pd
from models import IndicatorDataRequest, BtRequest


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/bt")
async def say_hello(bt_request: BtRequest):
    study = run_study(bt_request)
    study_results = get_standard_result_from_study(study, bt_request)

    return {"message": f"Hello world"}


@app.post("/indicators")
async def get_indicator_data_post(indicator_data_request: IndicatorDataRequest):  # todo <- convert to object
    indicator_data = get_indicator_data(indicator_data_request)
    return