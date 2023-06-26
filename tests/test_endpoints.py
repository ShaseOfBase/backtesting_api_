import json

from fastapi.testclient import TestClient

from models import BtRequest, TestingPeriod, RestIndicator


def test_bt_request():
    from main import app
    client = TestClient(app)

    tp = TestingPeriod(start='2023-01-15 00:00',
                       end='2023-04-01 00:00',
                       tz='Africa/Johannesburg')

    ri_ma_fast = RestIndicator(alias='fast_ma',
                               indicator='ma',
                               timeframe='1d',
                               normalize=True,
                               run_kwargs=dict(window=[10, 15]))

    ri_ma_slow = RestIndicator(alias='slow_ma',
                               indicator='ma',
                               timeframe='1d',
                               normalize=True,
                               run_kwargs=dict(window=[30, 50]))

    ri_macd = RestIndicator(alias='fast_macd',
                            indicator='macd',  # possible values are hist, macd, signal
                            timeframe='4h',
                            normalize=True,
                            )

    bt_request = BtRequest(symbol='BTCUSDT',
                           testing_period=tp,
                           indicators=[ri_ma_slow, ri_macd, ri_ma_fast],
                           custom_ranges=dict(macd_hist_long=[-0.5, 0.5]),
                           entries='(fast_macd.hist >= macd_hist_long)',
                           exits='fast_macd.hist < 0',
                           n_trials=100)

    response = client.post("/bt", data=bt_request.to_json())
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}, response.json()

    print('test_bt_request passed')


if __name__ == '__main__':
    test_bt_request()
