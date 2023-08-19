import json

from fastapi.testclient import TestClient

from models import BtRequest, TestingPeriod, RestIndicator, TriggerPair


def test_bt_request():
    from main import app
    client = TestClient(app)

    tp = TestingPeriod(start='2022-01-15 00:00',
                       end='2023-04-01 00:00',
                       tz='Africa/Johannesburg')

    ri_ma_fast = RestIndicator(alias='fast_ma',
                               indicator='ma',
                               timeframe='4h',
                               normalize=True,
                               run_kwargs=dict(window=[10, 20]))

    ri_ma_slow = RestIndicator(alias='slow_ma',
                               indicator='ma',
                               timeframe='12h',
                               normalize=True,
                               run_kwargs=dict(window=[25, 70]))

    ri_macd = RestIndicator(alias='fast_macd',
                            indicator='macd',  # possible values are hist, macd, signal
                            timeframe='4h',
                            normalize=True,
                            )

    tp_a = TriggerPair(
        alias='lost_cause',
        entry='(fast_macd.hist#diff.diff_diffs >= macd_hist_long) and (close > slow_ma)',
        exit='(fast_macd.hist < 0) or (close < slow_ma)'
    )

    tp_b = TriggerPair(
        alias='lost_cause2',
        entry='fast_macd.hist >= macd_hist_long',
        exit='fast_macd.hist < macd_hist_short'
    )

    macd_conditions = [
        'fast_macd.hist#diff.diff_diffs >= macd_hist_long',
        'fast_macd.hist >= macd_hist_long',
        'fast_macd.hist#diff.diff_diffs >= macd_hist_long',
    ]

 #   for _ in range(10):
  #      entry_type_a = f'({pos_a} and {pos_b}) or {pos_c}'

    try:
        bt_request = BtRequest(symbol='BTCUSDT',
                               testing_period=tp,
                               indicators=[ri_ma_slow, ri_macd, ri_ma_fast],
                               custom_ranges=dict(macd_hist_long=[-1, 1.],
                                                  macd_hist_short = [-1,0.],
                                                  diff_diffs=[1, 3]),
                               trigger_pairs=[tp_b.__dict__],
                               n_trials=15,
                               get_visuals_html=True,
                               get_signal=True,
                               cross_validate='standard',)
        json_bt_request = bt_request.to_json()

    except Exception as e:
        raise e

    response = client.post("/bt", data=json_bt_request)
    assert response.status_code == 200
    assert response.json() == {"message": "Hello world"}, response.json()

    print('test_bt_request passed')


if __name__ == '__main__':
    test_bt_request()
