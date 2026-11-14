from datetime import datetime, timezone

import pytest

from notify import NotifyError, build_failure_message, build_message, send_message
from scraper.models import Deal
from summary import summarize

UTC = timezone.utc
RUN_AT_UTC = datetime(2026, 11, 17, 0, 0, tzinfo=UTC)


def _deals(first_name='Game 1'):
    return [Deal(i, first_name if i == 1 else f'Game {i}', 100000, 10000, 90, f'u{i}') for i in range(1, 51)]


SUMMARY = summarize(_deals(), None, total_rows=100, run_number=2)


def SUMMARY_WITH_NAME(name):
    return summarize(_deals(name), None, total_rows=100, run_number=2)


class FakeResp:
    def __init__(self, status):
        self.status_code, self.text = status, ''


class fake_session:
    def __init__(self, status=200):
        self.status, self.url, self.json = status, None, None

    def post(self, url, json=None, timeout=None):
        self.url, self.json = url, json
        return FakeResp(self.status)


def test_message_has_spec_fields():
    m = build_message(SUMMARY, RUN_AT_UTC)
    for part in ('Scraping selesai', 'Data diambil : 50 game diskon', 'Per diskon', 'Total data'):
        assert part in m


def test_message_shows_time_in_wib():
    m = build_message(SUMMARY, datetime(2026, 11, 17, 0, 0, tzinfo=UTC))
    assert '07:00' in m and 'Sel, 17 Nov' in m


def test_markdown_chars_stay_literal_and_under_limit():
    m = build_message(SUMMARY_WITH_NAME('A_B *C*'), RUN_AT_UTC)
    assert 'A_B *C*' in m and len(m) <= 4096


def test_very_long_name_is_shortened_and_message_stays_under_limit():
    m = build_message(SUMMARY_WITH_NAME('X' * 5000), RUN_AT_UTC)
    assert len(m) <= 4096


def test_send_uses_plain_text_and_raises_on_error():
    s = fake_session(status=200)
    send_message('T', '1', 'hi', s)
    assert s.url == 'https://api.telegram.org/botT/sendMessage' and 'parse_mode' not in s.json
    with pytest.raises(NotifyError):
        send_message('T', '1', 'hi', fake_session(status=400))


def test_error_message_never_leaks_token():
    with pytest.raises(NotifyError) as e:
        send_message('SECRET-TOKEN', '1', 'hi', fake_session(status=401))
    assert 'SECRET-TOKEN' not in str(e.value)


def test_failure_message_mentions_failure_and_reason():
    m = build_failure_message('boom', RUN_AT_UTC)
    assert 'gagal' in m.lower() and 'boom' in m
