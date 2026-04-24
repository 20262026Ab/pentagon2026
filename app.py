import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Ev Bütçesi ve Borç Takibi", layout="wide")

# --- VERİ YÜKLEME ---
@st.cache_data
def load_and_clean_data():
    # Gelir Verisi (İlk satırı atlayıp temizliyoruz)
    df_gelir = pd.read_csv("gelir.csv", skiprows=0)
    df_gelir.columns = ["Ay", "Oz", "Performans", "Cift", "Ek", "Temettu", "Kira", "Toplam_Gelir"]
    
    # Gider/Kredi Verisi
    df_gider = pd.read_csv("gider.csv", skiprows=2) # Başlıklar 3. satırda olduğu için
    
    return df_gelir, df_gider

try:
    df_gelir, df_gider = load_and_clean_data()

    st.title("🏠 Ev Bütçesi Analiz Paneli")
    st.markdown("---")

    # --- HESAPLAMALAR ---
    # Toplam Kredi Yükü (Gider dosyasındaki 'şuank borç' sütunu üzerinden)
    toplam_kalan_borc = df_gider["şuank borç"].sum()
    aylik_toplam_taksit = df_gider["aylık borç"].sum()
    
    # Metrikler
    m1, m2, m3 = st.columns(3)
    m1.metric("Aylık Toplam Kredi Ödemesi", f"{aylik_toplam_taksit:,.2f} ₺")
    m2.metric("Toplam Kalan Borç", f"{toplam_kalan_borc:,.2f} ₺", delta="Bankalara Toplam")
    
    # Mevcut ayın geliri (Örn: Mayıs ayı için veriden çekelim)
    # Not: Dosyandaki Ay isimlerine göre filtreleme yapıyoruz
    secilen_ay = st.selectbox("Analiz Edilecek Ayı Seçin", df_gelir["Ay"].unique())
    aylik_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]["Toplam_Gelir"].values[0]
    
    m3.metric(f"{secilen_ay} Geliri", f"{aylik_gelir:,.2f} ₺")

    st.divider()

    # --- GRAFİKLER VE TABLOLAR ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📊 Nakit Akış Analizi")
        kalan_para = aylik_gelir - aylik_toplam_taksit
        
        fig_data = pd.DataFrame({
            "Kategori": ["Gelir", "Kredi Ödemeleri", "Kalan Net"],
            "Miktar": [aylik_gelir, aylik_toplam_taksit, kalan_para]
        })
        fig = px.bar(fig_data, x="Kategori", y="Miktar", color="Kategori", 
                     text_auto='.2s', title=f"{secilen_ay} Ayı Özeti")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("📑 Kredi Detayları")
        st.dataframe(df_gider[["ihtiyaç kredisi tablosu", "aylık borç", "şuank borç"]].rename(
            columns={"ihtiyaç kredisi tablosu": "Banka/Kredi", "aylık borç": "Taksit", "şuank borç": "Kalan"}
        ))

    # --- BORÇ DAĞILIMI ---
    st.subheader("📉 Kredi Borç Dağılımı")
    fig_pie = px.pie(df_gider, values='şuank borç', names='ihtiyaç kredisi tablosu', hole=.3)
    st.plotly_chart(fig_pie)

except Exception as e:
    st.error(f"Veri okunurken hata oluştu. Lütfen dosya formatını kontrol edin. Hata: {e}")