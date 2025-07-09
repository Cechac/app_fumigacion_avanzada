
# App avanzada de planificación de fumigación aérea

Esta app permite asignar lotes a aeronaves, planificar rutas diarias según ventanas de aplicación y visualizar resultados.

## Instrucciones
1. Sube un archivo .xlsx con las hojas "Lotes" y "Aeronaves"
2. La app asignará lotes a cada aeronave según cercanía, prioridad y ventana diaria (2.5–3 horas).
3. Se mostrará la tabla de asignación y rutas en el mapa.

## Requisitos
- `streamlit`, `pandas`, `folium`, `scipy`, `openpyxl`
