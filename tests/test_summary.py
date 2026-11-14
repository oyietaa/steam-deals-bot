from dataclasses import replace

from scraper.models import Deal
from summary import summarize, tier


def _d(i, pct=50, final=50000):
    return Deal(i, f'Game {i}', 100000, final, pct, f'https://store.steampowered.com/app/{i}/')


DEALS_50 = [_d(i, pct=90 - i) for i in range(1, 51)]
PREVIOUS = [_d(i) for i in range(1, 51)]
CURRENT = [_d(i) for i in range(18, 68)]
CURRENT = [replace(d, final_price=40000) if d.app_id in (20, 21) else d for d in CURRENT]


def test_tier_boundaries():
    assert [tier(p) for p in (75, 74, 50, 49, 25, 24)] == ['>=75', '50-74', '50-74', '25-49', '25-49', '<25']


def test_first_run_all_new():
    s = summarize(DEALS_50, None, total_rows=50, run_number=1)
    assert (s.new, s.existing, s.ended) == (50, 0, 0)


def test_second_run_diff():
    s = summarize(CURRENT, PREVIOUS, total_rows=100, run_number=2)
    assert (s.new, s.existing, s.ended, s.price_changed) == (17, 33, 17, 2)


def test_top_and_new_limited_to_three():
    s = summarize(DEALS_50, None, 50, 1)
    assert len(s.top_discounts) == 3 and len(s.new_deals) == 3


def test_tiers_cover_all_keys_and_sum_to_count():
    s = summarize(DEALS_50, None, 50, 1)
    assert set(s.tiers) == {'>=75', '50-74', '25-49', '<25'} and sum(s.tiers.values()) == s.count == 50


def test_top_discounts_are_the_highest():
    s = summarize(DEALS_50, None, 50, 1)
    assert [d.discount_pct for d in s.top_discounts] == [89, 88, 87]
