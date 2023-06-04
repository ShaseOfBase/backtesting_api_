from fastapi.testclient import TestClient

from models import BtRequest, TestingPeriod, RestIndicator


def test_bt_request():
    from main import app
    client = TestClient(app)

    tp = TestingPeriod(start='2023-01-01',
                       end='2023-04-01').to_json()

    ri = RestIndicator(alias='slow_ma',
                       indicator='ma',
                       timeframe='1d').to_json()


    bt_request = BtRequest(symbols=['BTCUSDT', 'ETHUSDT'],
                           testing_period=tp,
                           indicators=[ri, ri],
                           entry='close > slow_ma',
                           exit='close < slow_ma')

    response = client.post("/bt", json=bt_request.to_json())
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}, response.json()

    print('test_bt_request passed')


if __name__ == '__main__':
    test_bt_request()