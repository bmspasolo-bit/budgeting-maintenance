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
# 3. HALAMAN UTAMA STAFF (LIVE SEARCH + ROBOTO + INSTANT CLICK ACTION)
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

            # PERSIAPAN DATA BARANG
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
            dept_code = st.session_state.role.replace(" ", "")

            # HTML & JAVASCRIPT INSTANT SEARCH ALA WA WEB (FONT ROBOTO + INLINE QTY & TAMBAH)
            live_search_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
            <style>
                * {{
                    font-family: 'Roboto', sans-serif !important;
                    box-sizing: border-box;
                }}
                body {{
                    background-color: #0f172a;
                    color: #ffffff;
                    margin: 0;
                    padding: 0;
                }}
                .search-box {{
                    width: 100%;
                    padding: 12px 16px;
                    background-color: #1e293b;
                    border: 1px solid #3b82f6;
                    border-radius: 8px;
                    color: #ffffff;
                    font-size: 15px;
                    outline: none;
                    margin-bottom: 12px;
                }}
                .search-box::placeholder {{
                    color: #94a3b8;
                }}
                .item-card {{
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-left: 4px solid #3b82f6;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 8px;
                    cursor: pointer;
                    transition: background 0.2s;
                }}
                .item-card:hover {{
                    background-color: #334155;
                }}
                .item-title {{
                    font-size: 15px;
                    font-weight: 700;
                    color: #60a5fa;
                }}
                .item-price {{
                    font-size: 14px;
                    font-weight: 700;
                    color: #34d399;
                    margin-top: 2px;
                }}
                .item-unit {{
                    color: #94a3b8;
                    font-weight: normal;
                    font-size: 12px;
                }}
                .action-panel {{
                    display: none;
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px dashed #475569;
                }}
                .qty-input {{
                    width: 80px;
                    padding: 8px;
                    background-color: #0f172a;
                    border: 1px solid #475569;
                    color: #ffffff;
                    border-radius: 6px;
                    font-weight: bold;
                    text-align: center;
                }}
                .add-btn {{
                    background-color: #2563eb;
                    color: #ffffff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 700;
                    cursor: pointer;
                    margin-left: 8px;
                }}
                .add-btn:hover {{
                    background-color: #1d4ed8;
                }}
                .status-msg {{
                    font-size: 12px;
                    color: #34d399;
                    margin-top: 6px;
                    display: none;
                }}
            </style>
            </head>
            <body>

            <input type="text" id="searchInput" oninput="filterBarang()" placeholder="🔍 Ketik nama barang... (langsung muncul)" class="search-box" autofocus />
            <div id="barangContainer"></div>

            <script>
                const dataBarang = {json_barang};
                const webhookUrl = "{webhook_url}";
                const deptCode = "{dept_code}";
                const periodeSec = "{periode_sekarang}";

                function toggleAction(idx) {{
                    const panel = document.getElementById('panel-' + idx);
                    if (panel.style.display === 'flex') {{
                        panel.style.display = 'none';
                    }} else {{
                        // Sembunyikan panel lain
                        document.querySelectorAll('.action-panel').forEach(el => el.style.display = 'none');
                        panel.style.display = 'flex';
                    }}
                }}

                function filterBarang() {{
                    const query = document.getElementById('searchInput').value.toLowerCase().trim();
                    const container = document.getElementById('barangContainer');
                    container.innerHTML = '';

                    const filtered = dataBarang.filter(item => 
                        item.nama.toLowerCase().includes(query)
                    );

                    if (filtered.length === 0) {{
                        container.innerHTML = '<div style="color: #ef4444; padding: 10px; font-size: 14px;">Barang tidak ditemukan...</div>';
                        return;
                    }}

                    const itemsToDisplay = filtered.slice(0, 25);

                    itemsToDisplay.forEach((item, index) => {{
                        const formattedPrice = new Intl.NumberFormat('id-ID', {{ style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }}).format(item.harga);
                        
                        const itemHtml = `
                            <div class="item-card" onclick="toggleAction(${{index}})">
                                <div class="item-title">📌 ${{item.nama}}</div>
                                <div class="item-price">${{formattedPrice}} <span class="item-unit">/ ${{item.satuan}}</span></div>
                                
                                <div class="action-panel" id="panel-${{index}}" onclick="event.stopPropagation()">
                                    <input type="number" id="qty-${{index}}" value="1" min="1" class="qty-input" placeholder="Qty" />
                                    <button class="add-btn" onclick="tambahBarang('${{item.nama}}', '${{item.satuan}}', ${{item.harga}}, ${{index}})">➕ Tambah</button>
                                </div>
                                <div class="status-msg" id="status-${{index}}"></div>
                            </div>
                        `;
                        container.innerHTML += itemHtml;
                    }});
                }}

                function tambahBarang(nama, satuan, harga, idx) {{
                    const qtyInput = document.getElementById('qty-' + idx);
                    const qtyVal = parseInt(qtyInput.value) || 1;
                    const subtotal = harga * qtyVal;
                    const statusEl = document.getElementById('status-' + idx);

                    statusEl.style.display = 'block';
                    statusEl.style.color = '#38bdf8';
                    statusEl.innerText = '⏳ Menyimpan...';

                    const payload = {{
                        departemen: deptCode,
                        periode: periodeSec,
                        nama_barang: nama,
                        satuan: satuan,
                        harga: harga,
                        qty: qtyVal,
                        subtotal: subtotal
                    }};

                    if (webhookUrl && webhookUrl.includes('http')) {{
                        fetch(webhookUrl, {{
                            method: 'POST',
                            mode: 'no-cors',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify(payload)
                        }}).then(() => {{
                            statusEl.style.color = '#34d399';
                            statusEl.innerText = '✅ Tersimpan! (' + qtyVal + ' ' + satuan + ')';
                        }}).catch(err => {{
                            statusEl.style.color = '#ef4444';
                            statusEl.innerText = '❌ Gagal mengirim data.';
                        }});
                    }} else {{
                        statusEl.style.color = '#34d399';
                        statusEl.innerText = '✅ Berhasil ditambahkan!';
                    }}
                }}

                filterBarang();
            </script>
            </body>
            </html>
            """
            
            # Render komponen live search
            st.components.v1.html(live_search_html, height=520, scrolling=True)

        except Exception as e:
            st.error(f"Gagal membaca database. Error: {e}")
    else:
        st.info("👈 Silakan atur link Google Sheet terlebih dahulu.")
