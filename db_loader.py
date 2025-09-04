import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text
from io import StringIO
import re

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS (desde secrets.toml) ---
try:
    DB_USER = st.secrets["database"]["db_user"]
    DB_PASSWORD = st.secrets["database"]["db_password"]
    DB_HOST = st.secrets["database"]["db_host"]
    DB_PORT = st.secrets["database"]["db_port"]
    DB_NAME = st.secrets["database"]["db_name"]
except KeyError as e:
    st.error(f"❌ Error: La clave '{e}' no se encontró en su archivo secrets.toml. Asegúrese de que la sección [database] esté configurada correctamente.")
    st.stop()

# --- 2. CONEXIÓN A LA BASE DE DATOS ---
@st.cache_resource
def get_db_connection():
    db_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(db_string)

# --- 3. LÓGICA DE CARGA ---

# Mapeo de archivos CSV a indicadores y columnas de la tabla 'indicador_hechos'
INDICATOR_MAP = {
    'vivienda': {
        'id_indicador': 28,  # Cartera de crédito
        'tipo_credito': 'Vivienda',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'tarjeta_credito': {
        'id_indicador': 28,
        'tipo_credito': 'Tarjeta Crédito',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'nomina': {
        'id_indicador': 28,
        'tipo_credito': 'Nomina',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'personales': {
        'id_indicador': 28,
        'tipo_credito': 'Personales',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'empresariales': {
        'id_indicador': 28,
        'tipo_credito': 'Empresariales',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'resultados': {
        'id_indicador': [24, 25, 26, 28, 27], # Activo, Capital, Resultado, Cartera Total, Captacion
        'cols_map': {'Entidad': 'grupo_banco', 'ActivoTotal': 24, 'CapitalContable': 25, 'ResultadoNeto': 26, 'CarteraTotal': 28, 'CaptacionTotal': 27}
    },
    'auto': {
        'id_indicador': 28,
        'tipo_credito': 'Auto',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'consumo': {
        'id_indicador': 28,
        'tipo_credito': 'Consumo',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'cartera': {
        'id_indicador': 28,
        'tipo_credito': 'Total',
        'cols_map': {'Entidad': 'grupo_banco', 'CarteraTotal': 'valor'}
    },
    'captacion': {
        'id_indicador': 27, # Captación
        'tipo_captacion': ['CtaGlobalCapt', 'DepExigInm', 'DepPlazo', 'Total'],
        'cols_map': {'Entidad': 'grupo_banco'} # Columnas se generarán dinámicamente
    },
    'imor_vivienda': {
        'id_indicador': 29,  # IMOR
        'tipo_credito': 'Vivienda',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
    'imor_tarjeta_credito': {
        'id_indicador': 29,
        'tipo_credito': 'Tarjeta Credito',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
    'imor_nomina': {
        'id_indicador': 29,
        'tipo_credito': 'Nomina',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
    'imor_personales': {
        'id_indicador': 29,
        'tipo_credito': 'Personales',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
    'imor_empresariales': {
        'id_indicador': 29,
        'tipo_credito': 'Empresariales',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
    'imor_auto': {
        'id_indicador': 29,
        'tipo_credito': 'Auto',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
    'imor_consumo': {
        'id_indicador': 29,
        'tipo_credito': 'Consumo',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
    'imor_cartera': {
        'id_indicador': 29,
        'tipo_credito': 'Total',
        'cols_map': {'Entidad': 'grupo_banco', 'IMORTotal': 'valor'}
    },
}

def clean_dataframe(df):
    """Limpia el DataFrame, reemplazando valores no numéricos y convirtiendo columnas."""
    df = df.replace(['n.a.', '-', 'n.d.', 'N.A.', 's.i.', ''], 0)
    for col in df.columns:
        if col != 'Entidad':
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def process_and_load_file(uploaded_file, conn, indicator_type=None):
    """Procesa un archivo subido y lo carga a la base de datos."""
    
    # Intenta determinar el tipo de archivo desde el nombre
    file_name = uploaded_file.name
    # Usar regex para capturar tanto 'imor_vivienda' como 'vivienda'
    match = re.search(r'consolidated_data_(\w+)\.csv', file_name)
    if not match:
        st.error("El nombre del archivo CSV no coincide con el formato esperado (ej. consolidated_data_vivienda.csv o consolidated_data_imor_vivienda.csv).")
        return
    
    file_key = match.group(1)
    
    # Comprobar si el archivo es de IMOR, ya que tienen un prefijo
    if file_key.startswith('imor_'):
        file_key = f'imor_{file_key.split("_")[1]}'
        if len(file_key.split('_')) > 2:
            file_key = f'imor_{file_key.split("_")[2]}'
        
    if file_key not in INDICATOR_MAP:
        st.error(f"El tipo de archivo '{file_key}' no está mapeado en nuestra configuración.")
        return

    config = INDICATOR_MAP[file_key]
    
    # Lee el archivo CSV
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio)
    
    if df.empty:
        st.warning("El archivo CSV está vacío.")
        return

    # Limpia el DataFrame
    df = clean_dataframe(df)

    # Prepara el DataFrame para la tabla 'indicador_hechos'
    rows_to_insert = []
    
    for _, row in df.iterrows():
        fecha = row['Fecha']
        grupo_banco = row['Entidad']
        
        # --- Lógica para Captación ---
        if file_key == 'captacion':
            for tipo_captacion in config['tipo_captacion']:
                rows_to_insert.append({
                    'fecha': fecha,
                    'id_indicador': config['id_indicador'],
                    'tipo_captacion': tipo_captacion,
                    'grupo_banco': grupo_banco,
                    'valor': row[tipo_captacion]
                })

        # --- Lógica para Múltiples Indicadores (Resultados) ---
        elif isinstance(config['id_indicador'], list):
            for col_name, indicador_id in config['cols_map'].items():
                if col_name in row and isinstance(indicador_id, int):
                    rows_to_insert.append({
                        'fecha': fecha,
                        'id_indicador': indicador_id,
                        'grupo_banco': grupo_banco,
                        'valor': row[col_name]
                    })
        
        # --- Lógica para Cartera o IMOR ---
        else:
            valor_col = list(config['cols_map'].keys())[-1]
            if valor_col in row:
                rows_to_insert.append({
                    'fecha': fecha,
                    'id_indicador': config['id_indicador'],
                    'tipo_credito': config.get('tipo_credito', None),
                    'grupo_banco': grupo_banco,
                    'valor': row[valor_col]
                })


    if rows_to_insert:
        # Crea un DataFrame temporal con los datos a insertar
        df_to_insert = pd.DataFrame(rows_to_insert)
        
        # Elimina duplicados si el archivo se sube más de una vez
        df_to_insert = df_to_insert.drop_duplicates(subset=['fecha', 'grupo_banco', 'id_indicador', 'tipo_credito', 'tipo_captacion'])

        # Carga el DataFrame a la base de datos
        df_to_insert.to_sql('indicador_hechos', conn, if_exists='append', index=False)
        st.success(f"✅ ¡Datos del archivo {file_name} cargados exitosamente!")
    else:
        st.warning("No se encontraron datos para insertar en el archivo.")

# --- 4. INTERFAZ DE USUARIO ---
st.title("Carga de Datos a la Base de Datos")
st.markdown("---")
st.write("Sube aquí tus archivos CSV consolidados para cargarlos a la tabla `indicador_hechos` de tu base de datos PostgreSQL.")

uploaded_files = st.file_uploader(
    "Selecciona uno o más archivos CSV",
    type=['csv'],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Cargar datos a la base de datos"):
        engine = get_db_connection()
        try:
            with engine.connect() as conn:
                for uploaded_file in uploaded_files:
                    st.write(f"Procesando: {uploaded_file.name}")
                    process_and_load_file(uploaded_file, conn, None)
            st.info("🎉 ¡Todos los archivos seleccionados han sido procesados!")
        except Exception as e:
            st.error(f"❌ Ocurrió un error al cargar los datos: {e}")
