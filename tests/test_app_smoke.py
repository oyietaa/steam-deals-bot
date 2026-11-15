from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from streamlit.testing.v1 import AppTest

from scraper.steam import parse_deals
from store import save_snapshot

APP = str(Path(__file__).resolve().parent.parent / 'dashboard' / 'app.py')
FIXTURE = (Path(__file__).parent / 'fixtures' / 'steam_search_id.json').read_text()
T1 = datetime(2026, 11, 16, tzinfo=timezone.utc)


def test_app_renders_cards_and_changes_with_two_runs(tmp_path, monkeypatch):
    deals = parse_deals(FIXTURE)
    save_snapshot(deals, T1, tmp_path)
    save_snapshot([replace(deals[0], final_price=1)] + deals[2:], T1 + timedelta(days=1), tmp_path)
    monkeypatch.setenv('DEALS_DATA_DIR', str(tmp_path))
    at = AppTest.from_file(APP).run(timeout=30)
    assert not at.exception
    assert [m.label for m in at.metric] == ['Total data', 'Jumlah pengambilan', 'Rata-rata diskon', 'Diskon terbesar']
    assert at.metric[1].value == '2'


def test_app_shows_info_when_no_data(tmp_path, monkeypatch):
    monkeypatch.setenv('DEALS_DATA_DIR', str(tmp_path))
    at = AppTest.from_file(APP).run(timeout=30)
    assert not at.exception and len(at.info) == 1 and len(at.metric) == 0
