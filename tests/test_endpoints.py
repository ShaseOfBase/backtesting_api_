import json

from fastapi.testclient import TestClient

from models import BtRequest, TestingPeriod, RestIndicator


def test_bt_request():
    from main import app
    client = TestClient(app)

    tp = TestingPeriod(start='2023-01-01',
                       end='2023-04-01')

    ri = RestIndicator(alias='slow_ma',
                       indicator='ma',
                       timeframe='1d')

    bt_request = BtRequest(symbols=['BTCUSDT', 'ETHUSDT'],
                           testing_period=tp,
                           indicators=[ri, ri],
                           entry='close > slow_ma',
                           exit='close < slow_ma')

    data = {
        "symbols": [
            "string"
        ],
        "testing_period": {
            "start": "asdasd",
            "end": "asdasd",
            "tz": "UTC"
        },
        "indicators": [
            {
                "alias": "string",
                "indicator": "string",
                "timeframe": "string",
                "window": 0,
                "alpha": 0
            }
        ],
        "entry": "string",
        "exit": "string",
        "sl_stop": "0",
        "tp_stop": "0",
        "tsl_stop": "0",
        "parameter_merge": "concat",
        "cross_validation": "none",
        "graph_analysis": False,
        "source": "binance",
        "direction": "long"
    }

    response = client.post("/bt", data=bt_request.to_json())
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}, response.json()

    print('test_bt_request passed')


if __name__ == '__main__':
    test_bt_request()
