import json

from fastapi.testclient import TestClient

from models import BtRequest, TestingPeriod, RestIndicator


def test_bt_request():
    from main import app
    client = TestClient(app)

    tp = TestingPeriod(start='2023-01-15 00:00',
                       end='2023-04-01 00:00')

    ri_ma = RestIndicator(alias='slow_ma',
                          indicator='ma',
                          timeframe='1d',
                          run_kwargs=dict(window=[20, 30, 40, 50]))

    ri_macd = RestIndicator(alias='fast_macd',
                            indicator='macd',  # possible values are hist, macd, signal
                            timeframe='4h',
                            )

    bt_request = BtRequest(symbols=['BTCUSDT', 'ETHUSDT'],
                           testing_period=tp,
                           indicators=[ri_ma, ri_macd],
                           custom_ranges=dict(macd_hist_long=[0, 1, 2]),
                           entries='fast_macd.hist |> macd_hist_long',
                           exits='fast_macd.hist < 0')

    response = client.post("/bt", data=bt_request.to_json())
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}, response.json()

    print('test_bt_request passed')


if __name__ == '__main__':
    test_bt_request()
