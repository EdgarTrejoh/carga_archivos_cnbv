import os
import requests
import streamlit as st
import urllib3

# === CONFIGURACIÓN ===
OUT_DIR = "./descargas_cnbv"

# Desactivar advertencias de certificados inseguros (necesario para algunos sitios gob)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_file(year, month):
    """
    Descarga el archivo desde la URL configurada en st.secrets.
    """
    # 1. Asegurar que la carpeta de destino existe
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR, exist_ok=True)

    # 2. Obtener URL de secretos y formatear
    try:
        base_url = st.secrets["BASE_URL"]
        # Asegúrate de que los nombres de los placeholders coincidan con tu secreto
        download_url = base_url.format(year=year, month=month)
    except KeyError:
        raise Exception("Error: No se encontró 'BASE_URL' en .streamlit/secrets.toml")
    except IndexError:
        raise Exception("Error: La URL en secrets no tiene el formato correcto {year} o {month}")

    file_name = f"cnbv_boletin_banca_multiple_{year:04d}_{month:02d}.xlsx"
    out_path = os.path.join(OUT_DIR, file_name)

    # 3. Headers más completos (imitan a un navegador real)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    }

    try:
        # Usamos un timeout razonable y verify=False por si el sitio tiene certificados expirados
        response = requests.get(download_url, headers=headers, timeout=60, stream=True, verify=False)
        
        # Esto lanzará un error si la respuesta es 404, 403, 500, etc.
        response.raise_for_status()

        # 4. Escritura del archivo
        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
        
        return out_path

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise Exception(f"Archivo no encontrado para {month}/{year}. Verifica si el periodo ya fue publicado.")
        else:
            raise Exception(f"Error HTTP: {e}")
    except requests.exceptions.ConnectionError:
        raise Exception("Error de conexión: No se pudo conectar al servidor de la CNBV.")
    except Exception as e:
        raise Exception(f"Ocurrió un error inesperado: {str(e)}")