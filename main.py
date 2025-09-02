import os
import sys
import requests

# === CONFIGURA AQUÍ ===
# Elige el año y el mes que quieres descargar
# Ejemplo: 2024, 6 para junio de 2024
DESIRED_YEAR = 2025
DESIRED_MONTH = 6
# Directorio donde se guardarán los archivos
OUT_DIR = "./descargas_cnbv"

# ----------------------

# URL base del archivo. Notar el patrón de año y mes
# Ejemplo de URL: https://portafolioinfo.cnbv.gob.mx/_layouts/15/download.aspx?SourceUrl=/PortafolioInfo/CNBV.gob.mx/PortafolioInformacion/BE_BM_202506.xlsx
BASE_URL = "https://portafolioinfo.cnbv.gob.mx/_layouts/15/download.aspx?SourceUrl=https://portafolioinfo.cnbv.gob.mx/PortafolioInformacion/BE%20BM%20{year:04d}{month:02d}.xlsx"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Desactiva las advertencias de conexiones no verificadas para que la salida de la terminal esté más limpia.
    requests.packages.urllib3.disable_warnings()

    # Construye la URL completa del archivo usando el año y el mes
    download_url = BASE_URL.format(year=DESIRED_YEAR, month=DESIRED_MONTH)
    
    # Construye el nombre de archivo de salida
    file_name = f"cnbv_boletin_banca_multiple_{DESIRED_YEAR:04d}_{DESIRED_MONTH:02d}.xlsx"
    out_path = os.path.join(OUT_DIR, file_name)

    # Encabezado para simular una solicitud desde un navegador web
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    print(f"Intentando descargar: {download_url}")
    print(f"Guardando en: {out_path}")
    
    try:
        # Usa requests para hacer la descarga directa del archivo, incluyendo el encabezado
        # Se desactiva la verificación SSL con verify=False para evitar problemas de certificado
        response = requests.get(download_url, headers=headers, timeout=120, stream=True, verify=False)
        response.raise_for_status() # Lanza un error si la descarga falla
        
        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
        
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        print(f"✅ Descarga completa. Tamaño: {size_mb:.2f} MB")
        
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo. Verifique que la URL sea correcta o si la conexión falla: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
