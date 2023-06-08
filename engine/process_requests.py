from engine.data.data_manager import fetch_datas
from indicators.indicator_library import indicator_library
from models import BtRequest


def process_bt_request(bt_request: BtRequest):
    timeframed_data = fetch_datas(source=bt_request.source,
                        symbols=bt_request.symbols,
                        timeframes=[indicator.timeframe for indicator in bt_request.indicators],
                        testing_period=bt_request.testing_period)


    for timeframe, data in timeframed_data.items():
        for rest_indicator in bt_request.indicators:
            if rest_indicator.timeframe == timeframe:
                # todo - get indicator kwargs from indicator_library
                indicator_data = indicator_library[rest_indicator.indicator]['indicator'].run()

                rest_indicator.data = indicator_data








    print(1)



