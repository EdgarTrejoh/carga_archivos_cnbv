import pandas as pd
import os
import re
from datetime import datetime  # <--- 1. Importación añadida

# --- 1. CONFIGURACIÓN CENTRALIZADA ---
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
    match = re.search(r'(\d{4})_(\d{2})', filename)
    if match:
        year = match.group(1)
        month = match.group(2)
        return f"{year}-{month}-01"
    return None

def extract_data_from_excel(filepath, sheet, usecols, names):
    try:
        df = pd.read_excel(
            filepath,
            sheet_name=sheet,
            header=5,
            usecols=','.join(usecols),
            names=names,
            engine='openpyxl'
        )
        return df
    except Exception as e:
        print(f"Error al procesar la hoja '{sheet}' en el archivo '{filepath}': {e}")
        return None

def clean_dataframe(df):
    sistema_row_mask = df['Entidad'].astype(str).str.contains(r'^Sistema\s+\*/', regex=True, na=False)
    sistema_df = df[sistema_row_mask].copy()

    if not sistema_df.empty:
        sistema_df['Entidad'] = 'Sistema'

    keywords_to_remove = ['CONCEPTO', 'NOTAS', 'TOTAL', 'FUENTE', 'Elaborado por', 'CNBV', 'Sistema']
    df = df[~df['Entidad'].str.contains('|'.join(keywords_to_remove), case=False, na=False)]
    df = df[~sistema_row_mask]

    if not sistema_df.empty:
        df = pd.concat([df, sistema_df], ignore_index=True)
    
    data_columns = [col for col in df.columns if col != 'Entidad' and col != 'Fecha']
    for col in data_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.fillna(0)
    df['Entidad'] = df['Entidad'].astype(str).str.strip()
    return df

def save_consolidated_data(df, output_filename):
    output_dir = "archivos_procesados"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path = os.path.join(output_dir, output_filename)
    df.to_csv(output_path, index=False)
    print(f"✅ Archivo consolidado '{output_filename}' creado exitosamente.")

# --- 3. LÓGICA PRINCIPAL ---

def process_all_files(filenames):
    """
    Procesa archivos y genera CSVs con el orden: 
    Fecha, Entidad, CarteraTotal, IMOR, ICOR, PE, periodicidad, timestamp
    """
    # 2. Capturamos la fecha y hora actual para el timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for config_name, config in DATA_CONFIG.items():
        all_dataframes = []
        
        # Definimos el orden de columnas deseado para las hojas tipo 'cartera'
        # Nota: Para 'captacion' o 'resultados' el orden variará según sus nombres
        column_order = ["Fecha", "Entidad"] + [col for col in config['names'] if col != "Entidad"] + ["periodicidad", "timestamp"]

        for file_name in filenames:
            df = extract_data_from_excel(file_name, config['sheet'], config['usecols'], config['names'])
            if df is not None:
                if 'Entidad' in df.columns:
                    df = clean_dataframe(df)

                    # 1. Agregamos la información nueva
                    df['Fecha'] = extract_date_from_filename(file_name)
                    df['periodicidad'] = 'mensual'
                    df['timestamp'] = current_time
                    
                    # 2. Reordenamos las columnas según tu solicitud
                    # Usamos un list comprehension para manejar configuraciones con diferentes nombres de columnas
                    actual_cols = [col for col in column_order if col in df.columns]
                    df = df[actual_cols]
                    
                    all_dataframes.append(df)
                else:
                    print(f"❌ La hoja '{config['sheet']}' del archivo '{file_name}' no contiene 'Entidad'.")
        
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            output_filename = f"consolidated_data_{config_name}.csv"
            save_consolidated_data(combined_df, output_filename)
        else:
            print(f"No se encontraron datos para la configuración '{config_name}'.")
        

# Ejemplo de uso:
if __name__ == "__main__":
    folder = "descargas_cnbv"
    if os.path.exists(folder):
        file_list = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".xlsx")]
        process_all_files(file_list)