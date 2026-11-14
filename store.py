from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from scraper.models import Deal

COLUMNS = ['run_at', 'app_id', 'name', 'normal_price', 'final_price', 'discount_pct', 'url']
_READ = dict(dtype={'run_at': str, 'name': str, 'url': str}, keep_default_na=False)


def _snapshot_dir(root: Path) -> Path:
    return Path(root) / 'snapshots'


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, **_READ)


def save_snapshot(deals: list[Deal], run_at: datetime, root: Path = Path('data')) -> Path:
    root = Path(root)
    snap_dir = _snapshot_dir(root)
    snap_dir.mkdir(parents=True, exist_ok=True)
    utc = run_at.astimezone(timezone.utc)
    stamp = utc.strftime('%Y-%m-%dT%H%M%SZ')
    path, n = snap_dir / f'{stamp}.csv', 2
    while path.exists():
        path, n = snap_dir / f'{stamp}_{n}.csv', n + 1
    rows = [
        (utc.strftime('%Y-%m-%dT%H:%M:%SZ'), d.app_id, d.name, d.normal_price, d.final_price, d.discount_pct, d.url)
        for d in deals
    ]
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)
    frames = [_read_csv(p) for p in sorted(snap_dir.glob('*.csv'))]
    pd.concat(frames, ignore_index=True).to_csv(root / 'all_deals.csv', index=False)
    return path


def load_all(root: Path = Path('data')) -> pd.DataFrame:
    path = Path(root) / 'all_deals.csv'
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return _read_csv(path)


def latest_snapshot(root: Path = Path('data')) -> list[Deal] | None:
    files = sorted(_snapshot_dir(Path(root)).glob('*.csv'))
    if not files:
        return None
    df = _read_csv(files[-1])
    return [
        Deal(int(r.app_id), r.name, int(r.normal_price), int(r.final_price), int(r.discount_pct), r.url)
        for r in df.itertuples(index=False)
    ]
