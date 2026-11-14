# steam-deals-bot

Bot yang tiap 3 hari mengambil 50 game diskon Steam (GitHub Actions), mengirim ringkasan ke Telegram, dan menampilkan semua data di dashboard Streamlit.

Rencana: `docs/plans/2026-11-15-steam-deals-bot.md`.

## Langkah yang harus dilakukan pemilik (Task 1)
1. Buat bot lewat BotFather, ambil chat ID, simpan secrets `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` di Settings > Secrets > Actions.
2. Jalankan workflow `probe` (Actions > probe > Run workflow). Harus muncul pesan uji di Telegram.
3. Unduh artifact `steam-probe` dan ganti `tests/fixtures/steam_search_id.json` dengan respons nyata (fixture bawaan SINTETIS).
