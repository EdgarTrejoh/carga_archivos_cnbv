import pandas as pd
import os
import re

# --- 1. CONFIGURACIÓN CENTRALIZADA ---
# Define aquí todas las hojas y columnas que quieres extraer.
# Si necesitas procesar una nueva hoja, simplemente agrega una entrada a este diccionario.
DATA_CONFIG = {
    'vivienda': {
        'sheet': 'CCV',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
    'cartera': {
        'sheet': 'CCT',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
    'captacion': {
        'sheet': 'CaptRec',
        'usecols': ['B', 'E', 'H', 'K', 'N', 'Q', 'T', 'W'],
        'names': ["Entidad", "CaptacionTotal", "DepositoExigInmediata", "DepositoPlazoPG", "DepositoPlazoMV", "TitulosCredito", "PrestamosInterBanc", "CuentaGlobalCapt"],
    },
    'tarjeta_credito': {
        'sheet': 'CCCTC',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
    'nomina': {
        'sheet': 'CCCN',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
    'personales': {
        'sheet': 'CCCnrP',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
    'empresariales': {
        'sheet': 'CCE',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
    'resultados': {
        'sheet': 'Pm2',
        'usecols': ['B', 'G', 'M', 'S', 'Y', 'AE', 'AK'],
        'names': ["Entidad", "ActivoTotal", "Inversiones", "CarteraTotal", "CaptacionTotal", "CapitalContable", "ResultadoNeto"],
    },
    'auto': {
        'sheet': 'CCCAut',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
    'consumo': {
        'sheet': 'CCCT',
        'usecols': ['B', 'E', 'H', 'K', 'N'],
        'names': ["Entidad", "CarteraTotal", "IMOR", "ICOR", "PE"],
    },
}

# --- 2. FUNCIONES GENÉRICAS ---

def extract_date_from_filename(filename):
    """
    Extrae el año y mes del nombre del archivo.
    Ej. 'cnbv_boletin_banca_multiple_2023_01.xlsx' -> ('2023', '01')
    """
    # Expresión regular para encontrar el año y el mes
    match = re.search(r'(\d{4})_(\d{2})', filename)
    if match:
        year = match.group(1)
        month = match.group(2)
        return f"{year}-{month}-01" # Formato YYYY-MM-DD
    return None

def extract_data_from_excel(filepath, sheet, usecols, names):
    """
    Extrae datos de una hoja de Excel específica y retorna un DataFrame de Pandas.
    Args:
        filepath (str): La ruta del archivo Excel.
        sheet (str): El nombre de la hoja a leer.
        usecols (list): Una lista de las columnas a usar.
        names (list): Una lista de los nombres de las columnas.
    Returns:
        pd.DataFrame: Un DataFrame con los datos extraídos.
    """
    try:
        df = pd.read_excel(
            filepath,
            sheet_name=sheet,
            header=4,
            usecols=','.join(usecols),
            # Eliminamos index_col para no causar errores con valores nulos
            names=names,
            engine='openpyxl'
        )
        return df
    except Exception as e:
        print(f"Error al procesar la hoja '{sheet}' en el archivo '{filepath}': {e}")
        return None

def clean_dataframe(df):
    """
    Limpia el DataFrame eliminando filas no deseadas de la columna 'Entidad'
    y reemplazando valores no numéricos en las columnas de datos por cero.
    Args:
        df (pd.DataFrame): El DataFrame a limpiar.
    Returns:
        pd.DataFrame: El DataFrame limpio.
    """
    # 📝 Elimina filas donde 'Entidad' está nulo o vacío
    df = df.dropna(subset=['Entidad']).copy()

    # 📝 Convierte la columna 'Entidad' a tipo string y limpia espacios
    df['Entidad'] = df['Entidad'].astype(str).str.strip()

    # 📝 Elimina las filas que contienen valores no deseados en la columna 'Entidad'
    # Esto manejará encabezados duplicados, notas, y totales
    keywords_to_remove = ['CONCEPTO', 'NOTAS', 'TOTAL', 'FUENTE', 'Elaborado por', 'CNBV', 'Sistema']
    df = df[~df['Entidad'].str.contains('|'.join(keywords_to_remove), case=False, na=False)]
    
    # 💡 Convertimos las columnas de datos a tipo numérico y reemplazamos los
    # valores no numéricos (ahora NaN) por 0.
    data_columns = [col for col in df.columns if col != 'Entidad' and col != 'Fecha']
    for col in data_columns:
        # Convierte a numérico, los valores no numéricos se vuelven NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Reemplazamos todos los valores NaN (que solían ser "n.a." o "-") por 0
    df = df.fillna(0)
    
    return df

def save_to_excel_with_sheets(dataframes_dict, output_filename):
    """
    Guarda múltiples DataFrames en un solo archivo Excel, cada uno en una hoja diferente.
    Args:
        dataframes_dict (dict): Un diccionario donde las claves son los nombres de las hojas
                                y los valores son los DataFrames.
        output_filename (str): El nombre del archivo Excel de salida.
    """
    # 📝 Crea la carpeta si no existe
    output_dir = "archivos_procesados"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 📝 Combina el directorio y el nombre del archivo
    output_path = os.path.join(output_dir, output_filename)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in dataframes_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=True)
    print(f"✅ Archivo '{output_filename}' creado exitosamente en la carpeta '{output_dir}'.")

def save_consolidated_data(df, output_filename):
    """
    Guarda un solo DataFrame consolidado en un archivo CSV.
    Args:
        df (pd.DataFrame): El DataFrame consolidado a guardar.
        output_filename (str): El nombre del archivo CSV de salida.
    """
    output_dir = "archivos_procesados"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, output_filename)
    df.to_csv(output_path, index=False)
    print(f"✅ Archivo consolidado '{output_filename}' creado exitosamente.")


# --- 3. LÓGICA PRINCIPAL ---

def process_all_files(filenames):
    """
    Procesa todos los archivos, extrae los datos y los consolida verticalmente
    agregando una columna de fecha.
    Args:
        filenames (list): Una lista de las rutas de los archivos Excel a procesar.
    """
    for config_name, config in DATA_CONFIG.items():
        all_dataframes = []
        for file_name in filenames:
            df = extract_data_from_excel(file_name, config['sheet'], config['usecols'], config['names'])
            if df is not None:
                if 'Entidad' in df.columns:
                    # 💡 Nueva función de limpieza
                    df = clean_dataframe(df)

                    # 📝 Agrega una columna de fecha al DataFrame antes de apilarlo
                    df['Fecha'] = extract_date_from_filename(file_name)
                    all_dataframes.append(df)
                else:
                    print(f"❌ La hoja '{config['sheet']}' del archivo '{file_name}' no contiene la columna 'Entidad'. Se omitirá.")
        
        if all_dataframes:
            # 📝 Consolida los DataFrames verticalmente
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            
            # Guardamos en un archivo CSV, como lo solicitaste
            output_filename = f"consolidated_data_{config_name}.csv"
            save_consolidated_data(combined_df, output_filename)

        else:
            print(f"No se encontraron datos para la configuración '{config_name}'.")

# Ejemplo de uso:
if __name__ == "__main__":
    # Asegúrate de que los archivos estén en la carpeta correcta
    file_list = [
        os.path.join("descargas_cnbv", "cnbv_boletin_banca_multiple_2023_01.xlsx"),
        os.path.join("descargas_cnbv", "cnbv_boletin_banca_multiple_2023_02.xlsx"),
    ]
    
    process_all_files(file_list)
