
import streamlit as st
import pandas as pd
import folium
from folium import PolyLine, Marker
from streamlit_folium import st_folium
from datetime import datetime
import numpy as np
from scipy.spatial.distance import cdist

st.set_page_config(page_title="Fumigación Aérea", layout="wide")
st.title("🚁 Planificación con Múltiples Vuelos por Aeronave")

archivo = st.file_uploader("Carga el archivo Excel (.xlsx)", type=["xlsx"])
BASE_COORD = (10.869, -74.146)
TIEMPO_RECARGA_MIN = 4

def asignar_lotes(df_lotes, df_aeronaves):
    df_lotes = df_lotes.copy()
    df_lotes["Fecha_sugerida"] = pd.to_datetime(df_lotes["Fecha_sugerida"])
    df_lotes["Asignado"] = np.nan
    df_lotes["Vuelo_nro"] = np.nan
    df_lotes["Tiempo_inicio"] = np.nan

    lotes_pendientes = df_lotes.copy()

    for _, aeronave in df_aeronaves.iterrows():
        tiempo_max = aeronave["Horas_max_dia"] * 60
        coord_base = np.array([[BASE_COORD[0], BASE_COORD[1]]])

        vuelos = []
        tiempo_total = 0
        vuelo_actual = 1

        while not lotes_pendientes.empty and tiempo_total < tiempo_max:
            df_candidatos = lotes_pendientes.copy()
            coords = df_candidatos[["Latitud", "Longitud"]].values
            distancias = cdist(coord_base, coords)[0]
            df_candidatos["Distancia"] = distancias
            df_candidatos = df_candidatos.sort_values(by=["Fecha_sugerida", "Distancia"])

            tiempo_vuelo = 0
            asignados = []

            for _, lote in df_candidatos.iterrows():
                duracion = lote["Duracion_estim_min"]
                if tiempo_vuelo + duracion <= (tiempo_max - tiempo_total):
                    tiempo_vuelo += duracion
                    asignados.append({
                        "lote_id": lote["lote_id"],
                        "Asignado": aeronave["aeronave_id"],
                        "Vuelo_nro": vuelo_actual,
                        "Tiempo_inicio": tiempo_total
                    })
                    tiempo_total += duracion

            if asignados:
                tiempo_total += TIEMPO_RECARGA_MIN
                vuelo_actual += 1

                for asignacion in asignados:
                    lote_id = asignacion["lote_id"]
                    df_lotes.loc[df_lotes["lote_id"] == lote_id, "Asignado"] = asignacion["Asignado"]
                    df_lotes.loc[df_lotes["lote_id"] == lote_id, "Vuelo_nro"] = asignacion["Vuelo_nro"]
                    df_lotes.loc[df_lotes["lote_id"] == lote_id, "Tiempo_inicio"] = asignacion["Tiempo_inicio"]

                lotes_pendientes = df_lotes[df_lotes["Asignado"].isna()]
            else:
                break

    return df_lotes

def mostrar_mapa(df_lotes):
    m = folium.Map(location=BASE_COORD, zoom_start=11)
    colores = ["red", "blue", "green", "orange", "purple", "cadetblue", "darkred", "darkblue", "gray"]

    grupos = df_lotes[df_lotes["Asignado"].notna()].groupby(["Asignado", "Vuelo_nro"])

    for idx, ((aeronave, vuelo), df_grupo) in enumerate(grupos):
        puntos = [BASE_COORD] + df_grupo[["Latitud", "Longitud"]].values.tolist() + [BASE_COORD]
        etiquetas = df_grupo["lote_id"].tolist()

        color = colores[int(vuelo) % len(colores)]
        PolyLine(puntos, color=color, weight=3, tooltip=f"{aeronave} - Vuelo {int(vuelo)}").add_to(m)

        for coord, label in zip(df_grupo[["Latitud", "Longitud"]].values, etiquetas):
            Marker(
                location=coord,
                popup=f"Lote {label} - {aeronave} (V{int(vuelo)})",
                tooltip=label,
                icon=folium.Icon(color=color)
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
        total_vuelos = df_asignado["Vuelo_nro"].nunique()
        st.markdown(f"### ✅ Lotes asignados: {total_asignados} / {len(df_asignado)}")
        st.markdown(f"### ✈️ Vuelos realizados: {total_vuelos}")

        st.subheader("Tabla de asignación")
        st.dataframe(df_asignado[["lote_id", "Asignado", "Vuelo_nro", "Tiempo_inicio", "Fecha_sugerida", "Duracion_estim_min"]])

        if total_asignados > 0:
            st.subheader("🗺️ Mapa con rutas por vuelo")
            mostrar_mapa(df_asignado)
        else:
            st.warning("Ningún lote fue asignado. Revisa duraciones o capacidad disponible.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Por favor, sube un archivo Excel para comenzar.")
