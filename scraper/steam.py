import html
import json
import re

from scraper.models import Deal

_ROW = re.compile(r'<a\s(?P<attrs>[^>]*?data-ds-appid="(?P<id>\d+)"[^>]*)>(?P<body>.*?)</a>', re.S)
_HREF = re.compile(r'href="([^"]+)"')
_TITLE = re.compile(r'<span class="title">(.*?)</span>', re.S)
_PCT = re.compile(r'search_discount[^"]*"><span>-(\d+)%</span>')
_STRIKE = re.compile(r'<strike>(.*?)</strike>', re.S)
_FINAL = re.compile(r'<br>\s*([^<]+)')


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
        title, pct, strike, final = (
            _TITLE.search(body), _PCT.search(body), _STRIKE.search(body), _FINAL.search(body)
        )
        if not (title and pct and strike and final):
            continue
        normal, now = parse_price(strike.group(1)), parse_price(final.group(1))
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
