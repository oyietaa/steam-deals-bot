from datetime import datetime, timedelta, timezone

from scraper.models import Deal
from store import latest_snapshot, load_all, save_snapshot

T1 = datetime(2026, 11, 16, 0, 0, tzinfo=timezone.utc)
T2 = T1 + timedelta(days=1)
D = Deal(1, 'Game', 100000, 50000, 50, 'https://store.steampowered.com/app/1/')


def test_roundtrip_keeps_tricky_names(tmp_path):
    d = Deal(1, 'Foo, "Bar" _x_ *y*', 200000, 100000, 50, 'u')
    save_snapshot([d], T1, tmp_path)
    assert latest_snapshot(tmp_path) == [d]


def test_two_runs_in_same_minute_get_distinct_files(tmp_path):
    assert save_snapshot([D], T1, tmp_path) != save_snapshot([D], T1 + timedelta(seconds=1), tmp_path)


def test_same_second_does_not_overwrite(tmp_path):
    a, b = save_snapshot([D], T1, tmp_path), save_snapshot([D], T1, tmp_path)
    assert a != b and a.exists() and b.exists()


def test_all_deals_accumulates(tmp_path):
    save_snapshot([D], T1, tmp_path)
    save_snapshot([D], T2, tmp_path)
    assert len(load_all(tmp_path)) == 2


def test_latest_snapshot_none_when_empty(tmp_path):
    assert latest_snapshot(tmp_path) is None
