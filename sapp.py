import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Ev Bütçesi ve Borç Takibi", layout="wide")

@st.cache_data
def load_and_clean_data():
    # --- GELİR VERİSİ İŞLEME ---
    # Dosyayı önce okuyup başlıkları manuel temizliyoruz
    df_gelir = pd.read_csv("gelir.csv", header=None)
    # "mayıs, haziran..." gibi ayların başladığı satırı bul (Genelde 2. satır)
    # İlk sütunda 'mayıs' olan satırdan itibaren alıyoruz
    start_idx = df_gelir[df_gelir[0].astype(str).str.contains('mayıs|haziran', case=False, na=False)].index[0]
    df_gelir = df_gelir.iloc[start_idx:]
    df_gelir.columns = ["Ay", "Oz", "Performans", "Cift", "Ek", "Temettu", "Kira", "Toplam_Gelir"]
    df_gelir["Toplam_Gelir"] = pd.to_numeric(df_gelir["Toplam_Gelir"], errors='coerce').fillna(0)

    # --- GİDER VERİSİ İŞLEME ---
    # Gider dosyasında 'aylık borç' sütununu içeren satırı bulana kadar tara
    df_gider_raw = pd.read_csv("gider.csv", header=None)
    header_row_idx = df_gider_raw[df_gider_raw.astype(str).apply(lambda x: x.str.contains('aylık borç', case=False)).any(axis=1)].index[0]
    
    df_gider = pd.read_csv("gider.csv", skiprows=header_row_idx + 1)
    # Sütun isimlerini temizle (boşlukları al)
    df_gider.columns = [c.strip() for c in df_gider.columns]
    
    # Sayısal sütunları temizle
    for col in ["aylık borç", "şuank borç"]:
        if col in df_gider.columns:
            df_gider[col] = pd.to_numeric(df_gider[col], errors='coerce').fillna(0)
    
    return df_gelir, df_gider

try:
    df_gelir, df_gider = load_and_clean_data()

    st.title("🏠 Ev Bütçesi Analiz Paneli")
    st.markdown("---")

    # --- HESAPLAMALAR ---
    aylik_toplam_taksit = df_gider["aylık borç"].sum()
    toplam_kalan_borc = df_gider["şuank borç"].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Aylık Toplam Taksit", f"{aylik_toplam_taksit:,.2f} ₺")
    m2.metric("Toplam Kalan Borç", f"{toplam_kalan_borc:,.2f} ₺")
    
    # Ay Seçimi
    ay_listesi = df_gelir["Ay"].dropna().unique().tolist()
    secilen_ay = st.selectbox("Analiz Edilecek Ayı Seçin", ay_listesi)
    
    aylik_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]["Toplam_Gelir"].sum()
    m3.metric(f"{secilen_ay} Toplam Geliri", f"{aylik_gelir:,.2f} ₺")

    st.divider()

    # --- GÖRSELLEŞTİRME ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader(f"📊 {secilen_ay} Nakit Akışı")
        net_kalan = aylik_gelir - aylik_toplam_taksit
        
        plot_df = pd.DataFrame({
            "Tip": ["Gelir", "Kredi Gideri", "Net Kalan"],
            "Miktar": [aylik_gelir, aylik_toplam_taksit, net_kalan]
        })
        fig = px.bar(plot_df, x="Tip", y="Miktar", color="Tip", text_auto='.2s',
                     color_discrete_map={"Gelir": "#00CC96", "Kredi Gideri": "#EF553B", "Net Kalan": "#636EFA"})
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("📑 Kredi Listesi")
        display_df = df_gider[["ihtiyaç kredisi tablosu", "aylık borç", "şuank borç"]].copy()
        display_df.columns = ["Banka/Kredi", "Taksit", "Kalan Borç"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Veri işlenirken bir hata oluştu: {e}")
    st.info("Lütfen CSV dosyalarınızın GitHub'da 'gelir.csv' ve 'gider.csv' adıyla yüklü olduğundan emin olun.")