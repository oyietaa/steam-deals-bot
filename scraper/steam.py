import html
import json
import re
import time
from urllib import robotparser

import requests

from scraper.models import Deal

UA = 'steam-deals-bot/0.1 (student project)'
BASE = 'https://store.steampowered.com'
SEARCH_URL = BASE + '/search/results/'


class ScrapeError(Exception):
    pass

_ROW = re.compile(r'<a\s(?P<attrs>[^>]*?data-ds-appid="(?P<id>\d+)"[^>]*)>(?P<body>.*?)</a>', re.S)
_HREF = re.compile(r'href="([^"]+)"')
_TITLE = re.compile(r'<span class="title">(.*?)</span>', re.S)
_PCT = re.compile(r'class="discount_pct"[^>]*>-?(\d+)%</div>')
_ORIGINAL = re.compile(r'class="discount_original_price">(.*?)</div>', re.S)
_FINAL = re.compile(r'class="discount_final_price">(.*?)</div>', re.S)


def parse_price(text: str) -> int | None:
    t = html.unescape(text).strip()
    if not t:
        return None
    if t.lower() in ('gratis', 'free'):
        return 0
    digits = re.sub(r'\D', '', t)
    return int(digits) if digits else None


def parse_deals(raw: str) -> list[Deal]:
    results_html = json.loads(raw).get('results_html', '')
    deals: list[Deal] = []
    for m in _ROW.finditer(results_html):
        body = m.group('body')
        title, pct, original, final = (
            _TITLE.search(body), _PCT.search(body), _ORIGINAL.search(body), _FINAL.search(body)
        )
        if not (title and pct and original and final):
            continue
        normal, now = parse_price(original.group(1)), parse_price(final.group(1))
        if normal is None or now is None:
            continue
        href = _HREF.search(m.group('attrs'))
        deals.append(Deal(
            app_id=int(m.group('id')),
            name=html.unescape(title.group(1)).strip(),
            normal_price=normal,
            final_price=now,
            discount_pct=int(pct.group(1)),
            url=href.group(1).split('?')[0] if href else '',
        ))
    return deals


def _get(session, url: str, params: dict | None, delay: float):
    last = 'unknown'
    for attempt in range(3):
        try:
            resp = session.get(url, params=params, headers={'User-Agent': UA}, timeout=20)
            if resp.status_code == 200 or (resp.status_code == 404 and url.endswith('/robots.txt')):
                return resp
            last = f'HTTP {resp.status_code}'
        except requests.RequestException as exc:
            last = str(exc)
        if delay and attempt < 2:
            time.sleep(delay)
    raise ScrapeError(f'gagal mengambil {url}: {last}')


def fetch_deals(limit: int = 50, cc: str = 'id', session: requests.Session | None = None,
                delay: float = 1.5) -> list[Deal]:
    session = session or requests.Session()
    robots = _get(session, BASE + '/robots.txt', None, delay)
    rp = robotparser.RobotFileParser()
    rp.parse(robots.text.splitlines() if robots.status_code == 200 else [])
    rp.modified()
    if not rp.can_fetch(UA, SEARCH_URL):
        raise ScrapeError('robots.txt melarang pengambilan halaman pencarian')
    deals: list[Deal] = []
    seen: set[int] = set()
    start = 0
    while len(deals) < limit:
        count = min(50, limit - len(deals))
        params = {'query': '', 'start': start, 'count': count, 'specials': 1, 'infinite': 1, 'cc': cc}
        raw = _get(session, SEARCH_URL, params, delay).text
        if delay:
            time.sleep(delay)
        page = parse_deals(raw)
        if not page:
            if not deals and 'search_result_row' in raw:
                raise ScrapeError('Steam mengembalikan data tetapi format tidak dikenali (parser perlu diperbarui)')
            break
        for d in page:
            if d.app_id not in seen:
                seen.add(d.app_id)
                deals.append(d)
        start += count
        total = json.loads(raw).get('total_count')
        if total is not None and start >= total:
            break
    return deals[:limit]
