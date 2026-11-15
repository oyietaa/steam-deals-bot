from pathlib import Path

from scraper.models import Deal
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


def test_parse_deals_first_row_matches_real_response():
    assert parse_deals(FIXTURE)[0] == Deal(
        227300, 'Euro Truck Simulator 2', 185999, 46499, 75,
        'https://store.steampowered.com/app/227300/Euro_Truck_Simulator_2/',
    )


def test_parse_deals_keeps_apostrophes_and_commas_in_names():
    names = [d.name for d in parse_deals(FIXTURE)]
    assert "Zombies Aren't Real" in names and 'Warhammer 40,000: Dawn of War IV' in names


def test_parse_deals_skips_rows_without_discount_block():
    raw = (
        '{"results_html": "<a href=\\"https://store.steampowered.com/app/9/X/\\" data-ds-appid=\\"9\\" '
        'class=\\"search_result_row\\"><span class=\\"title\\">NoDiscount</span>'
        '<div class=\\"discount_final_price\\">Rp 10 000</div></a>"}'
    )
    assert parse_deals(raw) == []
