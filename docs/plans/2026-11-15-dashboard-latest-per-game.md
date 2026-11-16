# Dashboard: Satu Baris per Game Implementation Plan

> **Untuk pelaksana:** gunakan superpowers:executing-plans (tidak ada alat subagen). Langkah memakai kotak centang.

**Goal:** Dashboard menampilkan tiap game sekali (kondisi terbarunya) walau data CSV bertambah dobel tiap pengambilan.

**Architecture:** Penyimpanan tidak berubah. Satu fungsi murni `latest_per_game` meringkas `all_deals.csv` menjadi satu baris per `app_id`; `app.py` memakainya untuk kartu, grafik, tabel, dan unduhan.

**Tech Stack:** Python 3.12, pandas, pytest, streamlit.

**Spec:** Pilihan pengguna 15 November 2026: alternatif kecil (tampilan satu baris per game, tanpa mengubah penyimpanan).

## Global Constraints

- Penyimpanan, scraper, notifikasi, dan workflow tidak berubah.
- Tab Perubahan (`changes_between`) tidak berubah.
- Filter tanggal dan rentang diskon tetap ada.

## Review Focus

1. Game yang muncul di banyak pengambilan hanya tampil sekali, dengan baris pengambilan terbaru.
2. Game yang tidak ada di pengambilan terakhir ditandai tidak aktif (`aktif` salah), termasuk saat filter tanggal aktif.
3. Data kosong tidak membuat dashboard error.

### Task 1: latest_per_game dan dashboard

**Files:**
- Modify: `dashboard/views.py`, `dashboard/app.py`, `tests/test_views.py`, `tests/test_app_smoke.py`, `README.md`

**Interfaces:**
- Produces: `latest_per_game(df: pd.DataFrame, latest_run: str | None = None) -> pd.DataFrame` dengan kolom `name, discount_pct, final_price, normal_price, pertama_terlihat, terakhir_terlihat, aktif, url`, satu baris per `app_id` (baris `run_at` terbaru), diurutkan diskon terbesar; `aktif` benar bila `terakhir_terlihat == latest_run` (default: `run_at` terbesar di `df`).

- [ ] **Step 1: Tulis tes yang gagal**

```python
def test_latest_per_game_one_row_per_game():
    assert len(latest_per_game(DF)) == 4
def test_latest_per_game_uses_latest_row():
    g = latest_per_game(DF).set_index('name').loc['Game 3']
    assert (g.final_price, g.discount_pct) == (45000, 55)
def test_latest_per_game_marks_active_and_first_last_seen():
    out = latest_per_game(DF).set_index('name')
    assert not out.loc['Game 1', 'aktif'] and out.loc['Game 4', 'aktif']
    assert (out.loc['Game 2', 'pertama_terlihat'], out.loc['Game 2', 'terakhir_terlihat']) == (RUN_A, RUN_B)
def test_latest_per_game_uses_given_latest_run():
    only_a = DF[DF.run_at == RUN_A]
    assert not latest_per_game(only_a, RUN_B).aktif.any()
def test_latest_per_game_empty():
    assert latest_per_game(pd.DataFrame(columns=COLUMNS)).empty
```

- [ ] **Step 2:** Jalankan `pytest tests/test_views.py -v`. Diharapkan: FAIL.
- [ ] **Step 3:** Implementasikan `latest_per_game`; ubah `app.py` (`view = latest_per_game(filter_deals(...), runs[-1])`, kartu pertama bernama `Jumlah game`); ubah tes smoke (`Jumlah game` bernilai `50`, tabel `Semua data` 50 baris); perbarui README.
- [ ] **Step 4:** Jalankan `pytest -q`. Diharapkan: semua PASS. Commit: `feat: dashboard shows one row per game`.
