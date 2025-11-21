import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime

# ==========================================
# 1. KONFIGURASI APLIKASI
# ==========================================

# --- Setel Halaman ---
st.set_page_config(
    page_title="Juragan Jus Online", 
    layout="wide", 
    page_icon="🥤"
)

st.title("🥤 Juragan Jus (Cloud)")

# --- Inisialisasi Model AI (Memanggil API Key dari Streamlit Secrets) ---
try:
    # Mengambil key dari konfigurasi rahasia Streamlit Cloud
    API_KEY = st.secrets["AIzaSyAd1RY9jxfKUuV9IX6Og2tpck2yWPz8dnA"]
    genai.configure(api_key=API_KEY)
    # Menggunakan Gemini 2.5 Flash: Model tercepat dan stabil saat ini
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    # Error jika API Key belum disetel di Streamlit Cloud
    st.error("⚠️ Error: API Key belum disetel di Streamlit Secrets! Cek Tab Laporan AI.")
    # Set model ke None agar program tidak crash
    model = None 

# ==========================================
# 2. DATA (Penyimpanan Sesi Sementara)
# ==========================================
# Menggunakan Session State karena ini adalah hosting gratis.
# PENTING: Data akan hilang jika server mati (tidak dibuka dalam waktu lama)!

if 'order' not in st.session_state:
    st.session_state.order = pd.DataFrame(columns=["Tanggal", "Pemesan", "Menu", "Qty", "Harga", "Status_Bayar"])
if 'belanja' not in st.session_state:
    st.session_state.belanja = pd.DataFrame(columns=["Tanggal", "Item", "Biaya"])

# ==========================================
# 3. TAMPILAN DAN FUNGSI
# ==========================================
tab1, tab2, tab3 = st.tabs(["📝 Order & Kasir", "🛒 Catat Belanja", "💰 Laporan AI"])

