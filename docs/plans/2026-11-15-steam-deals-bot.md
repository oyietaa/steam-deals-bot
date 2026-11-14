# Steam Deals Bot Implementation Plan

> **Untuk pelaksana:** gunakan sub-skill superpowers:subagent-driven-development (disarankan) atau superpowers:executing-plans untuk mengerjakan rencana ini tugas demi tugas. Langkah memakai kotak centang (`- [ ]`).

**Goal:** Bot yang tiap 3 hari mengambil 50 game diskon Steam lewat GitHub Actions, mengirim ringkasan ke Telegram, dan menyajikan semua data di dashboard Streamlit.

**Architecture:** Satu skrip Python dijalankan GitHub Actions sesuai jadwal: ambil data, bandingkan dengan pengambilan sebelumnya, simpan CSV di repositori, kirim ringkasan lewat Bot API Telegram. Dashboard Streamlit membaca CSV gabungan dari repositori yang sama. Logika murni (parse, diff, pesan) dipisah dari jaringan supaya bisa dites tanpa internet.

**Tech Stack:** Python 3.12, requests, pandas, pytest, streamlit, GitHub Actions.

**Spec:** Rancangan: Bot Scraping Diskon Steam (https://claude.ai/artifact/7aDf1QYrumGdG3VCS3V2KD)

## Global Constraints

- 50 game per pengambilan (diubah pengguna 15 November; menggantikan usulan 100 di spec).
- Harga dalam Rupiah (kode negara Indonesia, `cc=id`).
- Jadwal tiap 3 hari ditambah tombol Run workflow (`workflow_dispatch`).
- Token bot hanya sebagai GitHub secret `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID`, tidak pernah di repositori.
- Jeda antar-request dan User-Agent yang jujur; robots.txt dibaca dulu.
- Satu CSV per pengambilan di `data/snapshots/` dan satu berkas gabungan `data/all_deals.csv`.
- Kelompok diskon: `>=75`, `50-74`, `25-49`, `<25`; status perubahan: baru, berakhir, harga berubah.
- Repositori publik; dashboard di Streamlit Community Cloud; tidak ada bot interaktif.
- Presentasi Rabu 18 November 2026, dengan minimal 2 pengambilan sebelumnya.
- Jika Steam tidak bisa diakses dari GitHub: pindah ke Hacker News dengan struktur yang sama.

## Review Focus

1. Steam mengembalikan kurang dari 50 game atau kosong: yang ada disimpan dan pesan menyebut jumlah sebenarnya; kosong berarti tidak ada snapshot dan notifikasi gagal terkirim (Task 3, 7).
2. Pengambilan pertama tanpa snapshot sebelumnya: semua game "baru", tidak ada "berakhir", tanpa error (Task 5).
3. Format harga tak terduga (`Rp 150.000`, `Gratis`, tanpa harga normal): menjadi angka tanpa crash (Task 2).
4. Nama game berisi koma, kutip, atau karakter Markdown (`_`, `*`): CSV tetap utuh dan pesan Telegram terkirim sebagai teks biasa (Task 4, 6).
5. Dua run berdekatan (manual dan terjadwal): nama snapshot unik dan tidak ada data hilang saat push (Task 4, 7).

---

## File Structure

| File | Tanggung jawab |
| --- | --- |
| `scraper/models.py` | dataclass `Deal` |
| `scraper/steam.py` | `parse_price`, `parse_deals` (murni), `fetch_deals` (jaringan) |
| `store.py` | simpan dan muat snapshot CSV |
| `summary.py` | `tier`, `summarize`, `RunSummary` |
| `notify.py` | susun dan kirim pesan Telegram |
| `run.py` | orkestrasi satu pengambilan |
| `dashboard/views.py`, `dashboard/app.py` | fungsi data dan tampilan Streamlit |
| `.github/workflows/scrape.yml` | jadwal dan tombol Run workflow |
| `tests/` | satu berkas tes per modul, plus `tests/fixtures/` |

### Task 1: Fondasi repositori dan uji kelayakan

**Files:**
- Create: `.github/workflows/probe.yml`, `requirements.txt`, `README.md`, `tests/fixtures/steam_search_id.json`, `tests/fixtures/steam_search_empty.json`

**Interfaces:**
- Produces: fixture respons Steam nyata (50 entri) dan fixture kosong; secret Telegram terpasang.

- [ ] **Step 1:** Buat repositori publik `steam-deals-bot`, buat bot lewat BotFather, ambil chat ID, simpan `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` sebagai Actions secrets.
- [ ] **Step 2:** Tulis `probe.yml` (`workflow_dispatch`) yang memanggil halaman pencarian Steam dengan filter diskon (`specials=1`, `count=50`, `cc=id`), menyimpan responsnya sebagai artifact, dan mengirim satu pesan uji ke Telegram.
- [ ] **Step 3:** Jalankan workflow. Hasil yang diharapkan: pesan uji tiba di Telegram dan respons memuat 50 game diskon dengan harga Rupiah. Jika Steam menolak dari server GitHub (403 atau kosong), berhenti dan laporkan ke pengguna untuk pindah ke Hacker News.
- [ ] **Step 4:** Simpan respons artifact sebagai `tests/fixtures/steam_search_id.json`; buat `steam_search_empty.json` dengan struktur sama tanpa entri. Commit: `git commit -m "chore: repo, probe workflow, fixtures"`.

### Task 2: Model dan parser

**Files:**
- Create: `scraper/models.py`, `scraper/steam.py`, `tests/test_steam_parse.py`

**Interfaces:**
- Produces: `Deal(app_id: int, name: str, normal_price: int, final_price: int, discount_pct: int, url: str)` (frozen dataclass, harga dalam Rupiah utuh); `parse_price(text: str) -> int | None`; `parse_deals(raw: str) -> list[Deal]`.

- [ ] **Step 1: Tulis tes yang gagal**

```python
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
```

- [ ] **Step 2:** Jalankan `pytest tests/test_steam_parse.py -v`. Diharapkan: FAIL (fungsi belum ada).
- [ ] **Step 3:** Implementasikan `Deal`, `parse_price`, `parse_deals` terhadap fixture nyata dari Task 1; entri tanpa harga normal dilewati.
- [ ] **Step 4:** Jalankan tes yang sama. Diharapkan: PASS. Commit: `feat: steam parser`.

### Task 3: Pengambilan dari Steam

**Files:**
- Modify: `scraper/steam.py`
- Test: `tests/test_steam_fetch.py`

**Interfaces:**
- Consumes: `parse_deals` (Task 2).
- Produces: `fetch_deals(limit: int = 50, cc: str = 'id', session: requests.Session | None = None, delay: float = 1.5) -> list[Deal]`; `class ScrapeError(Exception)`.

- [ ] **Step 1: Tulis tes yang gagal** (session palsu, tanpa internet)

```python
def test_fetch_stops_at_limit():
    assert len(fetch_deals(limit=50, session=fake_pages(total=80), delay=0)) == 50

def test_fetch_returns_fewer_when_source_has_fewer():
    assert len(fetch_deals(limit=50, session=fake_pages(total=20), delay=0)) == 20

def test_fetch_sends_honest_user_agent():
    s = fake_pages(total=50); fetch_deals(session=s, delay=0)
    assert 'steam-deals-bot' in s.last_headers['User-Agent']

def test_fetch_raises_after_three_failures():
    with pytest.raises(ScrapeError): fetch_deals(session=failing_session(), delay=0)

def test_fetch_respects_robots_disallow():
    with pytest.raises(ScrapeError): fetch_deals(session=fake_pages(total=50, robots='Disallow: /'), delay=0)
```

- [ ] **Step 2:** Jalankan `pytest tests/test_steam_fetch.py -v`. Diharapkan: FAIL.
- [ ] **Step 3:** Implementasikan `fetch_deals`: baca robots.txt dulu, ambil halaman demi halaman dengan jeda `delay` detik, ulangi maksimal 3 kali per halaman, berhenti di `limit` atau saat halaman habis.
- [ ] **Step 4:** Jalankan tes. Diharapkan: PASS. Commit: `feat: fetch deals with pacing and robots check`.

### Task 4: Penyimpanan snapshot

**Files:**
- Create: `store.py`, `tests/test_store.py`

**Interfaces:**
- Consumes: `Deal`.
- Produces: `save_snapshot(deals: list[Deal], run_at: datetime, root: Path = Path('data')) -> Path` (berkas `snapshots/YYYY-MM-DDTHHMMSSZ.csv`, sekaligus menulis ulang `all_deals.csv`); `load_all(root: Path = Path('data')) -> pd.DataFrame` dengan kolom `run_at, app_id, name, normal_price, final_price, discount_pct, url`; `latest_snapshot(root: Path = Path('data')) -> list[Deal] | None`.

- [ ] **Step 1: Tulis tes yang gagal**

```python
def test_roundtrip_keeps_tricky_names(tmp_path):
    d = Deal(1, 'Foo, "Bar" _x_ *y*', 200000, 100000, 50, 'u')
    save_snapshot([d], T1, tmp_path)
    assert latest_snapshot(tmp_path) == [d]

def test_two_runs_in_same_minute_get_distinct_files(tmp_path):
    assert save_snapshot([D], T1, tmp_path) != save_snapshot([D], T1 + timedelta(seconds=1), tmp_path)

def test_all_deals_accumulates(tmp_path):
    save_snapshot([D], T1, tmp_path); save_snapshot([D], T2, tmp_path)
    assert len(load_all(tmp_path)) == 2

def test_latest_snapshot_none_when_empty(tmp_path):
    assert latest_snapshot(tmp_path) is None
```

- [ ] **Step 2:** Jalankan `pytest tests/test_store.py -v`. Diharapkan: FAIL.
- [ ] **Step 3:** Implementasikan dengan pandas; `all_deals.csv` dibangun dari semua berkas snapshot.
- [ ] **Step 4:** Jalankan tes. Diharapkan: PASS. Commit: `feat: csv snapshot store`.

### Task 5: Ringkasan dan perbandingan

**Files:**
- Create: `summary.py`, `tests/test_summary.py`

**Interfaces:**
- Consumes: `Deal`.
- Produces: `tier(pct: int) -> str` (`'>=75'`, `'50-74'`, `'25-49'`, `'<25'`); `RunSummary(count: int, new: int, existing: int, ended: int, price_changed: int, tiers: dict[str, int], top_discounts: list[Deal], new_deals: list[Deal], total_rows: int, run_number: int)`; `summarize(current: list[Deal], previous: list[Deal] | None, total_rows: int, run_number: int) -> RunSummary` (`top_discounts` dan `new_deals` masing-masing maksimal 3).

- [ ] **Step 1: Tulis tes yang gagal**

```python
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
```

- [ ] **Step 2:** Jalankan `pytest tests/test_summary.py -v`. Diharapkan: FAIL.
- [ ] **Step 3:** Implementasikan; game dicocokkan lewat `app_id`; `price_changed` menghitung game yang ada di kedua pengambilan dengan `final_price` berbeda.
- [ ] **Step 4:** Jalankan tes. Diharapkan: PASS. Commit: `feat: run summary and diff`.

### Task 6: Pesan Telegram

**Files:**
- Create: `notify.py`, `tests/test_notify.py`

**Interfaces:**
- Consumes: `RunSummary`.
- Produces: `build_message(s: RunSummary, run_at: datetime) -> str`; `build_failure_message(error: str, run_at: datetime) -> str`; `send_message(token: str, chat_id: str, text: str, session: requests.Session | None = None) -> None`; `class NotifyError(Exception)`.

- [ ] **Step 1: Tulis tes yang gagal**

```python
def test_message_has_spec_fields():
    m = build_message(SUMMARY, RUN_AT_UTC)
    for part in ('Scraping selesai', 'Data diambil : 50 game diskon', 'Per diskon', 'Total data'):
        assert part in m

def test_message_shows_time_in_wib():
    assert '07:00' in build_message(SUMMARY, datetime(2026, 11, 17, 0, 0, tzinfo=UTC))

def test_markdown_chars_stay_literal_and_under_limit():
    m = build_message(SUMMARY_WITH_NAME('A_B *C*'), RUN_AT_UTC)
    assert 'A_B *C*' in m and len(m) <= 4096

def test_send_uses_plain_text_and_raises_on_error():
    s = fake_session(status=200); send_message('T', '1', 'hi', s)
    assert s.url == 'https://api.telegram.org/botT/sendMessage' and 'parse_mode' not in s.json
    with pytest.raises(NotifyError): send_message('T', '1', 'hi', fake_session(status=400))
```

- [ ] **Step 2:** Jalankan `pytest tests/test_notify.py -v`. Diharapkan: FAIL.
- [ ] **Step 3:** Implementasikan sesuai contoh pesan di spec; waktu ditampilkan dalam `Asia/Jakarta`; tanpa `parse_mode`.
- [ ] **Step 4:** Jalankan tes. Diharapkan: PASS. Commit: `feat: telegram message builder and sender`.

### Task 7: Orkestrasi dan workflow terjadwal

**Files:**
- Create: `run.py`, `tests/test_run.py`, `.github/workflows/scrape.yml`
- Delete: `.github/workflows/probe.yml`

**Interfaces:**
- Consumes: `fetch_deals`, `latest_snapshot`, `save_snapshot`, `load_all`, `summarize`, `build_message`, `build_failure_message`, `send_message`.
- Produces: `main() -> int` (0 sukses, 1 gagal); membaca `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` dari lingkungan.

- [ ] **Step 1: Tulis tes yang gagal**

```python
def test_success_saves_one_snapshot_and_sends_one_message(env, fakes):
    assert main() == 0
    assert len(fakes.saved) == 1 and len(fakes.sent) == 1

def test_zero_deals_sends_failure_and_saves_nothing(env, fakes_empty):
    assert main() == 1
    assert fakes_empty.saved == [] and 'gagal' in fakes_empty.sent[0].lower()

def test_fewer_than_50_still_reports_actual_count(env, fakes_20):
    assert main() == 0 and 'Data diambil : 20 game diskon' in fakes_20.sent[0]
```

- [ ] **Step 2:** Jalankan `pytest tests/test_run.py -v`. Diharapkan: FAIL.
- [ ] **Step 3:** Implementasikan `main`: ambil, bandingkan dengan `latest_snapshot`, simpan, ringkas, kirim; jika `ScrapeError` atau hasil kosong, kirim pesan gagal dan kembalikan 1 tanpa menyimpan.
- [ ] **Step 4:** Tulis `scrape.yml`: `schedule` (`cron: '0 0 */3 * *'`, sama dengan 07.00 WIB; langkah hari-dalam-bulan ini mengulang tiap awal bulan, dapat diterima) dan `workflow_dispatch`; izin `contents: write`; langkah checkout, setup Python 3.12, `pip install -r requirements.txt`, `pytest`, `python run.py`, lalu commit `data/` dengan `git pull --rebase` sebelum `git push`.
- [ ] **Step 5:** Jalankan `pytest -v` (semua PASS), lalu klik Run workflow di GitHub. Diharapkan: satu pesan Telegram tiba dan satu commit data baru muncul. Commit: `feat: scheduled scrape workflow`.

### Task 8: Dashboard

**Files:**
- Create: `dashboard/views.py`, `dashboard/app.py`, `tests/test_views.py`

**Interfaces:**
- Consumes: `load_all`, `tier`.
- Produces: `filter_deals(df: pd.DataFrame, run_dates: list[str] | None, min_pct: int, max_pct: int) -> pd.DataFrame`; `changes_between(df: pd.DataFrame, run_a: str, run_b: str) -> pd.DataFrame` dengan kolom `name, status, normal_price, final_price_a, final_price_b` dan `status` salah satu dari `'baru'`, `'berakhir'`, `'harga berubah'`.

- [ ] **Step 1: Tulis tes yang gagal**

```python
def test_filter_by_date_and_discount():
    out = filter_deals(DF, ['2026-11-16'], 50, 100)
    assert set(out.run_at.str[:10]) == {'2026-11-16'} and out.discount_pct.min() >= 50

def test_changes_between_statuses():
    out = changes_between(DF, RUN_A, RUN_B)
    assert set(out.status) == {'baru', 'berakhir', 'harga berubah'}

def test_empty_data_does_not_crash():
    assert filter_deals(pd.DataFrame(columns=COLUMNS), None, 0, 100).empty
```

- [ ] **Step 2:** Jalankan `pytest tests/test_views.py -v`. Diharapkan: FAIL.
- [ ] **Step 3:** Implementasikan fungsi di `views.py`; `app.py` memuat `data/all_deals.csv` dan menampilkan empat kartu (total data, jumlah pengambilan, rata-rata diskon, diskon terbesar), filter tanggal dan rentang diskon, grafik jumlah game per rentang diskon, tabel dengan tombol unduh CSV, dan tab perubahan; data kosong menampilkan pesan informasi.
- [ ] **Step 4:** Jalankan `pytest -v` (PASS) dan `streamlit run dashboard/app.py`. Diharapkan: halaman terbuka dengan data dari pengambilan yang ada. Commit: `feat: streamlit dashboard`.
- [ ] **Step 5:** Pasang di Streamlit Community Cloud dari repositori publik. Diharapkan: tautan publik terbuka dan menampilkan data yang sama.

### Task 9: Persiapan demo

**Files:**
- Modify: `README.md`

- [ ] **Step 1:** Senin 16 November: jalankan workflow secara manual (pengambilan ke-1).
- [ ] **Step 2:** Selasa 17 November atau Rabu 18 pagi: jalankan lagi (pengambilan ke-2). Diharapkan: dua pesan Telegram, 100 baris di `all_deals.csv`, tab perubahan di dashboard tidak kosong.
- [ ] **Step 3:** Ambil tangkapan layar kedua pesan Telegram dan dashboard sebagai cadangan; tulis di README cara kerja, jadwal, dan tautan dashboard. Commit: `docs: readme and demo notes`.
