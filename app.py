
import streamlit as st
import pandas as pd
import folium
from folium import PolyLine, Marker
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np
from scipy.spatial.distance import cdist

st.set_page_config(page_title="Planificación Fumigación Aérea", layout="wide")
st.title("🚁 Rutas Óptimas de Fumigación Aérea por Aeronave y Día")

archivo = st.file_uploader("Carga el archivo de datos preparado (.xlsx)", type=["xlsx"])

BASE_COORD = (10.869, -74.146)

def asignar_lotes(df_lotes, df_aeronaves):
    # Copiar y convertir fechas
    df = df_lotes.copy()
    df["Fecha_sugerida"] = pd.to_datetime(df["Fecha_sugerida"])
    df["Dia_semana"] = df["Fecha_sugerida"].dt.day_name()

    plan = []

    for _, aeronave in df_aeronaves.iterrows():
        horas_disponibles = aeronave["Horas_max_dia"]
        minutos_disponibles = horas_disponibles * 60
        coord_base = np.array([[BASE_COORD[0], BASE_COORD[1]]])

        # Calcular distancias desde base a todos los lotes
        coord_lotes = df[["Latitud", "Longitud"]].values
        distancias = cdist(coord_base, coord_lotes)[0]
        df["Dist_base"] = distancias

        # Ordenar por distancia y prioridad
        df_sorted = df.sort_values(by=["Fecha_sugerida", "Dist_base", "prioridad"], ascending=[True, True, False])

        total_min = 0
        asignados = []
        for _, lote in df_sorted.iterrows():
            duracion = lote["Duracion_estim_min"]
            if (total_min + duracion) <= minutos_disponibles:
                asignados.append(lote["lote_id"])
                total_min += duracion
        df.loc[df["lote_id"].isin(asignados), "Asignado"] = aeronave["aeronave_id"]
        df = df[~df["lote_id"].isin(asignados)]

    return df_lotes.merge(df_lotes[["lote_id"]].merge(df[["lote_id", "Asignado"]], on="lote_id", how="left"), on="lote_id", how="left")

def mostrar_mapa(df_lotes):
    m = folium.Map(location=BASE_COORD, zoom_start=11)
    colores = ["red", "blue", "green", "orange", "purple", "cadetblue", "darkred"]
    aeronaves = df_lotes["Asignado"].dropna().unique()

    for idx, aero in enumerate(aeronaves):
        df_a = df_lotes[df_lotes["Asignado"] == aero].sort_values(by="Fecha_sugerida")
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

        st.subheader("Asignación de Lotes a Aeronaves")
        df_asignado = asignar_lotes(df_lotes, df_aeronaves)
        st.dataframe(df_asignado[["lote_id", "Asignado", "Fecha_sugerida", "Area_ha", "Duracion_estim_min"]])

        st.subheader("Mapa de rutas planificadas")
        mostrar_mapa(df_asignado)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Por favor, sube un archivo Excel para comenzar.")