# --- TAB 1: ORDER & KASIR ---
with tab1:
    st.subheader("Input Pesanan Baru")
    with st.form("form_order"):
        col_input_1, col_input_2 = st.columns(2)
        
        with col_input_1:
            nama = st.text_input("Nama Pemesan")
            menu = st.selectbox("Menu", ["Jus Mangga", "Jus Alpukat", "Jus Naga", "Custom"])
            
        with col_input_2:
            qty = st.number_input("Qty", 1, 100, 1)
            harga = st.number_input("Total Harga (Rp)", 0, 1000000, 15000, step=1000)
            status_bayar = st.radio("Status Bayar", ["Lunas", "Bon"], horizontal=True)
            
        if st.form_submit_button("Simpan Pesanan"):
            new_data = {
                "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                "Pemesan": nama, 
                "Menu": menu, 
                "Qty": qty, 
                "Harga": harga, 
                "Status_Bayar": status_bayar
            }
            # Menambah data ke session state
            st.session_state.order = pd.concat([st.session_state.order, pd.DataFrame([new_data])], ignore_index=True)
            st.success(f"Pesanan {nama} tersimpan!")
            st.rerun()
            
    st.markdown("---")
    st.subheader("Daftar Pesanan Saat Ini")
    
    # Menampilkan tabel pesanan (Editable)
    st.info("Tips: Anda bisa edit kolom 'Status Bayar' langsung di tabel, lalu klik 'Simpan Perubahan'.")
    edited_order_df = st.data_editor(
        st.session_state.order,
        column_config={
            "Harga": st.column_config.NumberColumn("Harga (Rp)", format="Rp %d"),
            "Status_Bayar": st.column_config.SelectboxColumn("Status Bayar", options=["Lunas", "Bon"], required=True)
        },
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Simpan Perubahan Tabel Order"):
        st.session_state.order = edited_order_df
        st.toast("Tabel Order diperbarui!", icon="✅")

# --- TAB 2: CATAT BELANJA ---
with tab2:
    st.subheader("Catat Pengeluaran Modal")
    with st.form("form_belanja"):
        item = st.text_input("Beli Apa? (Misal: 1kg Mangga, Gelas Plastik)")
        biaya = st.number_input("Total Bayar (Rp)", min_value=0, step=5000)
        
        if st.form_submit_button("Catat Modal"):
            new_b = {
                "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                "Item": item, 
                "Biaya": biaya
            }
            st.session_state.belanja = pd.concat([st.session_state.belanja, pd.DataFrame([new_b])], ignore_index=True)
            st.success("Modal berhasil dicatat!")
            st.rerun()
            
    st.markdown("---")
    st.subheader("Riwayat Belanja")
    edited_belanja_df = st.data_editor(
        st.session_state.belanja,
        column_config={"Biaya": st.column_config.NumberColumn("Biaya (Rp)", format="Rp %d")},
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Simpan Perubahan Tabel Belanja"):
        st.session_state.belanja = edited_belanja_df
        st.toast("Tabel Belanja diperbarui!", icon="✅")


# --- TAB 3: LAPORAN AI ---
with tab3:
    st.subheader("Ringkasan Keuangan")
    
    # Kalkulasi Keuangan
    omzet = st.session_state.order['Harga'].sum() if not st.session_state.order.empty else 0
    cash_in = st.session_state.order[st.session_state.order['Status_Bayar'] == 'Lunas']['Harga'].sum() if not st.session_state.order.empty else 0
    modal = st.session_state.belanja['Biaya'].sum() if not st.session_state.belanja.empty else 0
    piutang = omzet - cash_in
    profit = cash_in - modal

    c1, c2, c3 = st.columns(3)
    c1.metric("Modal Keluar", f"Rp {modal:,.0f}")
    c2.metric("Uang Cash Masuk", f"Rp {cash_in:,.0f}")
    c3.metric("Profit Bersih", f"Rp {profit:,.0f}", delta="Untung" if profit > 0 else "Minus")

    if piutang > 0:
        st.warning(f"⚠️ Ada piutang (Bon) sebesar **Rp {piutang:,.0f}** belum tertagih!")

    st.markdown("---")
    
    # Fitur Tanya AI
    st.subheader("🤖 Tanya Asisten Bisnis (Gemini 2.5 Flash)")
    
    if model is None:
        st.warning("Silakan atur API Key di Streamlit Secrets (Menu Settings -> Secrets) agar fitur AI berfungsi.")
    else:
        tanya = st.text_area("Konsultasi (Contoh: Apakah stok alpukat sudah cukup untuk omzet ini?)")
        
        if st.button("Kirim ke AI"):
            with st.spinner("AI sedang menganalisa data..."):
                # Menyusun data untuk konteks AI
                data_ringkas = f"""
                DATA KEUANGAN: Modal: Rp {modal}, Cash Masuk: Rp {cash_in}, Profit: Rp {profit}, Piutang: Rp {piutang}.
                RIWAYAT ORDER: {st.session_state.order.to_string()}
                RIWAYAT BELANJA: {st.session_state.belanja.to_string()}
                """
                
                prompt = f"""
                Anda adalah konsultan bisnis minuman yang santai dan cerdas.
                Analisa data berikut:
                {data_ringkas}
                
                Pertanyaan User: {tanya}
                
                Jawab dengan ringkas (maksimal 5 paragraf), praktis, dan bahasa yang membumi.
                """
                try:
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Gagal koneksi AI. Cek apakah API Key Anda benar atau kuota habis. Error: {e}")

# ==========================================
# 4. DOWNLOAD DATA (Sebagai Backup)
# ==========================================
st.sidebar.markdown("### 📥 Backup Data")

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv_order = convert_df_to_csv(st.session_state.order)
st.sidebar.download_button(
    label="Download Data Order (.csv)",
    data=csv_order,
    file_name='data_order_backup.csv',
    mime='text/csv',
)

csv_belanja = convert_df_to_csv(st.session_state.belanja)
st.sidebar.download_button(
    label="Download Data Belanja (.csv)",
    data=csv_belanja,
    file_name='data_belanja_backup.csv',
    mime='text/csv',
)