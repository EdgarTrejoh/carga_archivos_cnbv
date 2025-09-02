import streamlit as st
import os
import sys
import requests
from datetime import datetime

# === CONFIGURACIÓN ===
OUT_DIR = "./descargas_cnbv"

# Diccionario para mapear los nombres de los meses a sus números
MONTHS_ES = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12,
}

# URL base del archivo. Notar el patrón de año y mes
# Ejemplo: https://portafolioinfo.cnbv.gob.mx/_layouts/15/download.aspx?SourceUrl=/PortafolioInfo/CNBV.gob.mx/PortafolioInformacion/BE_BM_202506.xlsx
BASE_URL = "https://portafolioinfo.cnbv.gob.mx/_layouts/15/download.aspx?SourceUrl=https://portafolioinfo.cnbv.gob.mx/PortafolioInformacion/BE%20BM%20{year:04d}{month:02d}.xlsx"

def download_file(year, month):
    """
    Función para construir la URL y descargar el archivo.
    """
    os.makedirs(OUT_DIR, exist_ok=True)
    requests.packages.urllib3.disable_warnings()

    download_url = BASE_URL.format(year=year, month=month)
    file_name = f"cnbv_boletin_banca_multiple_{year:04d}_{month:02d}.xlsx"
    out_path = os.path.join(OUT_DIR, file_name)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(download_url, headers=headers, timeout=120, stream=True, verify=False)
        response.raise_for_status()

        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
        
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        st.success(f"✅ ¡Descarga completa! Archivo guardado en **{out_path}** ({size_mb:.2f} MB)")
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error al descargar el archivo. Verifique que la URL sea correcta o si la conexión falla: {e}")
        st.info("Es posible que no haya un boletín para el mes y año seleccionados. Por favor, intente con otra fecha.")

def main():
    """
    Función principal de la interfaz de Streamlit.
    """
    st.title("Descargador de Boletines de la CNBV")
    st.markdown("Selecciona el año y el mes del boletín de Banca Múltiple que deseas descargar.")

    # Obtener el año y mes actuales para los valores por defecto
    current_year = datetime.now().year
    current_month_name = list(MONTHS_ES.keys())[datetime.now().month - 1]

    # Widgets para la selección del usuario
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input("Año", min_value=2010, max_value=current_year, value=current_year, step=1)
    
    with col2:
        selected_month_name = st.selectbox("Mes", options=list(MONTHS_ES.keys()), index=list(MONTHS_ES.keys()).index(current_month_name))
        selected_month = MONTHS_ES[selected_month_name]

    st.markdown("---")

    if st.button("Descargar Boletín"):
        st.info(f"Iniciando descarga del boletín de {selected_month_name} de {selected_year}...")
        download_file(selected_year, selected_month)

if __name__ == "__main__":
    main()
