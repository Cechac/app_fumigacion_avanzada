
import streamlit as st
import pandas as pd
import folium
from folium import PolyLine, Marker
from streamlit_folium import st_folium
from datetime import datetime
import numpy as np
from scipy.spatial.distance import cdist

st.set_page_config(page_title="Fumigación Aérea", layout="wide")
st.title("🚁 Asignación Óptima de Rutas de Fumigación")

archivo = st.file_uploader("Carga el archivo Excel (.xlsx)", type=["xlsx"])
BASE_COORD = (10.869, -74.146)

def asignar_lotes(df_lotes, df_aeronaves):
    df_lotes = df_lotes.copy()
    df_lotes["Fecha_sugerida"] = pd.to_datetime(df_lotes["Fecha_sugerida"])
    df_lotes["Asignado"] = np.nan
    lotes_pendientes = df_lotes.copy()

    for _, aeronave in df_aeronaves.iterrows():
        tiempo_max = aeronave["Horas_max_dia"] * 60
        coord_base = np.array([[BASE_COORD[0], BASE_COORD[1]]])

        lotes_candidatos = lotes_pendientes.copy()
        coords_lotes = lotes_candidatos[["Latitud", "Longitud"]].values
        dists = cdist(coord_base, coords_lotes)[0]
        lotes_candidatos["Distancia"] = dists
        lotes_candidatos = lotes_candidatos.sort_values(by=["Fecha_sugerida", "Distancia"])

        tiempo_usado = 0
        ids_asignados = []

        for _, lote in lotes_candidatos.iterrows():
            duracion = lote["Duracion_estim_min"]
            if tiempo_usado + duracion <= tiempo_max:
                tiempo_usado += duracion
                ids_asignados.append(lote["lote_id"])

        df_lotes.loc[df_lotes["lote_id"].isin(ids_asignados), "Asignado"] = aeronave["aeronave_id"]
        lotes_pendientes = df_lotes[df_lotes["Asignado"].isna()]

    return df_lotes

def mostrar_mapa(df_lotes):
    m = folium.Map(location=BASE_COORD, zoom_start=11)
    colores = ["red", "blue", "green", "orange", "purple", "cadetblue", "darkred", "darkblue", "gray"]
    aeronaves = df_lotes["Asignado"].dropna().unique()

    for idx, aero in enumerate(aeronaves):
        df_a = df_lotes[df_lotes["Asignado"] == aero].sort_values(by="Fecha_sugerida")
        if df_a.empty:
            continue
        puntos = [BASE_COORD] + df_a[["Latitud", "Longitud"]].values.tolist() + [BASE_COORD]
        etiquetas = df_a["lote_id"].tolist()

        # Ruta
        PolyLine(puntos, color=colores[idx % len(colores)], weight=3).add_to(m)

        # Marcadores
        for coord, label in zip(df_a[["Latitud", "Longitud"]].values, etiquetas):
            Marker(
                location=coord,
                popup=f"Lote {label} - Aeronave {aero}",
                tooltip=label,
                icon=folium.Icon(color=colores[idx % len(colores)])
            ).add_to(m)

    Marker(BASE_COORD, tooltip="Base", icon=folium.Icon(color="black")).add_to(m)
    return st_folium(m, width=700, height=500)

if archivo:
    try:
        df_lotes = pd.read_excel(archivo, sheet_name="Lotes")
        df_aeronaves = pd.read_excel(archivo, sheet_name="Aeronaves")
        st.success("Datos cargados correctamente.")

        df_asignado = asignar_lotes(df_lotes, df_aeronaves)
        total_asignados = df_asignado["Asignado"].notna().sum()
        st.markdown(f"### ✅ Lotes asignados: {total_asignados} / {len(df_asignado)}")

        st.subheader("Tabla de asignación")
        st.dataframe(df_asignado[["lote_id", "Asignado", "Fecha_sugerida", "Duracion_estim_min"]])

        if total_asignados > 0:
            st.subheader("🗺️ Mapa con rutas por aeronave")
            mostrar_mapa(df_asignado)
        else:
            st.warning("Ningún lote fue asignado. Verifica las duraciones o capacidad de las aeronaves.")
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Por favor, sube un archivo Excel para comenzar.")
