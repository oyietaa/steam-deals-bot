# Steam Deals Bot

Bot yang secara otomatis mengambil **50 game diskon dari Steam** (harga dalam Rupiah) tiap 3 hari, mengirim ringkasannya ke **Telegram**, dan menampilkan semua data yang terkumpul di **dashboard Streamlit**. Seluruh proses berjalan di GitHub Actions, jadi tidak perlu laptop yang menyala.

> **Dashboard:** https://diskon-steam.streamlit.app/

## Fitur

- Scraping terjadwal otomatis (tiap 3 hari) dan bisa dijalankan manual lewat tombol **Run workflow**.
- Notifikasi Telegram setelah tiap pengambilan: berapa game diambil, mana yang baru, yang berakhir, dan yang harganya berubah.
- Riwayat disimpan sebagai berkas CSV di repositori, satu berkas per pengambilan.
- Dashboard: kartu ringkasan, filter, grafik, tabel yang bisa diunduh, dan perbandingan dua pengambilan.
- Jika scraping gagal, bot mengirim pesan `Scraping gagal` beserta alasannya, dan tidak ada data yang disimpan.

## Cara kerja

```
Jadwal GitHub Actions (atau tombol Run workflow)
   -> run.py mengambil 50 game diskon dari Steam
   -> dibandingkan dengan pengambilan sebelumnya
   -> disimpan ke data/snapshots/*.csv dan data/all_deals.csv
   -> ringkasan dikirim ke Telegram
Dashboard Streamlit membaca data/all_deals.csv dari repositori
```

Bagian jaringan (`fetch_deals`) dipisah dari bagian logika murni (parse, perbandingan, penyusunan pesan), sehingga logikanya bisa dites tanpa internet.

## Sumber data dan etika scraping

- Data diambil dari halaman pencarian publik toko Steam (`store.steampowered.com/search/results/`) dengan filter diskon (`specials=1`) dan kode negara Indonesia (`cc=id`).
- Bot membaca `robots.txt` lebih dulu dan berhenti bila pengambilan dilarang.
- Ada jeda antar-request, percobaan ulang maksimal 3 kali, dan User-Agent yang jujur (`steam-deals-bot/0.1 (student project)`).
- Volume sangat kecil: 50 game tiap 3 hari.
- Endpoint ini **tidak didokumentasikan resmi** oleh Steam dan formatnya bisa berubah. Jika itu terjadi, bot mengirim pesan `format tidak dikenali` dan `scraper/steam.py` perlu disesuaikan.

## Contoh pesan Telegram

```
Scraping selesai (Sel, 17 Nov, 07:00)
Data diambil : 50 game diskon
Baru / sudah ada : 17 / 33
Per diskon   : >=75%: 7 | 50-74%: 14 | 25-49%: 8 | <25%: 21
Berakhir / harga berubah : 10 / 2
Diskon terbesar:
- Euro Truck Simulator 2 (-75%) Rp 46.499 dari Rp 185.999
...
Game baru:
- ...
Total data   : 97 (pengambilan ke-2)
```

Teks di atas hanya contoh; angka dan nama game berbeda tiap pengambilan.

## Dashboard

- **Kartu:** Jumlah game, Jumlah pengambilan, Rata-rata diskon, Diskon terbesar.
- **Sidebar:** filter tanggal pengambilan dan rentang diskon.
- **Tab "Semua data":** tiap game ditampilkan sekali dengan kondisi terbarunya (kolom `pertama_terlihat`, `terakhir_terlihat`, dan `aktif`), grafik jumlah game per rentang diskon, dan tombol unduh CSV.
- **Tab "Perubahan":** bandingkan dua pengambilan untuk melihat game baru, game yang berakhir, dan harga yang berubah.

## Data

- `data/snapshots/<waktu>.csv`: isi satu pengambilan.
- `data/all_deals.csv`: gabungan semua pengambilan (satu baris per game per pengambilan, jadi riwayat harga tetap ada).
- Kolom: `run_at`, `app_id`, `name`, `normal_price`, `final_price`, `discount_pct`, `url`. Harga dalam Rupiah utuh.
- Dashboard meringkas `all_deals.csv` menjadi satu baris per game, jadi game yang muncul berulang tidak tampil dobel.

## Jadwal

Workflow `scrape` berjalan dengan cron `0 0 */3 * *`, yaitu pukul 07.00 WIB pada tanggal 1, 4, 7, 10, ... tiap bulan. Ini bukan "tepat 3 hari setelah pengambilan terakhir", dan GitHub kadang terlambat menjalankan jadwal. Untuk pengambilan di luar jadwal, buka **Actions → scrape → Run workflow**.

## Menjalankan sendiri

1. Fork atau clone repositori ini (repositori publik agar Actions gratis).
2. Buat bot lewat BotFather di Telegram, lalu ambil token dan chat ID (kirim pesan ke bot, buka `https://api.telegram.org/bot<TOKEN>/getUpdates`, cari `chat.id`).
3. Di GitHub: **Settings → Secrets and variables → Actions → New repository secret**, buat:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Jalankan **Actions → scrape → Run workflow**. Pesan Telegram harus tiba dan commit data baru muncul. Jika perlu, aktifkan **Settings → Actions → General → Workflow permissions → Read and write**.
5. Pasang dashboard di Streamlit Community Cloud: pilih repositori ini, branch `main`, file utama `dashboard/app.py`.

### Lokal

```
pip install -r requirements.txt
python -m pytest -q
streamlit run dashboard/app.py
```

Untuk menjalankan scraping dari komputer sendiri, isi variabel lingkungan `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID`, lalu jalankan `python run.py`. Dashboard membaca folder `data/` secara bawaan; lokasi lain bisa ditentukan lewat `DEALS_DATA_DIR`.

## Struktur proyek

```
.github/workflows/scrape.yml   jadwal dan tombol Run workflow
scraper/models.py              dataclass Deal
scraper/steam.py               parser dan pengambilan data dari Steam
store.py                       simpan dan muat snapshot CSV
summary.py                     perbandingan antar-pengambilan dan ringkasan
notify.py                      penyusunan dan pengiriman pesan Telegram
run.py                         alur satu pengambilan
dashboard/views.py             fungsi data untuk dashboard
dashboard/app.py               tampilan Streamlit
tests/                         tes otomatis dan fixture respons asli Steam
docs/plans/                    rencana pengerjaan
```

## Pengujian

Semua tes berjalan tanpa internet (`python -m pytest -q`). Parser dites terhadap respons asli Steam yang disimpan di `tests/fixtures/steam_search_id.json`. Workflow juga menjalankan tes sebelum scraping.

## Batasan

- Bot hanya **mengirim notifikasi**; belum ada perintah interaktif seperti `/cari`.
- Endpoint Steam tidak resmi, sehingga bisa berubah tanpa pemberitahuan.
- `all_deals.csv` terus bertambah tiap pengambilan karena menyimpan riwayat lengkap.
- Angka `Total data` di pesan Telegram menghitung semua baris di `all_deals.csv`, bukan jumlah game unik.

## Teknologi

Python 3.12, requests, pandas, pytest, Streamlit, GitHub Actions, Telegram Bot API.
