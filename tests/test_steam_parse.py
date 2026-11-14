from pathlib import Path

from scraper.steam import parse_deals, parse_price

FIX = Path(__file__).parent / "fixtures"
FIXTURE = (FIX / "steam_search_id.json").read_text()
EMPTY = (FIX / "steam_search_empty.json").read_text()


def test_parse_deals_fixture():
    deals = parse_deals(FIXTURE)
    assert len(deals) == 50
    assert all(d.discount_pct > 0 and d.final_price <= d.normal_price for d in deals)


def test_parse_price_formats():
    assert parse_price('Rp 150.000') == 150000
    assert parse_price('Gratis') == 0
    assert parse_price('') is None


def test_parse_deals_empty():
    assert parse_deals(EMPTY) == []


def test_parse_deals_unescapes_names():
    names = [d.name for d in parse_deals(FIXTURE)]
    assert 'Tom & Jerry Racers' in names


def test_parse_deals_skips_rows_without_original_price():
    row_ok = parse_deals(FIXTURE)[0]
    raw = '{"results_html": "<a href=\\"https://store.steampowered.com/app/9/X/\\" data-ds-appid=\\"9\\" class=\\"search_result_row\\"><span class=\\"title\\">NoDiscount</span><div class=\\"col search_price responsive_secondrow\\">Rp 10.000</div></a>"}'
    assert parse_deals(raw) == []
    assert row_ok.app_id == 100000
