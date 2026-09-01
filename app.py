import streamlit as st
import pandas as pd
from datetime import datetime
import re
import requests

# ==============================================================================
# CONFIG DATABASE PERMANEN (PASTE LINK OM DI SINI SUPAYA OTOMATIS KONEK)
# ==============================================================================
URL_SHEET_DEFAULT = "https://docs.google.com/spreadsheets/d/1dhbkNELRxIa9HAexkpT13t2cbg3sqdRp5yBr7af9bcw/edit?usp=sharing"
WEBHOOK_URL_DEFAULT = "https://script.google.com/macros/s/AKfycbzVQGBtdyZwB93hzfJdpAGYADO9r-q2yL4L7u2DBWein3N5wH5qI9R2QY5apPoLeKkh/exec"
# ==============================================================================

# 1. Konfigurasi Halaman & Styling
st.set_page_config(page_title="E-Katalog Budgeting & Admin Portal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7fa; padding: 10px; }
    .stButton>button { background-color: #2563eb; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 45px; }
    div[data-testid="stSidebar"] { background-color: #e0f2fe; }
    h1, h2, h3 { color: #1e3a8a; }
    
    .item-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        margin-top: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #2563eb;
    }
    .item-title { font-size: 18px; font-weight: bold; color: #1e293b; }
    .item-price { font-size: 16px; color: #059669; font-weight: bold; margin-top: 5px; }
    .item-unit { font-size: 13px; color: #64748b; }
    
    /* Format Khusus Dokumen Proposal Cetak Admin */
    .print-container {
        background-color: white;
        padding: 25px;
        border: 1px solid #ccc;
        border-radius: 8px;
        color: #000;
        font-family: Arial, sans-serif;
    }
    .print-header {
        text-align: center;
        border-bottom: 2px solid #000;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .summary-box {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .summary-box th, .summary-box td {
        border: 1px solid #666;
        padding: 10px;
        text-align: left;
    }
    .summary-box th { background-color: #f0f0f0; }
    .ttd-table {
        width: 100%;
        margin-top: 30px;
        margin-bottom: 30px;
        text-align: center;
    }
    .ttd-space { height: 70px; }
    
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
    st.title("🟦 Portal Budgeting Staff & Admin")
    st.subheader("🔑 Login Akses Sistem")
    
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
        st.header("⚙️ Pengaturan Database")
        url_sheet = st.text_input("Link Google Sheet Utama:", value=URL_SHEET_DEFAULT)

    st.title("🖨️ Panel Cetak Proposal Anggaran Admin")
    
    if url_sheet and "http" in url_sheet:
        try:
            list_dept = ["Teknisi", "CleaningService", "Gardener"]
            dict_df = {}
            
            for dept in list_dept:
                sheet_target = f"{dept}_{datetime.now().strftime('%B%Y')}"
                try:
                    csv_url = get_csv_url(url_sheet, sheet_target)
                    df_temp = pd.read_csv(csv_url)
                    if not df_temp.empty:
                        dict_df[dept] = df_temp
                except:
                    pass

            df_tek = dict_df.get("Teknisi", pd.DataFrame(columns=['Nama Barang', 'Satuan', 'Harga Satuan', 'Jumlah (Qty)', 'Subtotal']))
            df_cs = dict_df.get("CleaningService", pd.DataFrame(columns=['Nama Barang', 'Satuan', 'Harga Satuan', 'Jumlah (Qty)', 'Subtotal']))
            df_gar = dict_df.get("Gardener", pd.DataFrame(columns=['Nama Barang', 'Satuan', 'Harga Satuan', 'Jumlah (Qty)', 'Subtotal']))

            budget_tek = df_tek['Subtotal'].sum() if 'Subtotal' in df_tek.columns else 0
            budget_cs = df_cs['Subtotal'].sum() if 'Subtotal' in df_cs.columns else 0
            budget_gar = df_gar['Subtotal'].sum() if 'Subtotal' in df_gar.columns else 0
            total_keseluruhan = budget_tek + budget_cs + budget_gar

            html_header = f"""
            <div class="print-container">
                <div class="print-header">
                    <h2>PROPOSAL PENGAJUAN ANGGARAN BUILDING MAINTENANCE</h2>
                    <h3>PERIODE: {periode_sekarang.upper()}</h3>
                </div>
                <h4>A. RINGKASAN ANGGARAN DEPARTEMEN</h4>
                <table class="summary-box">
                    <tr>
                        <th>No</th>
                        <th>Departemen</th>
                        <th>Jumlah Anggaran (Rupiah)</th>
                    </tr>
                    <tr>
                        <td>1</td>
                        <td>Teknisi</td>
                        <td>Rp {budget_tek:,.0f}</td>
                    </tr>
                    <tr>
                        <td>2</td>
                        <td>Cleaning Service</td>
                        <td>Rp {budget_cs:,.0f}</td>
                    </tr>
                    <tr>
                        <td>3</td>
                        <td>Gardener</td>
                        <td>Rp {budget_gar:,.0f}</td>
                    </tr>
                    <tr style="font-weight: bold; background-color: #f0f0f0;">
                        <td colspan="2" style="text-align: right;">TOTAL ESTIMASI ANGGARAN:</td>
                        <td>Rp {total_keseluruhan:,.0f}</td>
                    </tr>
                </table>
                <h4>B. LEMBAR PERSETUJUAN</h4>
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
                <h4>C. RINCIAN BARANG PER DEPARTEMEN</h4>
            </div>
            """
            st.markdown(html_header, unsafe_allow_html=True)

            cols_show = ['Nama Barang', 'Satuan', 'Harga Satuan', 'Jumlah (Qty)', 'Subtotal']
            
            st.markdown("##### 🛠️ 1. Departemen Teknisi")
            df_tek_display = df_tek[cols_show] if all(col in df_tek.columns for col in cols_show) else df_tek
            st.dataframe(df_tek_display, use_container_width=True)
            st.markdown(f"**Subtotal Teknisi:** `Rp {budget_tek:,.0f}`")
            st.markdown("---")

            st.markdown("##### 🧹 2. Departemen Cleaning Service")
            df_cs_display = df_cs[cols_show] if all(col in df_cs.columns for col in cols_show) else df_cs
            st.dataframe(df_cs_display, use_container_width=True)
            st.markdown(f"**Subtotal Cleaning Service:** `Rp {budget_cs:,.0f}`")
            st.markdown("---")

            st.markdown("##### 🌿 3. Departemen Gardener")
            df_gar_display = df_gar[cols_show] if all(col in df_gar.columns for col in cols_show) else df_gar
            st.dataframe(df_gar_display, use_container_width=True)
            st.markdown(f"**Subtotal Gardener:** `Rp {budget_gar:,.0f}`")

            html_footer = f"""
            <div class="print-container" style="border-top: none; margin-top: 20px;">
                <h2 style="text-align: right; color: #1e3a8a;">TOTAL KESELURUHAN DEPARTEMEN: Rp {total_keseluruhan:,.0f}</h2>
            </div>
            """
            st.markdown(html_footer, unsafe_allow_html=True)

            st.info("💡 Tekan **CTRL + P** di keyboard untuk mencetak/menyimpan proposal dalam bentuk PDF.")

        except Exception as e:
            st.error(f"Gagal memuat proposal admin. Pastikan link Google Sheet benar. Error: {e}")
    else:
        st.info("👈 Masukkan link Google Sheet di menu sebelah kiri terlebih dahulu.")

# ==========================================
# 4. HALAMAN UTAMA STAFF (OTOMATIS KONEK)
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
        st.header("⚙️ Pengaturan Database")
        url_sheet = st.text_input("Link Google Sheet Utama:", value=URL_SHEET_DEFAULT)
        webhook_url = st.text_input("URL Web App Google Script:", value=WEBHOOK_URL_DEFAULT)

    st.title(f"📦 Cari & Pilih Barang - {st.session_state.role}")
    
    if url_sheet and "http" in url_sheet:
        try:
            csv_url = get_csv_url(url_sheet, "DataBarang")
            df_barang = pd.read_csv(csv_url)
            df_barang.columns = df_barang.columns.str.strip()

            search_text = st.text_input("🔍 Ketik huruf/nama barang yang dicari:", placeholder="Contoh: ac, pel, lampu...")

            if search_text.strip():
                df_filtered = df_barang[df_barang['Nama Barang'].astype(str).str.contains(search_text, case=False, na=False)]
            else:
                df_filtered = df_barang

            list_nama_barang = ["-- Pilih dari daftar barang --"] + list(df_filtered['Nama Barang'].dropna().unique())

            pilihan_barang = st.selectbox("👇 Atau klik/ketik langsung pada dropdown berikut:", list_nama_barang)

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
                        payload = {
                            "departemen": st.session_state.role,
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
            st.error(f"Gagal membaca database. Pastikan link Google Sheet benar. Error: {e}")
    else:
        st.info("👈 Silakan isi link database Google Sheet default di dalam file app.py.")