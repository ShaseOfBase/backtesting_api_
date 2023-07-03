from datetime import datetime
from pathlib import Path

import numpy as np
import vectorbtpro as vbt
from models import AssessmentResult, BtRequest


def get_assessment_result_from_study(study, bt_request: BtRequest) -> AssessmentResult:

    optuna_df = study.trials_dataframe()
    best_trial = study.best_trial
    best_params = study.best_params
    best_objective_value = study.best_value

    best_trial_pf = best_trial.user_attrs['pf']
    best_trial_pf_stats = best_trial_pf.stats()

    if bt_request.get_signal:
        order_records_df = best_trial_pf.orders.records_readable
        signal_order = order_records_df.iloc[-1]

        signal_dict = {
            'value': signal_order['Side'],
            'price': signal_order['Price'],
            'datetime': signal_order['Signal Index']
        }
    else:
        signal_dict = {
            'value': None,
            'price': None,
            'datetime': None
        }

    if bt_request.get_visuals_html:
        strat_runs_dict = best_trial.user_attrs['strat_runs']
        best_trial_pf_visuals_html = get_html_pf_plot(best_trial_pf, strat_runs_dict)
        if __debug__:
            Path('temp').mkdir(exist_ok=True)
            with open(f'temp/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_pf_visuals.html', 'wb') as f:
                f.write(best_trial_pf_visuals_html.encode('utf-8'))
    else:
        best_trial_pf_visuals_html = None

    return AssessmentResult(optuna_df=optuna_df,
                            best_params=best_params,
                            best_objective_value=best_objective_value,
                            best_trial_pf_stats=best_trial_pf_stats,
                            best_trial_pf_visuals_html=best_trial_pf_visuals_html,
                            signal=signal_dict)


def get_html_pf_plot(pf: vbt.Portfolio, strat_runs_dict: dict) -> str:

    subplots = [('orders_v2', {'title': 'orders_v2'}),
                'trade_pnl',
                'cum_returns']

    for i, (plot_name, strat_run) in enumerate(strat_runs_dict.items(), start=1):  # <- places this after the first item
        if strat_run.add_to_orders:
            continue
        subplots.insert(i, (plot_name, {'title': plot_name}))

    fig = pf.plot(subplots=subplots)

    pf.exit_trades.plot(title='orders_v2', fig=fig, add_trace_kwargs=dict(row=1, col=1))

    real_entries = (pf.orders.side.to_pd()
                    .replace(0, 2)
                    .replace(1, False)
                    .replace(np.nan, False)
                    .replace(2, True))

    real_exits = (pf.orders.side.to_pd()
                  .replace(1, 2)
                  .replace(0, False)
                  .replace(np.nan, False)
                  .replace(2, True))

    for i, (plot_name, strat_run) in enumerate(strat_runs_dict.items(), start=2):
        row = 1 if strat_run.add_to_orders else i
        if strat_run.style == 'raw':
            strat_run.run_object.vbt.plot(title=plot_name, fig=fig, add_trace_kwargs=dict(row=row, col=1))
        elif strat_run.style == 'pure':
            strat_run.run_object.plot(title=plot_name, fig=fig, add_trace_kwargs=dict(row=row, col=1))

        if strat_run.add_to_orders:
            continue

        real_entries.vbt.signals.plot_as_entry_marks(fig=fig, y=strat_run.y_val, add_trace_kwargs=dict(row=i, col=1))
        real_exits.vbt.signals.plot_as_exit_marks(fig=fig, y=strat_run.y_val, add_trace_kwargs=dict(row=i, col=1))

    return fig.to_html()