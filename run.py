import os
import sys
from datetime import datetime, timezone

from notify import NotifyError, build_failure_message, build_message, send_message
from scraper.steam import ScrapeError, fetch_deals
from store import latest_snapshot, load_all, save_snapshot
from summary import summarize


def main() -> int:
    token, chat_id = os.environ.get('TELEGRAM_BOT_TOKEN'), os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print('TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID harus diisi', file=sys.stderr)
        return 1
    run_at = datetime.now(timezone.utc)
    try:
        deals = fetch_deals()
        if not deals:
            raise ScrapeError('Steam tidak mengembalikan data diskon')
    except Exception as exc:
        try:
            send_message(token, chat_id, build_failure_message(str(exc), run_at))
        except NotifyError as notify_exc:
            print(f'notifikasi gagal terkirim: {notify_exc}', file=sys.stderr)
        return 1
    previous = latest_snapshot()
    save_snapshot(deals, run_at)
    all_rows = load_all()
    summary = summarize(deals, previous, total_rows=len(all_rows), run_number=all_rows['run_at'].nunique())
    try:
        send_message(token, chat_id, build_message(summary, run_at))
    except NotifyError as exc:
        print(f'notifikasi gagal terkirim: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
