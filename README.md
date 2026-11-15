# steam-deals-bot

Bot yang mengambil 50 game diskon Steam (harga Rupiah) dengan GitHub Actions, mengirim ringkasan ke Telegram, dan menampilkan semua data di dashboard Streamlit.

Rencana: `docs/plans/2026-11-15-steam-deals-bot.md`.

## Cara kerja
1. Workflow `scrape` (`.github/workflows/scrape.yml`) jalan terjadwal (cron `0 0 */3 * *`, 07.00 WIB) atau lewat tombol **Run workflow**.
2. `run.py` mengambil data, membandingkannya dengan pengambilan sebelumnya, menyimpan CSV di `data/snapshots/` dan `data/all_deals.csv`, lalu mengirim pesan ke Telegram.
3. Dashboard (`dashboard/app.py`) membaca `data/all_deals.csv`.

Catatan jadwal: cron `*/3` pada hari-dalam-bulan jatuh di tanggal 1, 4, 7, ..., 16, 19, ... tiap bulan. Untuk November 2026 jadwal otomatis berikutnya adalah 16 dan 19 November; pengambilan tambahan untuk demo dilakukan dengan **Run workflow**.

## Pengaturan awal (dilakukan pemilik)
1. Buat bot lewat BotFather, ambil chat ID, simpan secrets `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` di Settings > Secrets and variables > Actions.
2. Jalankan workflow `scrape` sekali dari tab Actions. Pesan Telegram harus tiba dan commit data baru muncul.
3. Fixture tes `tests/fixtures/steam_search_id.json` adalah respons ASLI Steam (diambil 15 November 2026). Kalau Steam mengubah format halamannya, bot akan mengirim pesan "format tidak dikenali" dan `scraper/steam.py` perlu disesuaikan.
4. Pasang dashboard di Streamlit Community Cloud: repositori ini, file utama `dashboard/app.py`.

## Menjalankan lokal
```
pip install -r requirements.txt
python -m pytest -q
streamlit run dashboard/app.py
```

## Demo (Rabu 18 November 2026)
- Senin 16 November: pengambilan ke-1 (otomatis atau Run workflow).
- Selasa 17 atau Rabu 18 pagi: pengambilan ke-2 lewat Run workflow, supaya tab **Perubahan** di dashboard terisi.
- Simpan tangkapan layar pesan Telegram dan dashboard sebagai cadangan.
