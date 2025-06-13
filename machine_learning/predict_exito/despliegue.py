import pandas as pd
import joblib
import streamlit as st
import requests
import os
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import folium
import geopandas as gpd

# --- CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Predicción de Éxito", layout="wide")

# --- PALETA DE COLORES ---
COLOR_BG = "#001027"
COLOR_1 = "#6A3937"
COLOR_2 = "#706563"
COLOR_3 = "#748386"
COLOR_ACCENT = "#9DC7C8"

# --- DESCARGA Y CARGA DE DATOS/MODELO ---
URL_MODELO = "https://storage.googleapis.com/ml_exito/modelo_exito.pkl"
URL_DATOS = "https://storage.googleapis.com/ml_exito/modelo.csv"

modelo_path = "modelo_exito.pkl"
if not os.path.exists(modelo_path):
    r = requests.get(URL_MODELO)
    if r.status_code == 200:
        with open(modelo_path, "wb") as f:
            f.write(r.content)
    else:
        st.error("Error al descargar el modelo.")

# Cargar modelo y dataset
xgb = joblib.load(modelo_path)
modelo = pd.read_csv(URL_DATOS).drop_duplicates(subset="business_id")

# --- VARIABLES DEL MODELO ---
features_usuario = [
    'GoodForKids', 'Caters', 'meal_dinner', 'meal_lunch',
    'dietary_gluten_free', 'OutdoorSeating', 'Alcohol',
    'meal_breakfast', 'bestnight_friday', 'music_dj'
]

features_condado = [
    'latitude', 'longitude','locales_en_condado','prom_resenas_condado',
    'mujeres_total','porc_positivas_condado','hombres_total',
    'edad_media', 'locales_por_1000hab','poblacion_total', 'prom_stars_condado'
]

features_totales = features_condado + features_usuario

# --- TÍTULO PRINCIPAL ---
st.markdown(f"<h1 style='color:{COLOR_ACCENT}'> Recomendación de Condados con Mayor Éxito</h1>", unsafe_allow_html=True)

# --- CALCULAR TOP 3 CONDADOS ---
X_modelo = modelo[xgb.get_booster().feature_names].fillna(0)
modelo['proba_exito'] = xgb.predict_proba(X_modelo)[:, 1]
top3 = modelo.sort_values(by='proba_exito', ascending=False) \
             .drop_duplicates(subset='county')[['county', 'proba_exito']].head(3).reset_index(drop=True)

# --- TABLA Y GRÁFICO DE TOP 3 ---
col1, col2 = st.columns([1.2, 0.8])
with col1:
    st.subheader("Top 3 Condados")
    st.dataframe(
        top3.rename(columns={"county": "Condado", "proba_exito": "Probabilidad de Éxito"})
        .style.format({"Probabilidad de Éxito": "{:.2%}"}),
        use_container_width=True
    )

with col2:
    st.subheader("Probabilidad de exito")
    fig, ax = plt.subplots()
    ax.bar(top3["county"], top3["proba_exito"] * 100, color=COLOR_ACCENT)
    ax.set_ylabel("Probabilidad de Éxito (%)", color=COLOR_2)
    ax.set_xlabel("Condado", color=COLOR_2)
    ax.tick_params(axis='x', colors=COLOR_1)
    ax.tick_params(axis='y', colors=COLOR_1)
    fig.patch.set_facecolor("white")
    st.pyplot(fig)

# ----------------------- PARTE 2: SIMULACIÓN + MAPA -----------------------
st.markdown("---")
st.markdown(f"<h2 style='color:{COLOR_ACCENT}'> Simulá tu Restaurante</h2>", unsafe_allow_html=True)

# --- LAYOUT A DOS COLUMNAS ---
col_sim, col_mapa = st.columns([1.2, 1.1])

with col_sim:
    condado_default = top3.iloc[0]['county']
    condado_seleccionado = st.selectbox("📍 Seleccioná un condado:", sorted(modelo['county'].unique()), index=list(modelo['county'].unique()).index(condado_default))
    datos_condado = modelo[modelo['county'] == condado_seleccionado][features_condado].mean()

    st.subheader("Características del Restaurante:")
    input_usuario = {}
    for f in features_usuario:
        label = f.replace("_", " ").capitalize()
        input_usuario[f] = int(st.checkbox(label, value=False))

    input_final = pd.DataFrame({**datos_condado.to_dict(), **input_usuario}, index=[0])

    # Asegurar columnas
    for col in xgb.get_booster().feature_names:
        if col not in input_final.columns:
            input_final[col] = 0

    input_final = input_final[xgb.get_booster().feature_names]

    # --- PREDICCIÓN ---
    proba = xgb.predict_proba(input_final)[0][1]

    # --- RESULTADO FINAL ---
    st.markdown(
        f"<div style='background-color:{COLOR_ACCENT};padding:1em;border-radius:8px;color:#001027;font-size:20px'>"
        f"🌟 En el condado de <strong>{condado_seleccionado}</strong>, la probabilidad de éxito estimada es: <strong>{proba*100:.2f}%</strong>"
        f"</div>",
        unsafe_allow_html=True
    )

with col_mapa:
    st.subheader("🗺 Mapa del Condado Seleccionado")

    # Descargar geojson
    GEOJSON_URL = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/california-counties.geojson"
    geo = gpd.read_file(GEOJSON_URL)

    for col in geo.columns:
        if pd.api.types.is_datetime64_any_dtype(geo[col]):
            geo[col] = geo[col].astype(str)

    m = folium.Map(location=[datos_condado['latitude'], datos_condado['longitude']], zoom_start=8)

    # Base
    folium.GeoJson(
        geo,
        name="condados",
        style_function=lambda feature: {
            "fillColor": "#ccc",
            "color": "white",
            "weight": 1,
            "fillOpacity": 0.1,
        }
    ).add_to(m)

    # Condado actual
    highlight = geo[geo['name'].str.lower() == condado_seleccionado.lower()]
    if not highlight.empty:
        folium.GeoJson(
            highlight,
            name="seleccionado",
            style_function=lambda feature: {
                "fillColor": COLOR_ACCENT,
                "color": COLOR_1,
                "weight": 3,
                "fillOpacity": 0.6,
            },
            tooltip=condado_seleccionado
        ).add_to(m)

    # Marker
    folium.Marker(
        location=[datos_condado['latitude'], datos_condado['longitude']],
        popup=f"{condado_seleccionado}: {proba*100:.2f}%",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    st_folium(m, width=500, height=450)