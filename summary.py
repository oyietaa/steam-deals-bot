from dataclasses import dataclass

from scraper.models import Deal


def tier(pct: int) -> str:
    if pct >= 75:
        return '>=75'
    if pct >= 50:
        return '50-74'
    if pct >= 25:
        return '25-49'
    return '<25'


@dataclass(frozen=True)
class RunSummary:
    count: int
    new: int
    existing: int
    ended: int
    price_changed: int
    tiers: dict[str, int]
    top_discounts: list[Deal]
    new_deals: list[Deal]
    total_rows: int
    run_number: int


def summarize(current: list[Deal], previous: list[Deal] | None, total_rows: int, run_number: int) -> RunSummary:
    prev = {d.app_id: d for d in (previous or [])}
    cur = {d.app_id: d for d in current}
    new_deals = [d for d in current if d.app_id not in prev]
    both = [d for d in current if d.app_id in prev]
    tiers = {k: 0 for k in ('>=75', '50-74', '25-49', '<25')}
    for d in current:
        tiers[tier(d.discount_pct)] += 1
    by_discount = lambda ds: sorted(ds, key=lambda d: (-d.discount_pct, d.name))[:3]
    return RunSummary(
        count=len(current),
        new=len(new_deals),
        existing=len(both),
        ended=sum(1 for i in prev if i not in cur),
        price_changed=sum(1 for d in both if d.final_price != prev[d.app_id].final_price),
        tiers=tiers,
        top_discounts=by_discount(current),
        new_deals=by_discount(new_deals),
        total_rows=total_rows,
        run_number=run_number,
    )
