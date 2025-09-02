import os
import requests
import streamlit as st

# === CONFIGURACIÓN ===
OUT_DIR = "./descargas_cnbv"

# URL base del archivo, ahora se lee desde el archivo de secretos
BASE_URL = st.secrets["BASE_URL"]

def download_file(year, month):
    """
    Función para construir la URL y descargar el archivo.
    Lanza una excepción si la descarga falla.
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
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al descargar el archivo: {e}")
