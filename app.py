import streamlit as st
import pandas as pd
from datetime import datetime
import re
import requests

# ==============================================================================
# CONFIG DATABASE PERMANEN
# ==============================================================================
URL_SHEET_DEFAULT = "https://docs.google.com/spreadsheets/d/1dhbkNELRxIa9HAexkpT13t2cbg3sqdRp5yBr7af9bcw/edit?usp=sharing"
WEBHOOK_URL_DEFAULT = "https://script.google.com/macros/s/AKfycbzVQGbtdyZwB93hzfJdpAGYAD09r-q2yL4L7u2DBWein3N5wH5qI9R2QY5apPoLeKkh/exec"
# ==============================================================================

# Konfigurasi Halaman
st.set_page_config(page_title="E-Katalog Budgeting & Admin Portal", layout="wide")

# CSS KONTRASTING & MOBILE FRIENDLY (FIX DARK DROPDOWN & INPUTS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* Terapkan Font Utama */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif !important;
    }

    /* Paksa background halaman netral terang */
    .stApp {
        background-color: #0f172a !important; /* Tema Gelap Elegan Default */
        color: #f8fafc !important;
    }

    /* SEMUA TEKS DAN LABEL DIPAKSA KONTRAS TERANG */
    h1, h2, h3, h4, h5, h6, p, span, label, div, td, th {
        color: #f8fafc !important;
    }

    /* STYLING INPUT BOX & DROPDOWN (PASTE / KETIK / PILIH) */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div, 
    input, 
    textarea {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }

    /* PAKSA WARNA TEKS DALAM INPUT AGAR TETAP TERANG TERLIHAT */
    input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
    }

    /* STYLING POPUP DROPDOWN (SAAT DIKLIK) */
    div[data-baseweb="popover"], 
    div[data-baseweb="menu"], 
    ul[role="listbox"],
    li[role="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    /* Highlight saat item dropdown di-hover / dipilih */
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }

    /* Styling Teks Dropdown yang Terpilih */
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }

    /* BUTTON UTAMA */
    .stButton>button { 
        background-color: #2563eb !important; 
        color: #ffffff !important; 
        border-radius: 8px !important; 
        font-weight: 700 !important; 
        font-size: 15px !important;
        width: 100% !important; 
        height: 45px !important; 
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { 
        background-color: #1e293b !important; 
        border-right: 1px solid #334155 !important;
    }
    
    /* KARTU BARANG (STYLE WA WEB SEARCH RESULT) */
    .wa-card {
        background-color: #1e293b !important;
        padding: 14px 18px !important;
        border-radius: 10px !important;
        border-left: 5px solid #3b82f6 !important;
        border: 1px solid #334155 !important;
        margin-bottom: 12px !important;
    }
    .wa-title { 
        font-size: 16px !important; 
        font-weight: 700 !important; 
        color: #60a5fa !important; 
    }
    .wa-price { 
        font-size: 15px !important; 
        color: #34d399 !important; 
        font-weight: 700 !important; 
        margin-top: 2px !important; 
    }
    .wa-unit { 
        font-size: 13px !important; 
        color: #94a3b8 !important; 
    }

    /* PRINT LAYOUT FOR ADMIN */
    .print-container {
        background-color: #ffffff !important;
        padding: 20px !important;
        color: #000000 !important;
        border-radius: 8px !important;
    }
    .print-container * {
        color: #000000 !important;
    }
    .summary-box {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 13px;
    }
    .summary-box th, .summary-box td {
        border: 1px solid #333333;
        padding: 8px;
        text-align: left;
    }
    .summary-box th { background-color: #f1f5f9; font-weight: 700; }
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
    st.caption("Silakan pilih departemen dan masukkan password untuk melanjutkan.")
    
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
# 2. HALAMAN KHUSUS ADMIN (CETAK PROPOSAL)
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
    
    if url_sheet and "http" in url_sheet:
        try:
            list_dept = [
                ("Teknisi", "Teknisi"),
                ("CleaningService", "Cleaning Service"),
                ("Gardener", "Gardener"),
                ("Security", "Security"),
                ("ProyekPengadaan", "Proyek Pengadaan"),
                ("ProyekPerbaikan", "Proyek Perbaikan"),
                ("BoardingHouse", "Boarding House")
            ]
            
            dict_df = {}
            dict_budget = {}
            total_keseluruhan = 0

            for code_dept, name_dept in list_dept:
                sheet_target = f"{code_dept}_{datetime.now().strftime('%B%Y')}"
                try:
                    csv_url = get_csv_url(url_sheet, sheet_target)
                    df_temp = pd.read_csv(csv_url)
                    if not df_temp.empty:
                        dict_df[name_dept] = df_temp
                        subtotal = df_temp['Subtotal'].sum() if 'Subtotal' in df_temp.columns else 0
                        dict_budget[name_dept] = subtotal
                        total_keseluruhan += subtotal
                    else:
                        dict_budget[name_dept] = 0
                except:
                    dict_budget[name_dept] = 0

            html_header = f"""
            <div class="print-container">
                <h2 style="text-align: center; margin-bottom: 5px;">PROPOSAL PENGAJUAN ANGGARAN BUILDING MAINTENANCE</h2>
                <h3 style="text-align: center; margin-top: 0;">PERIODE: {periode_sekarang.upper()}</h3>
                <hr>
                <h4>A. RINGKASAN ANGGARAN DEPARTEMEN</h4>
                <table class="summary-box">
                    <tr>
                        <th width="8%">No</th>
                        <th>Departemen / Divisi</th>
                        <th width="35%">Jumlah Anggaran (Rupiah)</th>
                    </tr>
                    <tr><td>1</td><td>Teknisi</td><td>Rp {dict_budget.get('Teknisi', 0):,.0f}</td></tr>
                    <tr><td>2</td><td>Cleaning Service</td><td>Rp {dict_budget.get('Cleaning Service', 0):,.0f}</td></tr>
                    <tr><td>3</td><td>Gardener</td><td>Rp {dict_budget.get('Gardener', 0):,.0f}</td></tr>
                    <tr><td>4</td><td>Security</td><td>Rp {dict_budget.get('Security', 0):,.0f}</td></tr>
                    <tr><td>5</td><td>Proyek Pengadaan</td><td>Rp {dict_budget.get('Proyek Pengadaan', 0):,.0f}</td></tr>
                    <tr><td>6</td><td>Proyek Perbaikan</td><td>Rp {dict_budget.get('Proyek Perbaikan', 0):,.0f}</td></tr>
                    <tr><td>7</td><td>Boarding House</td><td>Rp {dict_budget.get('Boarding House', 0):,.0f}</td></tr>
                    <tr style="font-weight: bold; background-color: #e2e8f0;">
                        <td colspan="2" style="text-align: right;">TOTAL ESTIMASI ANGGARAN:</td>
                        <td>Rp {total_keseluruhan:,.0f}</td>
                    </tr>
                </table>
                <h4>B. RINCIAN BARANG PER DEPARTEMEN</h4>
            </div>
            """
            st.markdown(html_header, unsafe_allow_html=True)

            cols_show = ['Nama Barang', 'Satuan', 'Harga Satuan', 'Jumlah (Qty)', 'Subtotal']
            
            for idx, (code_dept, name_dept) in enumerate(list_dept, 1):
                st.markdown(f"### {idx}. Departemen {name_dept}")
                df_curr = dict_df.get(name_dept, pd.DataFrame(columns=cols_show))
                df_display = df_curr[cols_show] if all(c in df_curr.columns for c in cols_show) else df_curr
                st.dataframe(df_display, use_container_width=True)
                st.markdown(f"**Subtotal {name_dept}:** `Rp {dict_budget.get(name_dept, 0):,.0f}`")
                st.markdown("---")

            st.info("💡 Tekan **CTRL + P** untuk menyimpannya dalam format PDF.")

        except Exception as e:
            st.error(f"Gagal memuat proposal. Error: {e}")

# ==========================================
# 3. HALAMAN UTAMA STAFF (DINAMIS WA WEB SEARCH)
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

            # PENCARIAN DINAMIS ALA WA WEB
            search_text = st.text_input(
                "💬 Cari barang (seperti WA Web):", 
                placeholder="Ketik nama barang... (cth: ac, semen, sapu, lampu)"
            )

            # Filter Otomatis & Live
            if search_text.strip():
                df_filtered = df_barang[df_barang['Nama Barang'].astype(str).str.contains(search_text, case=False, na=False)]
            else:
                df_filtered = df_barang.head(10) # Menampilkan 10 awal jika belum mengetik

            st.caption(f"Menampilkan {len(df_filtered)} barang yang cocok:")

            # Render Barang Langsung di Kolom Bawah secara Dinamis
            for idx, row in df_filtered.iterrows():
                nama = str(row['Nama Barang'])
                satuan = str(row['Satuan'])
                harga = row['Harga']
                harga_clean = float(re.sub(r'[^0-9]', '', str(harga))) if pd.notnull(harga) else 0

                # Card Tampilan Barang
                st.markdown(f"""
                    <div class="wa-card">
                        <div class="wa-title">📌 {nama}</div>
                        <div class="wa-price">Rp {harga_clean:,.0f} <span class="wa-unit">/ {satuan}</span></div>
                    </div>
                """, unsafe_allow_html=True)

                # Form Input Jumlah (Qty) & Tambah
                col_qty, col_btn = st.columns([1, 2])
                with col_qty:
                    qty_input = st.number_input(
                        "Qty", 
                        min_value=1, 
                        value=1, 
                        step=1, 
                        key=f"qty_{idx}"
                    )
                with col_btn:
                    st.write("") # Spacing
                    if st.button(f"➕ Tambah {nama}", key=f"btn_{idx}"):
                        subtotal_calc = harga_clean * qty_input
                        dept_code = st.session_state.role.replace(" ", "")
                        
                        payload = {
                            "departemen": dept_code,
                            "periode": periode_sekarang,
                            "nama_barang": nama,
                            "satuan": satuan,
                            "harga": harga_clean,
                            "qty": qty_input,
                            "subtotal": subtotal_calc
                        }
                        
                        if webhook_url and "http" in webhook_url:
                            res = requests.post(webhook_url, json=payload)
                            if res.status_code == 200:
                                st.success(f"✅ {nama} ({qty_input} {satuan}) tersimpan ke Sheet!")
                            else:
                                st.error("Gagal terhubung ke Google Sheet.")
                        
                        st.session_state.keranjang.append(payload)
                        st.rerun()

            # KERANJANG BELANJA
            if st.session_state.keranjang:
                st.markdown("---")
                st.subheader("🛒 Pesanan Tersimpan Periode Ini")
                df_cart = pd.DataFrame(st.session_state.keranjang)
                st.dataframe(df_cart[['nama_barang', 'qty', 'satuan', 'subtotal']], use_container_width=True)

        except Exception as e:
            st.error(f"Gagal membaca database. Error: {e}")
    else:
        st.info("👈 Silakan konfigurasi link Google Sheet.")
