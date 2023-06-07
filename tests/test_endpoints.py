import json

from fastapi.testclient import TestClient

from models import BtRequest, TestingPeriod, RestIndicator


def test_bt_request():
    from main import app
    client = TestClient(app)

    tp = TestingPeriod(start='2023-01-01 00:00',
                       end='2023-02-01 00:00')

    ri = RestIndicator(alias='slow_ma',
                       indicator='ma',
                       timeframe='1d')

    bt_request = BtRequest(symbols=['BTCUSDT', 'ETHUSDT'],
                           testing_period=tp,
                           indicators=[ri, ri],
                           entry='close > slow_ma',
                           exit='close < slow_ma')

    response = client.post("/bt", data=bt_request.to_json())
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}, response.json()

    print('test_bt_request passed')


if __name__ == '__main__':
    test_bt_request()
