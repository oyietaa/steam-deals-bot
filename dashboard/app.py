import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from dashboard.views import changes_between, filter_deals  # noqa: E402
from store import load_all  # noqa: E402
from summary import tier  # noqa: E402

TIERS = ['>=75', '50-74', '25-49', '<25']

st.set_page_config(page_title='Pantau Diskon Steam', layout='wide')
st.title('Pantau Diskon Steam')

df = load_all(Path(os.environ.get('DEALS_DATA_DIR', ROOT / 'data')))
if df.empty:
    st.info('Belum ada data. Jalankan workflow scrape di GitHub (Actions > scrape > Run workflow).')
    st.stop()

runs = sorted(df['run_at'].unique())
dates = sorted({r[:10] for r in runs})
selected = st.sidebar.multiselect('Tanggal pengambilan', dates, default=dates)
lo, hi = st.sidebar.slider('Rentang diskon (%)', 0, 100, (0, 100))
view = filter_deals(df, selected, lo, hi)

c1, c2, c3, c4 = st.columns(4)
c1.metric('Total data', len(view))
c2.metric('Jumlah pengambilan', len(runs))
c3.metric('Rata-rata diskon', f"{view['discount_pct'].mean():.0f}%" if len(view) else '-')
c4.metric('Diskon terbesar', f"{view['discount_pct'].max()}%" if len(view) else '-')

tab_data, tab_changes = st.tabs(['Semua data', 'Perubahan'])
with tab_data:
    counts = view['discount_pct'].map(tier).value_counts().reindex(TIERS, fill_value=0)
    st.bar_chart(counts)
    st.dataframe(view, use_container_width=True)
    st.download_button('Unduh CSV', view.to_csv(index=False), file_name='diskon_steam.csv', mime='text/csv')
with tab_changes:
    if len(runs) < 2:
        st.info('Perubahan baru terlihat setelah ada minimal 2 pengambilan.')
    else:
        a = st.selectbox('Pengambilan awal', runs, index=len(runs) - 2)
        b = st.selectbox('Pengambilan akhir', runs, index=len(runs) - 1)
        st.dataframe(changes_between(df, a, b), use_container_width=True)
