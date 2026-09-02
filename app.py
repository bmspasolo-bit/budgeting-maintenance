import streamlit as st
import pandas as pd
from datetime import datetime
import re
import requests
import json  # <-- TAMBAHKAN BARIS INI
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

# Catch Data dari Query Parameters (Penyambung JavaScript -> Python)
query_params = st.query_params
if "add_nama" in query_params:
    add_nama = query_params["add_nama"]
    add_satuan = query_params.get("add_satuan", "")
    add_harga = float(query_params.get("add_harga", 0))
    add_qty = int(query_params.get("add_qty", 1))
    
    dept_code = st.session_state.role.replace(" ", "") if st.session_state.role else "General"
    periode_sec = datetime.now().strftime("%B%Y")

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
            "subtotal": add_harga * add_qty
        })

    # Kirim ke Webhook
    webhook_url = st.session_state.get("webhook_url", WEBHOOK_URL_DEFAULT)
    if webhook_url and "http" in webhook_url:
        payload = {
            "departemen": dept_code,
            "periode": periode_sec,
            "nama_barang": add_nama,
            "satuan": add_satuan,
            "harga": add_harga,
            "qty": add_qty,
            "subtotal": add_harga * add_qty
        }
        try:
            requests.post(webhook_url, json=payload, timeout=3)
        except:
            pass
            
    # Bersihkan Query Parameter setelah ditambahkan
    st.query_params.clear()
    st.rerun()

# ==========================================
# 1. LOGIN
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
# 2. ADMIN PANEL
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
# 3. STAFF CATALOG (MODERN DESIGN & STICKY SEARCH)
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

            # Clean data harga
            df_barang['Harga_Clean'] = df_barang['Harga'].apply(
                lambda x: float(re.sub(r'[^0-9]', '', str(x))) if pd.notnull(x) else 0.0
            )

            # ------------------------------------------------------------------
            # 1. KOLOM PENCARIAN STATIS / STICKY 
            # ------------------------------------------------------------------
            search_query = st.text_input(
                "🔍 Cari Nama Barang:", 
                placeholder="⚡ Ketik nama barang... (Filter otomatis & instan)",
                key="sticky_search_input"
            )

            # Filter data frame secara langsung (Dynamic Live Search)
            if search_query:
                filtered_df = df_barang[df_barang['Nama Barang'].astype(str).str.contains(search_query, case=False, na=False)].copy()
            else:
                filtered_df = df_barang.copy()

            # Tambahkan kolom kontrol untuk tabel interaktif
            filtered_df.insert(0, 'Pilih', False)
            filtered_df['Jumlah (Qty)'] = 1

            # ------------------------------------------------------------------
            # 2. TABEL BARANG MODERN (DATA EDITOR WITH CUSTOM CONFIG)
            # ------------------------------------------------------------------
            st.caption(f"📊 Menampilkan **{len(filtered_df)}** barang tersedia.")
            
            # Form UI & Data Editor Modern
            with st.form("catalog_form"):
                edited_df = st.data_editor(
                    filtered_df[['Pilih', 'Nama Barang', 'Satuan', 'Harga_Clean', 'Jumlah (Qty)']],
                    column_config={
                        "Pilih": st.column_config.CheckboxColumn(
                            "🛒 Pilih", 
                            help="Centang untuk menambah ke keranjang",
                            default=False
                        ),
                        "Nama Barang": st.column_config.TextColumn(
                            "📦 Nama Barang", 
                            disabled=True
                        ),
                        "Satuan": st.column_config.TextColumn(
                            "🏷️ Satuan", 
                            disabled=True
                        ),
                        "Harga_Clean": st.column_config.NumberColumn(
                            "💰 Harga Unit", 
                            format="Rp %'d", 
                            disabled=True
                        ),
                        "Jumlah (Qty)": st.column_config.NumberColumn(
                            "🔢 Qty", 
                            min_value=1, 
                            step=1, 
                            required=True
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=360,
                    key="catalog_editor"
                )

                # Tombol Aksi Modern yang Menyatu dengan Tabel
                submit_button = st.form_submit_button("➕ Masukkan Barang Terpilih ke Keranjang", type="primary", use_container_width=True)

            # ------------------------------------------------------------------
            # 3. LOGIKA EKSEKUSI TAMBAH KE KERANJANG
            # ------------------------------------------------------------------
            if submit_button:
                items_to_add = edited_df[edited_df['Pilih'] == True]
                
                if not items_to_add.empty:
                    dept_code = st.session_state.role.replace(" ", "") if st.session_state.role else "General"
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

                        # Webhook
                        if webhook_url and "http" in webhook_url:
                            payload = {
                                "departemen": dept_code,
                                "periode": periode_sec,
                                "nama_barang": add_nama,
                                "satuan": add_satuan,
                                "harga": add_harga,
                                "qty": add_qty,
                                "subtotal": add_subtotal
                            }
                            try:
                                requests.post(webhook_url, json=payload, timeout=3)
                            except:
                                pass

                    st.toast(f"✅ Berhasil menambah {len(items_to_add)} barang ke keranjang!", icon="🛒")
                    st.rerun()
                else:
                    st.warning("⚠️ Silakan centang minimal satu barang pada kolom 'Pilih' terlebih dahulu.")

            # ==========================================
            # TABEL KERANJANG BELANJA
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

                if st.button("🔴 Kosongkan Semua Keranjang", key="clear_all_cart"):
                    st.session_state.keranjang = []
                    st.rerun()

            else:
                st.info("Keranjang masih kosong. Pilih barang pada tabel di atas untuk menambahkan.")

        except Exception as e:
            st.error(f"Gagal membaca database. Error: {e}")
    else:
        st.info("👈 Silakan atur link Google Sheet terlebih dahulu.")
