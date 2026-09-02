import re
from datetime import datetime
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# CONFIG DATABASE PERMANEN
# ==============================================================================
URL_SHEET_DEFAULT = 'https://docs.google.com/spreadsheets/d/1dhbkNELRxIa9HAexkpT13t2cbg3sqdRp5yBr7af9bcw/edit?usp=sharing'
WEBHOOK_URL_DEFAULT = 'https://script.google.com/macros/s/AKfycbzVQGbtdyZwB93hzfJdpAGYAD09r-q2yL4L7u2DBWein3N5wH5qI9R2QY5apPoLeKkh/exec'
# ==============================================================================

st.set_page_config(
    page_title='E-Katalog Budgeting & Admin Portal', layout='wide'
)

# STYLING GLOBAL, FIX DARK MODE FONT, & CLEANUP UI
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    html, body, [class*="css"]:not(button):not(i):not([class*="icon"]) {
        font-family: 'Roboto', sans-serif;
    }

    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, label, div, td, th {
        color: #f8fafc !important;
    }

    /* Fix Kontras Font Tabel Data Editor di Dark Mode */
    div[data-testid="stDataFrame"] *, 
    div[data-baseweb="table"] *, 
    div[role="grid"] * {
        color: #f8fafc !important;
        background-color: transparent !important;
    }

    /* Sembunyikan Tulisan 'keyboard double arrow right' Pada Tabel */
    [aria-label*="keyboard double arrow right"],
    [data-testid="stDataEditor"] span:contains("keyboard double arrow right") {
        display: none !important;
    }

    /* Styling Input Text & Password */
    div[data-baseweb="input"] > div, input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 8px !important;
    }

    /* FIX ICON EYE (VISIBILITY) PASSWORDS */
    button[aria-label*="password"], 
    button[aria-label*="Password"],
    button[aria-label*="Show"],
    button[aria-label*="Hide"] {
        color: #94a3b8 !important;
    }

    button[aria-label*="password"] *, 
    button[aria-label*="Password"] *,
    button[aria-label*="Show"] *,
    button[aria-label*="Hide"] * {
        font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
        font-size: 1.2rem !important;
    }

    .stButton>button { 
        background-color: #2563eb !important; 
        color: #ffffff !important; 
        border-radius: 8px !important; 
        font-weight: 700 !important; 
        font-size: 13px !important;
        width: 100% !important; 
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
    
    section[data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 1px solid #334155 !important;
    }

    .cart-summary-box {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #334155;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

ROLE_DB = {
    'Teknisi': 'tek2026',
    'Cleaning Service': 'cs2026',
    'Gardener': 'gar2026',
    'Security': 'sec2026',
    'Proyek Pengadaan': 'pengadaan2026',
    'Proyek Perbaikan': 'perbaikan2026',
    'Boarding House': 'boarding2026',
    'Admin': 'admin2026',
}

# --- INIT STATE MANAGEMENT ---
if 'logged_in' not in st.session_state:
  st.session_state.logged_in = False
if 'role' not in st.session_state:
  st.session_state.role = ''
if 'keranjang' not in st.session_state:
  st.session_state.keranjang = []
if 'db_pengajuan_admin' not in st.session_state:
  st.session_state.db_pengajuan_admin = []


def get_csv_url(url, sheet_name='DataBarang'):
  match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
  if match:
    sheet_id = match.group(1)
    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
  return url


# ==========================================
# 1. HALAMAN LOGIN
# ==========================================
if not st.session_state.logged_in:
  st.title('🔑 Portal Login Budgeting')
  st.write('Silakan pilih departemen dan masukkan password:')

  role_pilihan = st.selectbox('Pilih Akses / Departemen:', list(ROLE_DB.keys()))
  password_input = st.text_input('Kata Sandi (Password):', type='password')

  if st.button('Masuk ke Aplikasi'):
    if password_input == ROLE_DB[role_pilihan]:
      st.session_state.logged_in = True
      st.session_state.role = role_pilihan
      st.rerun()
    else:
      st.error('❌ Kata sandi salah!')

# ==========================================
# 2. PANEL ADMIN (VERIFIKASI & EDIT & CETAK)
# ==========================================
elif st.session_state.role == 'Admin':
  periode_sekarang = datetime.now().strftime('%B %Y')

  with st.sidebar:
    st.header('👤 Panel Admin')
    st.write(f'📅 Periode Aktif: **{periode_sekarang}**')
    if st.button('Keluar (Logout)'):
      st.session_state.logged_in = False
      st.session_state.role = ''
      st.rerun()

    st.markdown('---')
    st.header('⚙️ Database')
    url_sheet = st.text_input(
        'Link Google Sheet Utama:', value=URL_SHEET_DEFAULT
    )

  st.title('🛡️ Admin Portal — Verifikasi & Cetak Proposal')

  if st.session_state.db_pengajuan_admin:
    df_admin = pd.DataFrame(st.session_state.db_pengajuan_admin)

    # 1. FILTER PERIODE & DEPARTEMEN
    col_f1, col_f2 = st.columns(2)
    with col_f1:
      daftar_periode = list(df_admin['periode'].unique())
      pilihan_periode = st.selectbox(
          '📅 Pilih Periode Anggaran:', options=daftar_periode
      )

    with col_f2:
      daftar_dept = ['Semua Departemen'] + list(df_admin['departemen'].unique())
      pilihan_dept = st.selectbox('🏢 Filter Departemen:', options=daftar_dept)

    filtered_admin_df = df_admin[
        df_admin['periode'] == pilihan_periode
    ].copy()
    if pilihan_dept != 'Semua Departemen':
      filtered_admin_df = filtered_admin_df[
          filtered_admin_df['departemen'] == pilihan_dept
      ]

    st.subheader('📝 Verifikasi & Edit Data Pengajuan Staff')
    st.caption(
        'Admin dapat mengubah Qty/Harga, menghapus item, atau menambah item'
        ' baru.'
    )

    if pilihan_dept == 'Semua Departemen':
      depts_to_show = list(filtered_admin_df['departemen'].unique())
    else:
      depts_to_show = [pilihan_dept]

    edited_dept_dfs = []

    # 2. TABEL INTERAKTIF DIPISAH PER DEPARTEMEN
    with st.form('admin_edit_form'):
      for dept_name in depts_to_show:
        dept_df = filtered_admin_df[
            filtered_admin_df['departemen'] == dept_name
        ].copy()
        if dept_df.empty:
          continue

        dept_df['Hapus'] = False
        cols_to_show = [
            'Hapus',
            'periode',
            'nama_barang',
            'satuan',
            'harga',
            'qty',
            'subtotal',
        ]

        st.markdown(f'### 🏢 Departemen: **{dept_name}**')

        edited_d_df = st.data_editor(
            dept_df[cols_to_show],
            column_config={
                'Hapus': st.column_config.CheckboxColumn(
                    '🗑️ Hapus', default=False
                ),
                'periode': st.column_config.TextColumn('Periode'),
                'nama_barang': st.column_config.TextColumn('Nama Barang'),
                'satuan': st.column_config.TextColumn('Satuan'),
                'harga': st.column_config.NumberColumn(
                    'Harga (Rp)', format="Rp %'d"
                ),
                'qty': st.column_config.NumberColumn(
                    'Qty', min_value=1, step=1
                ),
                'subtotal': st.column_config.NumberColumn(
                    'Subtotal (Rp)', format="Rp %'d", disabled=True
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows='dynamic',
            key=f'admin_editor_{dept_name}',
        )

        edited_d_df['departemen'] = dept_name
        edited_dept_dfs.append(edited_d_df)
        st.markdown('<br>', unsafe_allow_html=True)

      submit_admin = st.form_submit_button(
          '💾 Simpan Perubahan Admin', type='primary'
      )

    if edited_dept_dfs:
      combined_admin_df = pd.concat(edited_dept_dfs, ignore_index=True)
    else:
      combined_admin_df = pd.DataFrame(
          columns=[
              'departemen',
              'periode',
              'nama_barang',
              'satuan',
              'harga',
              'qty',
              'subtotal',
              'Hapus',
          ]
      )

    combined_admin_df['harga'] = (
        pd.to_numeric(combined_admin_df['harga'], errors='coerce').fillna(0)
    )
    combined_admin_df['qty'] = (
        pd.to_numeric(combined_admin_df['qty'], errors='coerce').fillna(1)
    )
    combined_admin_df['subtotal'] = (
        combined_admin_df['harga'] * combined_admin_df['qty']
    )

    if submit_admin:
      clean_updated_df = combined_admin_df[
          combined_admin_df['Hapus'] == False
      ].drop(columns=['Hapus'])

      other_periods = [
          x
          for x in st.session_state.db_pengajuan_admin
          if x.get('periode') != pilihan_periode
      ]

      if pilihan_dept != 'Semua Departemen':
        other_depts_current_period = [
            x
            for x in st.session_state.db_pengajuan_admin
            if x.get('periode') == pilihan_periode
            and x.get('departemen') != pilihan_dept
        ]
        st.session_state.db_pengajuan_admin = (
            other_periods
            + other_depts_current_period
            + clean_updated_df.to_dict('records')
        )
      else:
        st.session_state.db_pengajuan_admin = (
            other_periods + clean_updated_df.to_dict('records')
        )

      st.toast('✅ Perubahan database berhasil disimpan!', icon='💾')
      st.rerun()

    total_nominal_admin = combined_admin_df['subtotal'].sum()
    st.markdown(
        f"""
            <div class="cart-summary-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 15px; font-weight: bold; color: #ffffff;">TOTAL ANGGARAN VERIFIKASI ADMIN ({pilihan_periode}):</span>
                    <span style="font-size: 18px; font-weight: bold; color: #34d399;">Rp {total_nominal_admin:,.0f}</span>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. CETAK DOKUMEN PROPOSAL & PREVIEW (BISA DICETAK BERULANG-ULANG)
    st.markdown('---')
    st.subheader
