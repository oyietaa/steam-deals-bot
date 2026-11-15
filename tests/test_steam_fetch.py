import json

import pytest

from scraper.steam import ScrapeError, fetch_deals


class FakeResp:
    def __init__(self, status, text):
        self.status_code, self.text = status, text


def _row(i):
    return (
        f'<a href="https://store.steampowered.com/app/{i}/G{i}/?snr=1" data-ds-appid="{i}" class="search_result_row">'
        f'<span class="title">Game {i}</span>'
        f'<div class="discount_block"><div class="discount_pct">-50%</div><div class="discount_prices">'
        f'<div class="discount_original_price">Rp 100 000</div><div class="discount_final_price">Rp 50 000</div>'
        f'</div></div></a>'
    )


class FakeSession:
    def __init__(self, total=50, robots='', status=200):
        self.total, self.robots, self.status = total, robots, status
        self.calls, self.last_headers = 0, None

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls += 1
        self.last_headers = headers
        if self.status != 200:
            return FakeResp(self.status, '')
        if url.endswith('/robots.txt'):
            return FakeResp(200, 'User-agent: *\n' + self.robots + '\n')
        start, count = int(params['start']), int(params['count'])
        rows = ''.join(_row(i) for i in range(start, min(start + count, self.total)))
        return FakeResp(200, json.dumps({'success': 1, 'total_count': self.total, 'results_html': rows}))


def fake_pages(total, robots=''):
    return FakeSession(total=total, robots=robots)


def failing_session():
    return FakeSession(status=500)


def test_fetch_stops_at_limit():
    assert len(fetch_deals(limit=50, session=fake_pages(total=80), delay=0)) == 50


def test_fetch_returns_fewer_when_source_has_fewer():
    assert len(fetch_deals(limit=50, session=fake_pages(total=20), delay=0)) == 20


def test_fetch_sends_honest_user_agent():
    s = fake_pages(total=50)
    fetch_deals(session=s, delay=0)
    assert 'steam-deals-bot' in s.last_headers['User-Agent']


def test_fetch_raises_after_three_failures():
    s = failing_session()
    with pytest.raises(ScrapeError):
        fetch_deals(session=s, delay=0)
    assert s.calls == 3


def test_fetch_respects_robots_disallow():
    with pytest.raises(ScrapeError):
        fetch_deals(session=fake_pages(total=50, robots='Disallow: /'), delay=0)


def test_fetch_reports_unrecognized_format_instead_of_silent_empty():
    class Odd(FakeSession):
        def get(self, url, params=None, headers=None, timeout=None):
            if url.endswith('/robots.txt'):
                return FakeResp(200, 'User-agent: *\n')
            return FakeResp(200, json.dumps({'total_count': 5, 'results_html': '<a class="search_result_row"><b>x</b></a>'}))

    with pytest.raises(ScrapeError, match='format'):
        fetch_deals(session=Odd(), delay=0)
