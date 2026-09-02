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

# STYLING GLOBAL & ROBOTO FONT
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    html, body, [class*="css"], div, span, input, button {
        font-family: 'Roboto', sans-serif !important;
    }

    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, label, div, td, th {
        color: #f8fafc !important;
    }

    div[data-baseweb="input"] > div, input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 8px !important;
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
# Database Global Pengajuan yang Masuk ke Admin
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
    
    # Menampilkan pengajuan dari seluruh departemen
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

        # 2. TABEL INTERAKTIF UNTUK ADMIN
        filtered_admin_df['Hapus'] = False
        
        with st.form("admin_edit_form"):
            edited_admin_df = st.data_editor(
                filtered_admin_df,
                column_config={
                    "Hapus": st.column_config.CheckboxColumn("🗑️ Hapus", default=False),
                    "departemen": st.column_config.TextColumn("Departemen"),
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
                key="admin_editor"
            )

            submit_admin = st.form_submit_button("💾 Simpan Perubahan Admin", type="primary")

        if submit_admin:
            edited_admin_df['harga'] = pd.to_numeric(edited_admin_df['harga'], errors='coerce').fillna(0)
            edited_admin_df['qty'] = pd.to_numeric(edited_admin_df['qty'], errors='coerce').fillna(1)
            edited_admin_df['subtotal'] = edited_admin_df['harga'] * edited_admin_df['qty']
            
            updated_df = edited_admin_df[edited_admin_df['Hapus'] == False].drop(columns=['Hapus'])
            st.session_state.db_pengajuan_admin = updated_df.to_dict('records')
            st.toast("✅ Perubahan database berhasil disimpan!", icon="💾")
            st.rerun()

        # Ringkasan Total
        total_nominal_admin = edited_admin_df['subtotal'].sum()
        st.markdown(f"""
            <div class="cart-summary-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 15px; font-weight: bold; color: #ffffff;">TOTAL ANGGARAN VERIFIKASI ADMIN ({pilihan_periode}):</span>
                    <span style="font-size: 18px; font-weight: bold; color: #34d399;">Rp {total_nominal_admin:,.0f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 3. CETAK DOKUMEN PROPOSAL (BROWSER NATIVE HASIL UPDATE)
        st.markdown("---")
        st.subheader("🖨️ Cetak Dokumen Proposal Anggaran")
        
        if st.button("🖨️ Buka Preview & Cetak PDF", type="primary"):
            # A. Buat Tabel Ringkasan per Departemen
            summary_dept_df = edited_admin_df.groupby('departemen')['subtotal'].sum().reset_index()
            
            summary_html = ""
            for s_idx, s_row in enumerate(summary_dept_df.itertuples(), start=1):
                summary_html += f"""
                <tr>
                    <td style="text-align:center;">{s_idx}</td>
                    <td><b>{s_row.departemen}</b></td>
                    <td style="text-align:right;"><b>Rp {s_row.subtotal:,.0f}</b></td>
                </tr>
                """

            # B. Buat Rincian Barang Per Departemen
            detail_tables_html = ""
            grouped_dept = edited_admin_df.groupby('departemen')
            
            for dept_name, group in grouped_dept:
                dept_subtotal = group['subtotal'].sum()
                item_rows = ""
                for idx, r in enumerate(group.itertuples(), start=1):
                    item_rows += f"""
                    <tr>
                        <td style="text-align:center;">{idx}</td>
                        <td>{r.nama_barang}</td>
                        <td style="text-align:center;">{r.qty}</td>
                        <td style="text-align:center;">{r.satuan}</td>
                        <td style="text-align:right;">Rp {r.harga:,.0f}</td>
                        <td style="text-align:right;">Rp {r.subtotal:,.0f}</td>
                    </tr>
                    """
                
                detail_tables_html += f"""
                <h4 style="margin-top:25px; margin-bottom:8px;">🏢 Departemen: {dept_name}</h4>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 5%;">No</th>
                            <th style="width: 45%;">Nama Barang</th>
                            <th style="width: 10%;">Qty</th>
                            <th style="width: 10%;">Satuan</th>
                            <th style="width: 15%;">Harga Unit</th>
                            <th style="width: 15%;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {item_rows}
                        <tr class="total-row">
                            <td colspan="5" style="text-align:right;">SUBTOTAL {dept_name.upper()}:</td>
                            <td style="text-align:right;">Rp {dept_subtotal:,.0f}</td>
                        </tr>
                    </tbody>
                </table>
                """

            # C. Template HTML Lengkap untuk Cetak PDF
            tgl_cetak = datetime.now().strftime("%d %B %Y")
            html_print = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #000; padding: 20px; }}
                h2 {{ text-align: center; margin-bottom: 5px; text-transform: uppercase; }}
                p.sub {{ text-align: center; font-size: 13px; color: #333; margin-top: 0; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
                th, td {{ border: 1px solid #333; padding: 7px 10px; font-size: 12px; }}
                th {{ background-color: #f2f2f2; text-align: center; }}
                .total-row {{ font-weight: bold; background-color: #e6e6e6; }}
                .summary-box {{ border: 2px solid #000; padding: 12px; margin-bottom: 20px; background-color: #fafafa; }}
                .summary-title {{ font-weight: bold; font-size: 13px; margin-bottom: 8px; text-transform: uppercase; }}
                .signature-section {{ width: 100%; margin-top: 40px; border: none; }}
                .signature-section td {{ border: none; text-align: center; padding: 0px; font-size: 12px; }}
            </style>
            </head>
            <body>
                <h2>PROPOSAL PENGAJUAN ANGGARAN BUDGETING</h2>
                <p class="sub">Periode: <b>{pilihan_periode}</b> | Filter: <b>{pilihan_dept}</b></p>
                
                <!-- 1. RINGKASAN EKSEKUTIF UNTUK PIMPINAN -->
                <div class="summary-box">
                    <div class="summary-title">📊 RINGKASAN KEBUTUHAN BIAYA PER DEPARTEMEN</div>
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 10%;">No</th>
                                <th style="width: 65%;">Departemen</th>
                                <th style="width: 25%;">Total Pengajuan</th>
                            </tr>
                        </thead>
                        <tbody>
                            {summary_html}
                            <tr class="total-row">
                                <td colspan="2" style="text-align:right;">GRAND TOTAL ANGGARAN BULAN INI:</td>
                                <td style="text-align:right; font-size:13px; color:#000;">Rp {total_nominal_admin:,.0f}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <hr style="border: 1px dashed #666; margin-top: 30px; margin-bottom: 10px;">
                <h3 style="text-align: center; margin-bottom: 15px;">RINCIAN ITEM PER DEPARTEMEN</h3>

                <!-- 2. DETAIL TABLE BARANG PER DEPARTEMEN -->
                {detail_tables_html}

                <!-- 3. GRAND TOTAL FOOTER -->
                <br>
                <table>
                    <tr class="total-row" style="font-size: 13px;">
                        <td style="text-align:right; padding: 10px;">GRAND TOTAL ENTIRE ANGGARAN:</td>
                        <td style="text-align:right; width: 25%; padding: 10px;">Rp {total_nominal_admin:,.0f}</td>
                    </tr>
                </table>

                <!-- 4. KOLOM TANDA TANGAN -->
                <table class="signature-section">
                    <tr>
                        <td style="width: 50%;"></td>
                        <td style="width: 50%;">Jakarta, {tgl_cetak}</td>
                    </tr>
                    <tr>
                        <td style="padding-top: 15px;">Dibuat oleh,</td>
                        <td style="padding-top: 15px;">Diketahui oleh,</td>
                    </tr>
                    <tr>
                        <td style="padding-top: 60px;"><b><u>Ali Sukmawan</u></b><br>Building Manager (BM)</td>
                        <td style="padding-top: 60px;"><b><u>Aristya Pambudi</u></b><br>General Manager</td>
                    </tr>
                </table>

                <script>
                    window.onload = function() {{ window.print(); }}
                </script>
            </body>
            </html>
            """
            st.components.v1.html(html_print, height=750, scrolling=True)

    else:
        st.info("ℹ️ Belum ada data pengajuan anggaran dari departemen manapun yang di-Submit.")

# ==========================================
# 3. KATALOG STAFF (TEKNISI, CS, GARDENER, DLL)
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
        st.session_state.webhook_url = webhook_url

    st.title(f"📦 Katalog Barang — {st.session_state.role}")
    
    if url_sheet and "http" in url_sheet:
        try:
            csv_url = get_csv_url(url_sheet, "DataBarang")
            df_barang = pd.read_csv(csv_url)
            df_barang.columns = df_barang.columns.str.strip()

            df_barang['Harga_Clean'] = df_barang['Harga'].apply(
                lambda x: float(re.sub(r'[^0-9]', '', str(x))) if pd.notnull(x) else 0.0
            )

            # 1. PENCARIAN STATIS / STICKY
            search_query = st.text_input(
                "🔍 Cari Nama Barang:", 
                placeholder="⚡ Ketik nama barang... (Filter otomatis & instan)",
                key="sticky_search_input"
            )

            if search_query:
                filtered_df = df_barang[df_barang['Nama Barang'].astype(str).str.contains(search_query, case=False, na=False)].copy()
            else:
                filtered_df = df_barang.copy()

            filtered_df.insert(0, 'Pilih', False)
            filtered_df['Jumlah (Qty)'] = 1

            # 2. TABEL BARANG MODERN
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
                    height=360,
                    key="catalog_editor"
                )

                submit_button = st.form_submit_button("➕ Masukkan Barang Terpilih ke Keranjang", type="primary", use_container_width=True)

            # 3. LOGIKA TAMBAH KE KERANJANG LOKAL
            if submit_button:
                items_to_add = edited_df[edited_df['Pilih'] == True]
                
                if not items_to_add.empty:
                    dept_code = st.session_state.role
                    periode_sec = datetime.now().strftime("%B%Y")

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
                                "departemen": dept_code,
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

            # ==========================================
            # TABEL KERANJANG BELANJA & SUBMIT ADMIN
            # ==========================================
            st.markdown("---")
            st.subheader("🛒 Isi Keranjang Belanja")

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

                # TOMBOL SUBMIT KE ADMIN DAN WEBHOOK
                col_sub1, col_sub2 = st.columns(2)
                
                with col_sub1:
                    if st.button("🚀 Submit Pengajuan ke Admin", type="primary"):
                        # Masukkan ke Database Admin
                        for item in st.session_state.keranjang:
                            st.session_state.db_pengajuan_admin.append(item)
                            
                            # Kirim ke Webhook jika URL tersedia
                            if webhook_url and "http" in webhook_url:
                                try:
                                    requests.post(webhook_url, json=item, timeout=3)
                                except:
                                    pass
                                    
                        st.session_state.keranjang = []
                        st.balloons()
                        st.success("🎉 Pengajuan berhasil dikirimkan ke Admin!")
                        st.rerun()

                with col_sub2:
                    if st.button("🔴 Kosongkan Semua Keranjang", key="clear_all_cart"):
                        st.session_state.keranjang = []
                        st.rerun()

            else:
                st.info("Keranjang masih kosong. Pilih barang pada tabel di atas untuk menambahkan.")

        except Exception as e:
            st.error(f"Gagal membaca database. Error: {e}")
    else:
        st.info("👈 Silakan atur link Google Sheet terlebih dahulu.")
