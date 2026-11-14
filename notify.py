from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from summary import RunSummary

_DAYS = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
_LIMIT = 4096


class NotifyError(Exception):
    pass


def _stamp(run_at: datetime) -> str:
    t = run_at.astimezone(ZoneInfo('Asia/Jakarta'))
    return f'{_DAYS[t.weekday()]}, {t.day} {_MONTHS[t.month - 1]}, {t:%H:%M}'


def _rp(n: int) -> str:
    return 'Rp ' + f'{n:,}'.replace(',', '.')


def _line(d) -> str:
    name = d.name if len(d.name) <= 60 else d.name[:57] + '...'
    return f'- {name} (-{d.discount_pct}%) {_rp(d.final_price)} dari {_rp(d.normal_price)}'


def build_message(s: RunSummary, run_at: datetime) -> str:
    t = s.tiers
    lines = [
        f'Scraping selesai ({_stamp(run_at)})',
        f'Data diambil : {s.count} game diskon',
        f'Baru / sudah ada : {s.new} / {s.existing}',
        f'Per diskon   : >=75%: {t[">=75"]} | 50-74%: {t["50-74"]} | 25-49%: {t["25-49"]} | <25%: {t["<25"]}',
        f'Berakhir / harga berubah : {s.ended} / {s.price_changed}',
        'Diskon terbesar:',
        *[_line(d) for d in s.top_discounts],
        'Game baru:',
        *([_line(d) for d in s.new_deals] or ['- (tidak ada)']),
        f'Total data   : {s.total_rows} (pengambilan ke-{s.run_number})',
    ]
    return '\n'.join(lines)[:_LIMIT]


def build_failure_message(error: str, run_at: datetime) -> str:
    return f'Scraping gagal ({_stamp(run_at)})\nAlasan: {error[:500]}\nTidak ada data baru yang disimpan.'


def send_message(token: str, chat_id: str, text: str, session: requests.Session | None = None) -> None:
    session = session or requests.Session()
    resp = session.post(f'https://api.telegram.org/bot{token}/sendMessage',
                        json={'chat_id': chat_id, 'text': text}, timeout=20)
    if resp.status_code != 200:
        raise NotifyError(f'Telegram menolak pesan (HTTP {resp.status_code})')
