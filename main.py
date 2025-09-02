import streamlit as st
import os
import glob
import cnbv_downloader 
from data_processor import process_all_files

# --- Configuración de la página de Streamlit ---
st.set_page_config(
    page_title="Descargador de Boletines de la CNBV",
    page_icon="🤖",
    layout="centered"
)

# Título de la aplicación
st.title('Descargador y Procesador de Boletines CNBV')

# Descripción
st.markdown("""
Esta aplicación te permite descargar los boletines de Banca Múltiple de la CNBV y procesar sus datos.
""")

# --- 1. SECCIÓN DE DESCARGA ---
st.header("1. Descargar Boletines")

# Widgets para seleccionar el año y el mes
col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox(
        "Año",
        list(range(2025, 2018, -1)) # Desde 2025 hasta 2019
    )
with col2:
    selected_month = st.selectbox(
        "Mes",
        list(range(1, 13)),
        format_func=lambda x: f"{x:02d}" # Formato de 2 dígitos (ej. 01, 02)
    )

if st.button('Descargar Boletín', use_container_width=True):
    # Llama a la función de descarga
    with st.spinner(f"Descargando boletín para {selected_month:02d}/{selected_year}..."):
        cnbv_downloader(selected_year, selected_month)
    st.success("¡Descarga completada!")

# --- 2. SECCIÓN DE PROCESAMIENTO ---
st.header("2. Procesar Archivos")

# Checa si hay archivos descargados
download_dir = 'descargas_cnbv'
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

excel_files = glob.glob(os.path.join(download_dir, '*.xlsx'))

if not excel_files:
    st.info("No hay archivos Excel descargados para procesar. Por favor, descarga uno primero.")
else:
    st.markdown(f"**Archivos listos para procesar:**")
    for file in excel_files:
        st.write(f"- {os.path.basename(file)}")
    
    # Botón para procesar los archivos
    if st.button('Procesar Datos', use_container_width=True):
        with st.spinner("Procesando y consolidando datos..."):
            process_all_files(excel_files)
        st.success("¡Procesamiento completado! Revisa la carpeta raíz para los nuevos archivos.")
