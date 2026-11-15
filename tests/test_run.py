import pandas as pd
import pytest

import run
from notify import NotifyError
from scraper.models import Deal
from scraper.steam import ScrapeError


def _deals(n):
    return [Deal(i, f'Game {i}', 100000, 50000, 50, f'u{i}') for i in range(1, n + 1)]


class Fakes:
    def __init__(self, monkeypatch, deals=None, fetch_exc=None, send_exc=None):
        self.saved, self.sent = [], []
        deals = [] if deals is None else deals

        def fetch(*a, **k):
            if fetch_exc:
                raise fetch_exc
            return deals

        def save(ds, run_at, *a, **k):
            self.saved.append(ds)
            return 'p'

        def send(token, chat_id, text, *a, **k):
            self.sent.append(text)
            if send_exc and len(self.saved) > 0:
                raise send_exc

        monkeypatch.setattr(run, 'fetch_deals', fetch)
        monkeypatch.setattr(run, 'latest_snapshot', lambda *a, **k: None)
        monkeypatch.setattr(run, 'save_snapshot', save)
        monkeypatch.setattr(run, 'load_all', lambda *a, **k: pd.DataFrame({'run_at': ['t'] * len(deals)}))
        monkeypatch.setattr(run, 'send_message', send)


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'T')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '1')


@pytest.fixture
def fakes(monkeypatch):
    return Fakes(monkeypatch, deals=_deals(50))


@pytest.fixture
def fakes_empty(monkeypatch):
    return Fakes(monkeypatch, deals=[])


@pytest.fixture
def fakes_20(monkeypatch):
    return Fakes(monkeypatch, deals=_deals(20))


def test_success_saves_one_snapshot_and_sends_one_message(env, fakes):
    assert run.main() == 0
    assert len(fakes.saved) == 1 and len(fakes.sent) == 1


def test_zero_deals_sends_failure_and_saves_nothing(env, fakes_empty):
    assert run.main() == 1
    assert fakes_empty.saved == [] and 'gagal' in fakes_empty.sent[0].lower()


def test_fewer_than_50_still_reports_actual_count(env, fakes_20):
    assert run.main() == 0 and 'Data diambil : 20 game diskon' in fakes_20.sent[0]


def test_scrape_error_sends_failure_and_saves_nothing(env, monkeypatch):
    f = Fakes(monkeypatch, fetch_exc=ScrapeError('robots melarang'))
    assert run.main() == 1
    assert f.saved == [] and 'robots melarang' in f.sent[0]


def test_telegram_failure_after_save_returns_1_but_keeps_snapshot(env, monkeypatch):
    f = Fakes(monkeypatch, deals=_deals(50), send_exc=NotifyError('x'))
    assert run.main() == 1
    assert len(f.saved) == 1


def test_missing_token_returns_1(monkeypatch):
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
    monkeypatch.setenv('TELEGRAM_CHAT_ID', '1')
    assert run.main() == 1
