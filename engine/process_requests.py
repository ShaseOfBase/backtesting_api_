from engine.data.data_manager import fetch_datas
from models import BtRequest


def process_bt_request(bt_request: BtRequest):
    datas = fetch_datas(source=bt_request.source,
                        symbols=bt_request.symbols,
                        timeframes=[indicator.timeframe for indicator in bt_request.indicators],
                        testing_period=bt_request.testing_period)



