import pandas as pd

_OUT = ['name', 'status', 'normal_price', 'final_price_a', 'final_price_b']


def filter_deals(df: pd.DataFrame, run_dates: list[str] | None, min_pct: int, max_pct: int) -> pd.DataFrame:
    mask = df['discount_pct'].between(min_pct, max_pct)
    if run_dates is not None:
        mask &= df['run_at'].str[:10].isin(run_dates)
    return df[mask]


def changes_between(df: pd.DataFrame, run_a: str, run_b: str) -> pd.DataFrame:
    a = df[df['run_at'] == run_a].set_index('app_id')
    b = df[df['run_at'] == run_b].set_index('app_id')
    rows = []
    for app_id in a.index.union(b.index):
        in_a, in_b = app_id in a.index, app_id in b.index
        if in_a and in_b:
            if a.at[app_id, 'final_price'] == b.at[app_id, 'final_price']:
                continue
            status = 'harga berubah'
        else:
            status = 'baru' if in_b else 'berakhir'
        ref = b if in_b else a
        rows.append({
            'name': ref.at[app_id, 'name'],
            'status': status,
            'normal_price': ref.at[app_id, 'normal_price'],
            'final_price_a': a.at[app_id, 'final_price'] if in_a else None,
            'final_price_b': b.at[app_id, 'final_price'] if in_b else None,
        })
    return pd.DataFrame(rows, columns=_OUT)
