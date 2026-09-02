import streamlit as st
import pandas as pd
from datetime import datetime
import re
import requests
import json
import streamlit.components.v1 as components

# ==============================================================================
# CONFIG DATABASE PERMANEN
# ==============================================================================
URL_SHEET_DEFAULT = "https://docs.google.com/spreadsheets/d/1dhbkNELRxIa9HAexkpT13t2cbg3sqdRp5yBr7af9bcw/edit?usp=sharing"
WEBHOOK_URL_DEFAULT = "https://script.google.com/macros/s/AKfycbzVQGbtdyZwB93hzfJdpAGYAD09r-q2yL4L7u2DBWein3N5wH5qI9R2QY5apPoLeKkh/exec"
# ==============================================================================

st.set_page_config(page_title="E-Katalog Budgeting & Admin Portal", layout="wide")

# STYLING GLOBAL, FIX DARK MODE FONT, & CLEANUP UI
st.markdown("""
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
""", unsafe_allow_html=True)

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

# --- INIT STATE MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = ""
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []
if "db_pengajuan_admin" not in st.session_state:
    st.session_state.db_pengajuan_admin = []

def get_csv_url(url, sheet_name="DataBarang"):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if match:
        sheet_id = match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return url

# ==========================================
# 1. HALAMAN LOGIN
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
# 2. PANEL ADMIN (VERIFIKASI & EDIT & CETAK)
# ==========================================
elif st.session_state.role == "Admin":
    periode_sekarang = datetime.now().strftime("%B %Y")
    
    with st.sidebar:
        st.header("👤 Panel Admin")
        st.write(f"📅 Periode Aktif: **{periode_sekarang}**")
        if st.button("Keluar (Logout)"):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.rerun()
            
        st.markdown("---")
        st.header("⚙️ Database")
        url_sheet = st.text_input("Link Google Sheet Utama:", value=URL_SHEET_DEFAULT)

    st.title("🛡️ Admin Portal — Verifikasi & Cetak Proposal")
    
    if st.session_state.db_pengajuan_admin:
        df_admin = pd.DataFrame(st.session_state.db_pengajuan_admin)
        
        # 1. FILTER PERIODE & DEPARTEMEN
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            daftar_periode = list(df_admin['periode'].unique())
            pilihan_periode = st.selectbox("📅 Pilih Periode Anggaran:", options=daftar_periode)
            
        with col_f2:
            daftar_dept = ["Semua Departemen"] + list(df_admin['departemen'].unique())
            pilihan_dept = st.selectbox("🏢 Filter Departemen:", options=daftar_dept)

        filtered_admin_df = df_admin[df_admin['periode'] == pilihan_periode].copy()
        if pilihan_dept != "Semua Departemen":
            filtered_admin_df = filtered_admin_df[filtered_admin_df['departemen'] == pilihan_dept]

        st.subheader("📝 Verifikasi & Edit Data Pengajuan Staff")
        st.caption("Admin dapat mengubah Qty/Harga, menghapus item, atau menambah item baru.")

        if pilihan_dept == "Semua Departemen":
            depts_to_show = list(filtered_admin_df['departemen'].unique())
        else:
            depts_to_show = [pilihan_dept]

        edited_dept_dfs = []
        
        # 2. TABEL INTERAKTIF DIPISAH PER DEPARTEMEN
        with st.form("admin_edit_form"):
            for dept_name in depts_to_show:
                dept_df = filtered_admin_df[filtered_admin_df['departemen'] == dept_name].copy()
                if dept_df.empty:
                    continue
                
                dept_df['Hapus'] = False
                cols_to_show = ['Hapus', 'periode', 'nama_barang', 'satuan', 'harga', 'qty', 'subtotal']
                
                st.markdown(f"### 🏢 Departemen: **{dept_name}**")

                edited_d_df = st.data_editor(
                    dept_df[cols_to_show],
                    column_config={
                        "Hapus": st.column_config.CheckboxColumn("🗑️ Hapus", default=False),
                        "periode": st.column_config.TextColumn("Periode"),
                        "nama_barang": st.column_config.TextColumn("Nama Barang"),
                        "satuan": st.column_config.TextColumn("Satuan"),
                        "harga": st.column_config.NumberColumn("Harga (Rp)", format="Rp %'d"),
                        "qty": st.column_config.NumberColumn("Qty", min_value=1, step=1),
                        "subtotal": st.column_config.NumberColumn("Subtotal (Rp)", format="Rp %'d", disabled=True)
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic",
                    key=f"admin_editor_{dept_name}"
                )
                
                edited_d_df['departemen'] = dept_name
                edited_dept_dfs.append(edited_d_df)
                st.markdown("<br>", unsafe_allow_html=True)

            submit_admin = st.form_submit_button("💾 Simpan Perubahan Admin", type="primary")

        if edited_dept_dfs:
            combined_admin_df = pd.concat(edited_dept_dfs, ignore_index=True)
        else:
            combined_admin_df = pd.DataFrame(columns=['departemen', 'periode', 'nama_barang', 'satuan', 'harga', 'qty', 'subtotal', 'Hapus'])

        combined_admin_df['harga'] = pd.to_numeric(combined_admin_df['harga'], errors='coerce').fillna(0)
        combined_admin_df['qty'] = pd.to_numeric(combined_admin_df['qty'], errors='coerce').fillna(1)
        combined_admin_df['subtotal'] = combined_admin_df['harga'] * combined_admin_df['qty']

        if submit_admin:
            clean_updated_df = combined_admin_df[combined_admin_df['Hapus'] == False].drop(columns=['Hapus'])
            
            other_periods = [x for x in st.session_state.db_pengajuan_admin if x.get('periode') != pilihan_periode]
            
            if pilihan_dept != "Semua Departemen":
                other_depts_current_period = [
                    x for x in st.session_state.db_pengajuan_admin 
                    if x.get('periode') == pilihan_periode and x.get('departemen') != pilihan_dept
                ]
                st.session_state.db_pengajuan_admin = other_periods + other_depts_current_period + clean_updated_df.to_dict('records')
            else:
                st.session_state.db_pengajuan_admin = other_periods + clean_updated_df.to_dict('records')
                
            st.toast("✅ Perubahan database berhasil disimpan!", icon="💾")
            st.rerun()

        total_nominal_admin = combined_admin_df['subtotal'].sum()
        st.markdown(f"""
            <div class="cart-summary-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 15px; font-weight: bold; color: #ffffff;">TOTAL ANGGARAN VERIFIKASI ADMIN ({pilihan_periode}):</span>
                    <span style="font-size: 18px; font-weight: bold; color: #34d399;">Rp {total_nominal_admin:,.0f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 3. CETAK DOKUMEN PROPOSAL & PREVIEW (DENGAN TULISAN HITAM & BACKGROUND PUTIH)
        st.markdown("---")
        st.subheader("🖨️ Cetak Dokumen Proposal Anggaran")
        
        if st.button("🖨️ Buka Preview & Cetak PDF", type="primary"):
            tables_html = ""
            rekap_rows_html = ""
            grand_total = 0
            
            for dept_name in depts_to_show:
                dept_data = combined_admin_df[combined_admin_df['departemen'] == dept_name]
                if dept_data.empty:
                    continue
                
                dept_subtotal = dept_data['subtotal'].sum()
                grand_total += dept_subtotal
                
                # Menyiapkan baris untuk rekapitulasi subtotal tiap departemen
                rekap_rows_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #000;">Departemen {dept_name}</td>
                    <td style="padding: 8px; border: 1px solid #000; text-align: right; font-weight: bold;">Rp {dept_subtotal:,.0f}</td>
                </tr>
                """
                
                rows_html = ""
                for idx, r in enumerate(dept_data.itertuples(), start=1):
                    sub = float(r.harga) * float(r.qty)
                    rows_html += f"""
                    <tr>
                        <td style="text-align:center; border: 1px solid #000; padding: 6px;">{idx}</td>
                        <td style="border: 1px solid #000; padding: 6px;">{r.nama_barang}</td>
                        <td style="text-align:center; border: 1px solid #000; padding: 6px;">{r.qty}</td>
                        <td style="text-align:center; border: 1px solid #000; padding: 6px;">{r.satuan}</td>
                        <td style="text-align:right; border: 1px solid #000; padding: 6px;">Rp {r.harga:,.0f}</td>
                        <td style="text-align:right; border: 1px solid #000; padding: 6px;">Rp {sub:,.0f}</td>
                    </tr>
                    """
                
                tables_html += f"""
                <h3 style="margin-top: 25px; margin-bottom: 8px; color: #000000; font-size: 16px;">🏢 Departemen: {dept_name}</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <thead>
                        <tr style="background-color: #f2f2f2; color: #000;">
                            <th style="width: 5%; border: 1px solid #000; padding: 6px;">No</th>
                            <th style="border: 1px solid #000; padding: 6px; text-align: left;">Nama Barang</th>
                            <th style="width: 10%; border: 1px solid #000; padding: 6px;">Qty</th>
                            <th style="width: 10%; border: 1px solid #000; padding: 6px;">Satuan</th>
                            <th style="width: 20%; border: 1px solid #000; padding: 6px; text-align: right;">Harga Unit</th>
                            <th style="width: 20%; border: 1px solid #000; padding: 6px; text-align: right;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                        <tr style="font-weight: bold; background-color: #e6e6e6; color: #000;">
                            <td colspan="5" style="text-align:right; border: 1px solid #000; padding: 6px;">SUBTOTAL {dept_name.upper()}:</td>
                            <td style="text-align:right; border: 1px solid #000; padding: 6px;">Rp {dept_subtotal:,.0f}</td>
                        </tr>
                    </tbody>
                </table>
                """

            html_print = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                * {{ color: #000000 !important; font-family: Arial, sans-serif; }}
                body {{ background-color: #ffffff !important; padding: 25px; margin: 0; }}
                h2 {{ text-align: center; margin-bottom: 5px; color: #000000; }}
                p.sub {{ text-align: center; font-size: 13px; color: #333333; margin-top: 0; margin-bottom: 20px; }}
                .rekap-box {{ margin-top: 30px; margin-bottom: 30px; width: 60%; float: right; }}
                .signature-container {{ margin-top: 50px; width: 100%; clear: both; }}
                .signature-table {{ width: 100%; border: none !important; margin-top: 30px; }}
                .signature-table td {{ border: none !important; text-align: center; vertical-align: bottom; height: 90px; padding: 0; }}
            </style>
            </head>
            <body>
                <h2>PROPOSAL PENGAJUAN ANGGARAN BUDGETING</h2>
                <p class="sub">Periode: <b>{pilihan_periode}</b> | Filter: <b>{pilihan_dept}</b></p>
                
                {tables_html}

                <!-- TABEL RINGKASAN REKAPITULASI SUBTOTAL PER DEPARTEMEN -->
                <div style="clear: both; margin-top: 30px;">
                    <h4 style="margin-bottom: 8px; font-size: 14px; color: #000;">📊 REKAPITULASI TOTAL ANGGARAN DEPARTEMEN</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background-color: #e2e8f0; color: #000;">
                                <th style="border: 1px solid #000; padding: 8px; text-align: left;">Departemen</th>
                                <th style="border: 1px solid #000; padding: 8px; text-align: right; width: 30%;">Total Pengajuan</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rekap_rows_html}
                            <tr style="background-color: #cbd5e1; font-weight: bold;">
                                <td style="border: 1px solid #000; padding: 10px; text-align: right;">GRAND TOTAL ANGGARAN:</td>
                                <td style="border: 1px solid #000; padding: 10px; text-align: right; font-size: 15px;">Rp {grand_total:,.0f}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- KOLOM TANDA TANGAN -->
                <div class="signature-container">
                    <table class="signature-table">
                        <tr>
                            <td style="width: 33%;">
                                Diajukan oleh,<br><br><br><br><br>
                                _______________________<br>
                                <b>Kepala Departemen / Staff</b>
                            </td>
                            <td style="width: 33%;">
                                Diverifikasi oleh,<br><br><br><br><br>
                                _______________________<br>
                                <b>Admin / Tim Budgeting</b>
                            </td>
                            <td style="width: 33%;">
                                Disetujui oleh,<br><br><br><br><br>
                                _______________________<br>
                                <b>Pimpinan / Direktur</b>
                            </td>
                        </tr>
                    </table>
                </div>

                <script>
                    window.onload = function() {{ window.print(); }}
                </script>
            </body>
            </html>
            """
            st.components.v1.html(html_print, height=700, scrolling=True)

    else:
        st.info("ℹ️ Belum ada data pengajuan anggaran dari departemen manapun yang di-Submit.")

# ==========================================
# 3. KATALOG STAFF (TEKNISI, CS, GARDENER, DLL)
# ==========================================
else:
    periode_sekarang = datetime.now().strftime("%B %Y")
    dept_aktif = st.session_state.role
    
    with st.sidebar:
        st.header(f"👤 {dept_aktif}")
        st.write(f"📅 Periode: **{periode_sekarang}**")
        
        if st.button("Keluar (Logout)"):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.session_state.keranjang = []
            st.rerun()
            
        st.markdown("---")
        st.header("⚙️ Database")
        url_sheet = st.text_input("Link Google Sheet Utama:", value=URL_SHEET_DEFAULT)
        webhook_url = st.text_input("URL Web App Google Script:", value=WEBHOOK_URL_DEFAULT)
        st.session_state.webhook_url = webhook_url

    st.title(f"📦 Katalog Barang — {dept_aktif}")
    
    if url_sheet and "http" in url_sheet:
        try:
            csv_url = get_csv_url(url_sheet, "DataBarang")
            df_barang = pd.read_csv(csv_url)
            df_barang.columns = df_barang.columns.str.strip()

            df_barang['Harga_Clean'] = df_barang['Harga'].apply(
                lambda x: float(re.sub(r'[^0-9]', '', str(x))) if pd.notnull(x) else 0.0
            )

            # 1. PENCARIAN BARANG
            search_query = st.text_input(
                "🔍 Cari Nama Barang:", 
                placeholder="⚡ Ketik nama barang...",
                key="sticky_search_input"
            )

            if search_query:
                filtered_df = df_barang[df_barang['Nama Barang'].astype(str).str.contains(search_query, case=False, na=False)].copy()
            else:
                filtered_df = df_barang.copy()

            filtered_df.insert(0, 'Pilih', False)
            filtered_df['Jumlah (Qty)'] = 1

            # 2. TABEL BARANG
            st.caption(f"📊 Menampilkan **{len(filtered_df)}** barang tersedia.")
            
            with st.form("catalog_form"):
                edited_df = st.data_editor(
                    filtered_df[['Pilih', 'Nama Barang', 'Satuan', 'Harga_Clean', 'Jumlah (Qty)']],
                    column_config={
                        "Pilih": st.column_config.CheckboxColumn("🛒 Pilih", default=False),
                        "Nama Barang": st.column_config.TextColumn("📦 Nama Barang", disabled=True),
                        "Satuan": st.column_config.TextColumn("🏷️ Satuan", disabled=True),
                        "Harga_Clean": st.column_config.NumberColumn("💰 Harga Unit", format="Rp %'d", disabled=True),
                        "Jumlah (Qty)": st.column_config.NumberColumn("🔢 Qty", min_value=1, step=1, required=True)
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=320,
                    key="catalog_editor"
                )

                submit_button = st.form_submit_button("➕ Masukkan Barang Terpilih ke Keranjang", type="primary", use_container_width=True)

            if submit_button:
                items_to_add = edited_df[edited_df['Pilih'] == True]
                
                if not items_to_add.empty:
                    periode_sec = datetime.now().strftime("%B %Y")

                    for _, row in items_to_add.iterrows():
                        add_nama = row['Nama Barang']
                        add_satuan = row['Satuan']
                        add_harga = float(row['Harga_Clean'])
                        add_qty = int(row['Jumlah (Qty)'])
                        add_subtotal = add_harga * add_qty

                        found = False
                        for item in st.session_state.keranjang:
                            if item["nama_barang"] == add_nama:
                                item["qty"] += add_qty
                                item["subtotal"] = item["qty"] * item["harga"]
                                found = True
                                break

                        if not found:
                            st.session_state.keranjang.append({
                                "departemen": dept_aktif,
                                "periode": periode_sec,
                                "nama_barang": add_nama,
                                "satuan": add_satuan,
                                "harga": add_harga,
                                "qty": add_qty,
                                "subtotal": add_subtotal
                            })

                    st.toast(f"✅ Berhasil menambah {len(items_to_add)} barang ke keranjang!", icon="🛒")
                    st.rerun()
                else:
                    st.warning("⚠️ Silakan centang minimal satu barang pada kolom 'Pilih' terlebih dahulu.")

            # 3. KERANJANG BELANJA DEPARTEMEN
            st.markdown("---")
            st.subheader("🛒 Isi Keranjang Belanja (Belum Disubmit)")

            if st.session_state.keranjang:
                total_nominal = 0
                to_delete = None
                
                for c_idx, item in enumerate(st.session_state.keranjang):
                    total_nominal += item["subtotal"]
                    
                    with st.container():
                        col_info, col_qty, col_sub, col_del = st.columns([3, 1.5, 2, 1])
                        
                        with col_info:
                            st.markdown(f"**📌 {item['nama_barang']}** \n<small style='color: #94a3b8;'>Rp {item['harga']:,.0f} / {item['satuan']}</small>", unsafe_allow_html=True)
                        
                        with col_qty:
                            new_qty = st.number_input(
                                "Qty", 
                                min_value=1, 
                                value=int(item['qty']), 
                                key=f"cart_qty_key_{c_idx}", 
                                label_visibility="collapsed"
                            )
                            if new_qty != item['qty']:
                                st.session_state.keranjang[c_idx]['qty'] = new_qty
                                st.session_state.keranjang[c_idx]['subtotal'] = new_qty * item['harga']
                                st.rerun()

                        with col_sub:
                            st.markdown(f"**Rp {item['subtotal']:,.0f}**")
                            
                        with col_del:
                            if st.button("🗑️", key=f"cart_del_key_{c_idx}"):
                                to_delete = c_idx
                    
                    st.markdown("<hr style='margin: 4px 0; border-color: #334155;'>", unsafe_allow_html=True)

                if to_delete is not None:
                    st.session_state.keranjang.pop(to_delete)
                    st.rerun()

                st.markdown(f"""
                    <div class="cart-summary-box">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 15px; font-weight: bold; color: #ffffff;">TOTAL ANGGARAN DIAJUKAN:</span>
                            <span style="font-size: 18px; font-weight: bold; color: #34d399;">Rp {total_nominal:,.0f}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    if st.button("🚀 Submit Pengajuan ke Admin", type="primary"):
                        for item in st.session_state.keranjang:
                            st.session_state.db_pengajuan_admin.append(item)
                            
                            if webhook_url and "http" in webhook_url:
                                try:
                                    requests.post(webhook_url, json=item, timeout=3)
                                meb:
                                    pass
                                    
                        st.session_state.keranjang = []
                        st.balloons()
                        st.success("🎉 Pengajuan berhasil dikirimkan ke Admin!")
                        st.rerun()

                with col_sub2:
                    if st.button("🔴 Kosongkan Keranjang", key="clear_all_cart"):
                        st.session_state.keranjang = []
                        st.rerun()

            else:
                st.info("Keranjang saat ini kosong.")

            # 4. MODUL CROSS-CHECK PENGAJUAN (UNTUK DEPARTEMEN)
            st.markdown("---")
            st.subheader(f"📋 Riwayat & Status Pengajuan Anggaran ({dept_aktif})")
            
            # Filter data yang pernah diajukan oleh departemen ini saja
            submitted_dept_data = [
                x for x in st.session_state.db_pengajuan_admin 
                if x.get('departemen') == dept_aktif
            ]
            
            if submitted_dept_data:
                df_history = pd.DataFrame(submitted_dept_data)
                
                # Tampilkan rangkuman total & data tabel
                tot_submitted = df_history['subtotal'].sum()
                st.caption(f"Berikut adalah barang yang sudah terdaftar di Admin untuk departemen **{dept_aktif}**:")
                
                st.dataframe(
                    df_history[['periode', 'nama_barang', 'qty', 'satuan', 'harga', 'subtotal']],
                    column_config={
                        "periode": "Periode",
                        "nama_barang": "Nama Barang",
                        "qty": "Qty",
                        "satuan": "Satuan",
                        "harga": st.column_config.NumberColumn("Harga Unit", format="Rp %'d"),
                        "subtotal": st.column_config.NumberColumn("Subtotal", format="Rp %'d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                st.markdown(f"**Total Anggaran Terdaftar Admin: :green[Rp {tot_submitted:,.0f}]**")
            else:
                st.caption("Belum ada pengajuan anggaran yang disubmit ke Admin untuk departemen ini.")

        except Exception as e:
            st.error(f"Gagal membaca database. Error: {e}")
    else:
        st.info("👈 Silakan atur link Google Sheet terlebih dahulu.")
