import pandas as pd

from dashboard.views import changes_between, filter_deals, latest_per_game
from store import COLUMNS

RUN_A, RUN_B = '2026-11-16T00:00:00Z', '2026-11-17T00:00:00Z'


def _row(run, i, final=50000, pct=50):
    return (run, i, f'Game {i}', 100000, final, pct, f'u{i}')


DF = pd.DataFrame(
    [_row(RUN_A, 1, pct=30), _row(RUN_A, 2, pct=60), _row(RUN_A, 3, final=60000, pct=40),
     _row(RUN_B, 2, pct=60), _row(RUN_B, 3, final=45000, pct=55), _row(RUN_B, 4, pct=80)],
    columns=COLUMNS,
)


def test_filter_by_date_and_discount():
    out = filter_deals(DF, ['2026-11-16'], 50, 100)
    assert set(out.run_at.str[:10]) == {'2026-11-16'} and out.discount_pct.min() >= 50


def test_filter_without_dates_keeps_all_dates():
    assert set(filter_deals(DF, None, 0, 100).run_at.str[:10]) == {'2026-11-16', '2026-11-17'}


def test_changes_between_statuses():
    out = changes_between(DF, RUN_A, RUN_B)
    assert set(out.status) == {'baru', 'berakhir', 'harga berubah'}
    assert dict(zip(out.name, out.status)) == {'Game 1': 'berakhir', 'Game 3': 'harga berubah', 'Game 4': 'baru'}


def test_changes_between_columns():
    out = changes_between(DF, RUN_A, RUN_B)
    assert list(out.columns) == ['name', 'status', 'normal_price', 'final_price_a', 'final_price_b']


def test_empty_data_does_not_crash():
    empty = pd.DataFrame(columns=COLUMNS)
    assert filter_deals(empty, None, 0, 100).empty
    assert changes_between(empty, RUN_A, RUN_B).empty


def test_latest_per_game_one_row_per_game():
    assert len(latest_per_game(DF)) == 4


def test_latest_per_game_uses_latest_row():
    g = latest_per_game(DF).set_index('name').loc['Game 3']
    assert (g.final_price, g.discount_pct) == (45000, 55)


def test_latest_per_game_marks_active_and_first_last_seen():
    out = latest_per_game(DF).set_index('name')
    assert not out.loc['Game 1', 'aktif'] and out.loc['Game 4', 'aktif']
    assert (out.loc['Game 2', 'pertama_terlihat'], out.loc['Game 2', 'terakhir_terlihat']) == (RUN_A, RUN_B)


def test_latest_per_game_uses_given_latest_run():
    only_a = DF[DF.run_at == RUN_A]
    assert not latest_per_game(only_a, RUN_B).aktif.any()


def test_latest_per_game_sorted_by_biggest_discount_and_empty_ok():
    assert list(latest_per_game(DF).discount_pct) == sorted(latest_per_game(DF).discount_pct, reverse=True)
    assert latest_per_game(pd.DataFrame(columns=COLUMNS)).empty
