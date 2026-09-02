import streamlit as st
import pandas as pd
from datetime import datetime
import re
import requests
import json

# ==============================================================================
# CONFIG DATABASE PERMANEN
# ==============================================================================
URL_SHEET_DEFAULT = "https://docs.google.com/spreadsheets/d/1dhbkNELRxIa9HAexkpT13t2cbg3sqdRp5yBr7af9bcw/edit?usp=sharing"
WEBHOOK_URL_DEFAULT = "https://script.google.com/macros/s/AKfycbzVQGbtdyZwB93hzfJdpAGYAD09r-q2yL4L7u2DBWein3N5wH5qI9R2QY5apPoLeKkh/exec"
# ==============================================================================

st.set_page_config(page_title="E-Katalog Budgeting & Admin Portal", layout="wide")

# CUSTOM CSS UNTUK TEMA DARK ELEGANT & KONTRASTING TEXT
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif !important;
    }

    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, label, div, td, th {
        color: #f8fafc !important;
    }

    /* Input Styling */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div, 
    input, 
    textarea {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }

    input {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* Instant Search Live Box */
    .search-container {
        margin-bottom: 15px;
    }
    .live-search-input {
        width: 100%;
        padding: 12px 16px;
        background-color: #1e293b;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        color: #ffffff;
        font-size: 15px;
        outline: none;
    }
    .live-search-input:focus {
        border-color: #60a5fa;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4);
    }

    /* Kartu Barang Live Filter */
    .item-card-row {
        background-color: #1e293b;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        border: 1px solid #334155;
        margin-bottom: 8px;
    }
    .item-name-title {
        font-size: 15px;
        font-weight: 700;
        color: #60a5fa;
    }
    .item-price-tag {
        font-size: 14px;
        font-weight: 700;
        color: #34d399;
    }

    /* Buttons */
    .stButton>button { 
        background-color: #2563eb !important; 
        color: #ffffff !important; 
        border-radius: 8px !important; 
        font-weight: 700 !important; 
        font-size: 14px !important;
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
    </style>
""", unsafe_allow_html=True)

# Database Password Role
ROLE_DB = {
    "Teknisi": "tek2026",
    "Cleaning Service": "cs2026",
    "Gardener": "gar2026",
    "Security": "sec2026",
    "Proyek Pengadaan": "pengadaan2026",
    "Proyek Perbaikan": "perbaikan2026",
    "Boarding House": "boarding2026",
    "Admin": "admin2026"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = ""
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

def get_csv_url(url, sheet_name="DataBarang"):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        sheet_id = match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return url

# ==========================================
# 1. LANDING PAGE & LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.title("🔑 Portal Login Budgeting")
    st.write("Silakan pilih departemen dan masukkan password:")
    
    role_pilihan = st.selectbox("Pilih Akses / Departemen:", list(ROLE_DB.keys()))
    password_input = st.text_input("Kata Sandi (Password):", type="password")
    
    if st.button("Masuk ke Aplikasi"):
        if password_input == ROLE_DB[role_pilihan]:
            st.session_state.logged_in = True
            st.session_state.role = role_pilihan
            st.rerun()
        else:
            st.error("❌ Kata sandi salah!")

# ==========================================
# 2. HALAMAN KHUSUS ADMIN
# ==========================================
elif st.session_state.role == "Admin":
    periode_sekarang = datetime.now().strftime("%B %Y")
    
    with st.sidebar:
        st.header("👤 Panel Admin")
        st.write(f"📅 Periode: **{periode_sekarang}**")
        if st.button("Keluar (Logout)"):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.rerun()
            
        st.markdown("---")
        st.header("⚙️ Database")
        url_sheet = st.text_input("Link Google Sheet Utama:", value=URL_SHEET_DEFAULT)

    st.title("🖨️ Panel Cetak Proposal Anggaran Admin")
    st.info("Fitur cetak proposal admin dapat diakses di halaman ini.")

# ==========================================
# 3. HALAMAN UTAMA STAFF (REAL-TIME LIVE FILTER)
# ==========================================
else:
    periode_sekarang = datetime.now().strftime("%B%Y")
    
    with st.sidebar:
        st.header(f"👤 {st.session_state.role}")
        st.write(f"📅 Periode: **{datetime.now().strftime('%B %Y')}**")
        
        if st.button("Keluar (Logout)"):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.session_state.keranjang = []
            st.rerun()
            
        st.markdown("---")
        st.header("⚙️ Database")
        url_sheet = st.text_input("Link Google Sheet Utama:", value=URL_SHEET_DEFAULT)
        webhook_url = st.text_input("URL Web App Google Script:", value=WEBHOOK_URL_DEFAULT)

    st.title(f"📦 Katalog Barang — {st.session_state.role}")
    
    if url_sheet and "http" in url_sheet:
        try:
            csv_url = get_csv_url(url_sheet, "DataBarang")
            df_barang = pd.read_csv(csv_url)
            df_barang.columns = df_barang.columns.str.strip()

            # PERSIAPAN DATA JS UNTUK LIVE SEARCH VANILLA JS (REAL TIME INSTANT FILTER)
            barang_list = []
            for idx, row in df_barang.iterrows():
                nama = str(row['Nama Barang'])
                satuan = str(row['Satuan'])
                harga = row['Harga']
                harga_clean = float(re.sub(r'[^0-9]', '', str(harga))) if pd.notnull(harga) else 0
                barang_list.append({
                    "id": idx,
                    "nama": nama,
                    "satuan": satuan,
                    "harga": harga_clean
                })

            json_barang = json.dumps(barang_list)

            # SCRIPT INSTANT LIVE SEARCH (FILTER ON TYPE REAL-TIME TANPA TEKAN ENTER)
            live_search_html = f"""
            <div style="margin-bottom: 15px;">
                <label style="color: #94a3b8; font-size: 13px; font-weight: 500; display: block; margin-bottom: 5px;">
                    🔍 Ketik Nama Barang (Instant Filter per huruf):
                </label>
                <input type="text" id="searchInput" oninput="filterBarang()" placeholder="Ketik nama barang... (cth: ac, semen, lampu)" class="live-search-input" autofocus />
            </div>

            <div id="barangContainer"></div>

            <script>
                const dataBarang = {json_barang};

                function filterBarang() {{
                    const query = document.getElementById('searchInput').value.toLowerCase().trim();
                    const container = document.getElementById('barangContainer');
                    container.innerHTML = '';

                    const filtered = dataBarang.filter(item => 
                        item.nama.toLowerCase().includes(query)
                    );

                    if (filtered.length === 0) {{
                        container.innerHTML = '<div style="color: #ef4444; padding: 10px;">Barang tidak ditemukan...</div>';
                        return;
                    }}

                    // Tampilkan maksimal 20 item agar ringan saat di-scroll
                    const itemsToDisplay = filtered.slice(0, 20);

                    itemsToDisplay.forEach(item => {{
                        const formattedPrice = new Intl.NumberFormat('id-ID', {{ style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }}).format(item.harga);
                        
                        const itemHtml = `
                            <div class="item-card-row" style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 10px; border-left: 4px solid #3b82f6;">
                                <div style="font-weight: bold; color: #60a5fa; font-size: 15px;">📌 ${{item.nama}}</div>
                                <div style="color: #34d399; font-weight: bold; font-size: 14px; margin-top: 2px;">
                                    ${{formattedPrice}} <span style="color: #94a3b8; font-weight: normal; font-size: 12px;">/ ${{item.satuan}}</span>
                                </div>
                            </div>
                        `;
                        container.innerHTML += itemHtml;
                    }});
                }}

                // Jalankan filter awal
                filterBarang();
            </script>
            """
            
            # Render HTML Filter Instant
            st.components.v1.html(live_search_html, height=480, scrolling=True)

            # INPUT BARANG TERPILIH UNTUK MASUK KE Google Sheet / KERANJANG
            st.markdown("---")
            st.subheader("➕ Tambah Barang ke Pengajuan")
            
            pilihan_nama = st.selectbox("Pilih Barang dari Daftar Terfilter:", ["-- Pilih Barang --"] + list(df_barang['Nama Barang'].dropna().unique()))
            
            if pilihan_nama != "-- Pilih Barang --":
                row_sel = df_barang[df_barang['Nama Barang'] == pilihan_nama].iloc[0]
                nama_sel = str(row_sel['Nama Barang'])
                satuan_sel = str(row_sel['Satuan'])
                harga_sel = float(re.sub(r'[^0-9]', '', str(row_sel['Harga']))) if pd.notnull(row_sel['Harga']) else 0

                c1, c2 = st.columns([1, 1])
                with c1:
                    qty_input = st.number_input("Jumlah (Qty):", min_value=1, value=1, step=1)
                with c2:
                    st.write("")
                    st.write("")
                    if st.button("➕ Tambah"):
                        subtotal_calc = harga_sel * qty_input
                        dept_code = st.session_state.role.replace(" ", "")
                        
                        payload = {
                            "departemen": dept_code,
                            "periode": periode_sekarang,
                            "nama_barang": nama_sel,
                            "satuan": satuan_sel,
                            "harga": harga_sel,
                            "qty": qty_input,
                            "subtotal": subtotal_calc
                        }
                        
                        if webhook_url and "http" in webhook_url:
                            res = requests.post(webhook_url, json=payload)
                            if res.status_code == 200:
                                st.success(f"✅ {nama_sel} ({qty_input} {satuan_sel}) ditambahkan!")
                            else:
                                st.error("Gagal mengirim ke Google Sheet.")
                        
                        st.session_state.keranjang.append(payload)

            # TABEL KERANJANG BELANJA
            if st.session_state.keranjang:
                st.markdown("---")
                st.subheader("🛒 Pesanan Tersimpan Periode Ini")
                df_cart = pd.DataFrame(st.session_state.keranjang)
                st.dataframe(df_cart[['nama_barang', 'qty', 'satuan', 'subtotal']], use_container_width=True)

        except Exception as e:
            st.error(f"Gagal membaca database. Error: {e}")
    else:
        st.info("👈 Silakan atur link Google Sheet terlebih dahulu.")
