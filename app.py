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

# 1. Konfigurasi Halaman & Styling Font Roboto & Kontras Terang (Pop-up Dropdown Fixed)
st.set_page_config(page_title="E-Katalog Budgeting & Admin Portal", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* Paksa background aplikasi & kontras teks agar selalu jelas (Mobile Friendly) */
    .stAppViewContainer, .stApp {
        background-color: #f8fafc !important;
        font-family: 'Roboto', sans-serif !important;
    }

    /* Pengaturan Semua Teks & Label */
    h1, h2, h3, h4, h5, h6, p, span, label, div, td, th {
        font-family: 'Roboto', sans-serif !important;
        color: #0f172a !important; /* Warna teks gelap tegas */
    }

    /* Styling Input Box & Selectbox Utama */
    div[data-baseweb="select"] > div, input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }

    /* PERBAIKAN DROPDOWN POP-UP (MENU MELAYANG SAAT DIKLIK) */
    div[data-baseweb="popover"], 
    div[data-baseweb="menu"], 
    ul[role="listbox"],
    li[role="option"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    
    /* Hover/Pilihan pada Dropdown */
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #e2e8f0 !important;
        color: #1d4ed8 !important;
    }

    /* Teks dalam Dropdown / Selectbox */
    div[data-baseweb="select"] * {
        color: #0f172a !important;
    }

    /* Styling Tombol Utama */
    .stButton>button { 
        background-color: #1d4ed8 !important; 
        color: #ffffff !important; 
        border-radius: 6px !important; 
        font-weight: 600 !important; 
        font-size: 14px !important;
        width: 100% !important; 
        height: 42px !important; 
        border: none !important;
    }
    
    /* Sidebar Background & Teks */
    section[data-testid="stSidebar"] { 
        background-color: #f1f5f9 !important; 
    }
    section[data-testid="stSidebar"] * {
        color: #0f172a !important;
    }
    
    /* Ukuran Judul Ringkas & Proporsional */
    h1 { font-size: 22px !important; font-weight: 700 !important; }
    h2 { font-size: 18px !important; font-weight: 700 !important; }
    h3 { font-size: 16px !important; font-weight: 600 !important; }
    
    /* Kartu Barang (Item Card) */
    .item-card {
        background-color: #ffffff !important;
        padding: 14px !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        border-left: 5px solid #1d4ed8 !important;
        border: 1px solid #e2e8f0 !important;
    }
    .item-title { font-size: 15px !important; font-weight: 700 !important; color: #0f172a !important; }
    .item-price { font-size: 14px !important; color: #047857 !important; font-weight: 700 !important; margin-top: 4px !important; }
    .item-unit { font-size: 12px !important; color: #475569 !important; }
    
    /* Format Cetak Proposal Admin */
    .print-container {
        background-color: #ffffff !important;
        padding: 15px !important;
        color: #000000 !important;
        font-family: 'Roboto', sans-serif !important;
        border-radius: 8px !important;
    }
    .print-header {
        text-align: center;
        border-bottom: 2px solid #000000;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
    .print-header h2 {
        font-size: 16px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        color: #000000 !important;
    }
    .print-header h3 {
        font-size: 13px !important;
        font-weight: 500 !important;
        margin-top: 4px !important;
        color: #000000 !important;
    }
    .print-section-title {
        font-size: 13px !important;
        font-weight: 700 !important;
        margin-top: 12px;
        margin-bottom: 6px;
        color: #000000 !important;
    }
    .summary-box {
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
        margin-bottom: 15px;
        font-size: 12px;
    }
    .summary-box th, .summary-box td {
        border: 1px solid #333333;
        padding: 6px 8px;
        text-align: left;
        color: #000000 !important;
    }
    .summary-box th { background-color: #f1f5f9; font-weight: 700; }
    
    .ttd-table {
        width: 100%;
        margin-top: 20px;
        margin-bottom: 20px;
        text-align: center;
        font-size: 12px;
    }
    .ttd-space { height: 50px; }
    
    @media print {
        body * { visibility: hidden; }
        .print-container, .print-container * { visibility: visible; }
        .print-container { position: absolute; left: 0; top: 0; width: 100%; }
        .no-print { display: none !important; }
    }
    </style>
""", unsafe_allow_html=True)

# Database Password Role Staff & Admin
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
# 2. LANDING PAGE & LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.title("🔑 Login Portal Budgeting")
    
    role_pilihan = st.selectbox("Pilih Akses / Departemen:", list(ROLE_DB.keys()))
    password_input = st.text_input("Kata Sandi (Password):", type="password")
    
    if st.button("Masuk ke Aplikasi"):
        if password_input == ROLE_DB[role_pilihan]:
            st.session_state.logged_in = True
            st.session_state.role = role_pilihan
            st.rerun()
        else:
            st.error("Kata sandi salah!")

# ==========================================
# 3. HALAMAN KHUSUS ADMIN (CETAK PROPOSAL)
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
                <div class="print-header">
                    <h2>PROPOSAL PENGAJUAN ANGGARAN BUILDING MAINTENANCE</h2>
                    3>PERIODE: {periode_sekarang.upper()}</h3>
                </div>
                <div class="print-section-title">A. RINGKASAN ANGGARAN DEPARTEMEN</div>
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
                    <tr style="font-weight: bold; background-color: #f1f5f9;">
                        <td colspan="2" style="text-align: right;">TOTAL ESTIMASI ANGGARAN:</td>
                        <td>Rp {total_keseluruhan:,.0f}</td>
                    </tr>
                </table>
                <div class="print-section-title">B. LEMBAR PERSETUJUAN</div>
                <table class="ttd-table">
                    <tr>
                        <td width="50%">Diajukan Oleh,<br><b>Building Mgr</b></td>
                        <td width="50%">Disetujui Oleh,<br><b>General Mgr</b></td>
                    </tr>
                    <tr>
                        <td class="ttd-space"></td>
                        <td class="ttd-space"></td>
                    </tr>
                    <tr>
                        <td><b><u>Ali Sukmawan</u></b></td>
                        <td><b><u>Aristya Pambudi</u></b></td>
                    </tr>
                </table>
                <div class="print-section-title">C. RINCIAN BARANG PER DEPARTEMEN</div>
            </div>
            """
            st.markdown(html_header, unsafe_allow_html=True)

            cols_show = ['Nama Barang', 'Satuan', 'Harga Satuan', 'Jumlah (Qty)', 'Subtotal']
            
            for idx, (code_dept, name_dept) in enumerate(list_dept, 1):
                st.markdown(f"**{idx}. Departemen {name_dept}**")
                df_curr = dict_df.get(name_dept, pd.DataFrame(columns=cols_show))
                df_display = df_curr[cols_show] if all(c in df_curr.columns for c in cols_show) else df_curr
                st.dataframe(df_display, use_container_width=True)
                st.markdown(f"**Subtotal {name_dept}:** `Rp {dict_budget.get(name_dept, 0):,.0f}`")
                st.markdown("---")

            st.info("💡 Tekan **CTRL + P** untuk menyimpannya dalam format PDF.")

        except Exception as e:
            st.error(f"Gagal memuat proposal. Error: {e}")
    else:
        st.info("👈 Silakan isi link database Google Sheet default di dalam file app.py.")

# ==========================================
# 4. HALAMAN UTAMA STAFF
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

    st.title(f"📦 Pilih Barang - {st.session_state.role}")
    
    if url_sheet and "http" in url_sheet:
        try:
            csv_url = get_csv_url(url_sheet, "DataBarang")
            df_barang = pd.read_csv(csv_url)
            df_barang.columns = df_barang.columns.str.strip()

            search_text = st.text_input("🔍 Ketik nama barang:", placeholder="Contoh: ac, pel, semen...")

            if search_text.strip():
                df_filtered = df_barang[df_barang['Nama Barang'].astype(str).str.contains(search_text, case=False, na=False)]
            else:
                df_filtered = df_barang

            list_nama_barang = ["-- Pilih dari daftar barang --"] + list(df_filtered['Nama Barang'].dropna().unique())

            pilihan_barang = st.selectbox("👇 Pilih barang dari dropdown:", list_nama_barang)

            if pilihan_barang != "-- Pilih dari daftar barang --":
                row_barang = df_barang[df_barang['Nama Barang'] == pilihan_barang].iloc[0]
                
                nama = str(row_barang['Nama Barang'])
                satuan = str(row_barang['Satuan'])
                harga = row_barang['Harga']
                harga_clean = float(re.sub(r'[^0-9]', '', str(harga))) if pd.notnull(harga) else 0

                st.markdown(f"""
                    <div class="item-card">
                        <div class="item-title">📌 {nama}</div>
                        <div class="item-price">Harga Satuan: Rp {harga_clean:,.0f}</div>
                        <div class="item-unit">Satuan: {satuan}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.form("form_pesan", clear_on_submit=True):
                    qty = st.number_input("Masukkan Jumlah (Qty):", min_value=1, value=1, step=1)
                    subtotal_estimasi = harga_clean * qty
                    st.write(f"💰 Total Subtotal: **Rp {subtotal_estimasi:,.0f}**")
                    
                    submitted = st.form_submit_button("➕ Simpan ke Pengajuan")
                    
                    if submitted:
                        dept_code = st.session_state.role.replace(" ", "")
                        
                        payload = {
                            "departemen": dept_code,
                            "periode": periode_sekarang,
                            "nama_barang": nama,
                            "satuan": satuan,
                            "harga": harga_clean,
                            "qty": qty,
                            "subtotal": subtotal_estimasi
                        }
                        
                        if webhook_url and "http" in webhook_url:
                            res = requests.post(webhook_url, json=payload)
                            if res.status_code == 200:
                                st.success(f"✅ {nama} ({qty} {satuan}) berhasil disimpan ke Google Sheet!")
                            else:
                                st.error("Gagal mengirim data ke Google Sheet.")
                        else:
                            st.warning("Data tersimpan sementara di memori aplikasi.")

                        st.session_state.keranjang.append(payload)

            else:
                st.info("💡 Ketik kata kunci di atas atau pilih langsung dari menu drop-down.")

            if st.session_state.keranjang:
                st.markdown("---")
                st.subheader("🛒 Pesanan Tersimpan Saat Ini")
                df_cart = pd.DataFrame(st.session_state.keranjang)
                st.dataframe(df_cart[['nama_barang', 'qty', 'satuan', 'subtotal']], use_container_width=True)

        except Exception as e:
            st.error(f"Gagal membaca database. Error: {e}")
    else:
        st.info("👈 Silakan isi link database Google Sheet default di dalam file app.py.")
