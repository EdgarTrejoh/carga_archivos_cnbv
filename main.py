import streamlit as st
import pandas as pd
import glob
import os
import altair as alt
from datetime import datetime
from sqlalchemy import create_engine
import traceback
import requests
import io
import time

# Importamos las funciones de tus otros archivos
from cnbv_downloader import download_file
import data_processor as dp

# ======================================================================
# --- CONFIGURACIÓN DE LA PÁGINA ---
# ======================================================================
st.set_page_config(
    page_title="Análisis Integral CNBV",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Análisis Integral CNBV Banca Múltiple")

# ======================================================================
# --- VARIABLES GLOBALES ---
# ======================================================================
DOWNLOAD_DIR = "./descargas_cnbv"
PROCESSED_DIR = "./archivos_procesados"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Lista de bancos principales para la visualización.
TOP_BANKS = [
    "BBVA México", "Santander", "Banorte", "Banamex", "Scotiabank",
    "HSBC", "Inbursa", "BanCoppel"
]

# ======================================================================
# --- FUNCIONES DE PROCESAMIENTO Y VISUALIZACIÓN ---
# ======================================================================
def save_to_postgresql(df, table_name):
    """Guarda un DataFrame en una tabla de PostgreSQL."""
    try:
        db_config = st.session_state.db_config
        # Construimos la URL de conexión a la base de datos
        engine_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        engine = create_engine(engine_url)
        
        st.info(f"Conectando y guardando datos en la tabla '{table_name}'...")
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        st.success(f"✅ Datos guardados en la tabla '{table_name}' exitosamente.")
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error al conectar o guardar en la base de datos: {e}")
        st.error(f"Detalles del error: {traceback.format_exc()}")

def create_viz_df(df, y_column, selected_entities):
    """
    Crea un DataFrame para la visualización, incluyendo los datos de "Otros bancos"
    y "Sistema" según las selecciones del usuario.
    """
    df_viz = pd.DataFrame()
    
    # Agrega las entidades principales seleccionadas
    for entity in selected_entities:
        if entity in df['Entidad'].unique():
            df_viz = pd.concat([df_viz, df[df['Entidad'] == entity]], ignore_index=True)
    
    # Agrega "Otros bancos" si está seleccionado
    if 'Otros bancos' in selected_entities:
        other_banks_df = df[~df['Entidad'].isin(TOP_BANKS)]
        other_banks_df = other_banks_df[other_banks_df['Entidad'] != 'Sistema']
        if not other_banks_df.empty:
            agg_df = other_banks_df.groupby('Fecha', as_index=False).sum(numeric_only=True)
            agg_df['Entidad'] = 'Otros bancos'
            df_viz = pd.concat([df_viz, agg_df], ignore_index=True)

    # Agrega "Sistema" si está seleccionado
    if 'Sistema' in selected_entities and 'Sistema' in df['Entidad'].unique():
        sistema_df = df[df['Entidad'] == 'Sistema'].copy()
        df_viz = pd.concat([df_viz, sistema_df], ignore_index=True)
    
    return df_viz

def show_data_visualization(df, selected_file_name):
    """Genera y muestra la visualización de datos."""
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # Obtenemos la primera columna de datos, excluyendo 'Entidad', 'Fecha' y otras no numéricas
    excluded_columns = [
        'Entidad', 'Fecha', 'IMOR', 'ICOR', 'PE', 'CaptacionTotal', 'DepositoExigInmediata',
        'DepositoPlazoPG', 'DepositoPlazoMV', 'TitulosCredito', 'PrestamosInterBanc',
        'CuentaGlobalCapt', 'ActivoTotal', 'Inversiones', 'CapitalContable', 'ResultadoNeto', 'Sistema'
    ]
    
    y_column = [col for col in df.columns if col not in excluded_columns][0]
    
    st.header("Visualización de Datos")

    # Lista de opciones para la selección
    all_entities = sorted(df['Entidad'].unique().tolist())
    
    select_options = sorted([e for e in all_entities if e in TOP_BANKS])
    select_options.append('Otros bancos')
    if 'Sistema' in all_entities:
        select_options.append('Sistema')
    
    # Interfaz para selección de entidades
    selected_entities = st.multiselect(
        "Selecciona las entidades a visualizar:",
        options=select_options,
        default=['BBVA', 'Santander', 'Otros bancos', 'Sistema']
    )
    
    # Preparamos los datos para la visualización
    df_viz = create_viz_df(df, y_column, selected_entities)

    if not df_viz.empty:
        title = selected_file_name.replace(".csv", "").replace("consolidated_data_", "Dashboard de ").replace("_", " ").title()

        chart = alt.Chart(df_viz).mark_line().encode(
            x=alt.X('Fecha', title='Fecha'),
            y=alt.Y(y_column, title=y_column.replace('_', ' ').title()),
            color='Entidad',
            tooltip=['Fecha', 'Entidad', alt.Tooltip(y_column, format=',.0f')]
        ).properties(
            title=f'{title} por Entidad'
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("⚠️ Por favor, selecciona al menos una entidad para visualizar los datos.")
    
    st.subheader("Tabla de Datos")
    st.dataframe(df)

# ======================================================================
# --- LÓGICA DE LA INTERFAZ DE USUARIO CON STREAMLIT ---
# ======================================================================
st.sidebar.header("Opciones de Configuración")
with st.sidebar.expander("Descarga de Archivos CNBV"):
    year_options = list(range(datetime.now().year, 2000, -1))
    month_options = list(range(1, 13))
    selected_year = st.selectbox("Selecciona un año", year_options)
    selected_month = st.selectbox("Selecciona un mes", month_options)
    
    if st.button("Descargar Archivo"):
        with st.spinner("Descargando..."):
            filepath = download_file(selected_year, selected_month)
            if filepath:
                st.session_state.last_downloaded_file = filepath
                st.success("✅ ¡Descarga completada!")
            else:
                st.error("❌ No se pudo descargar el archivo. Verifique su conexión a internet.")

with st.sidebar.expander("Conexión a PostgreSQL"):
    db_config = {}
    db_config['host'] = st.text_input("Host de la DB", "localhost")
    db_config['port'] = st.text_input("Puerto de la DB", "5432")
    db_config['dbname'] = st.text_input("Nombre de la DB", "cnbv_db")
    db_config['user'] = st.text_input("Usuario", "postgres")
    db_config['password'] = st.text_input("Contraseña", type="password")
    st.session_state.db_config = db_config

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    if st.button("Procesar Archivos Descargados"):
        downloaded_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.xlsx"))
        if not downloaded_files:
            st.warning("⚠️ No se encontraron archivos para procesar en la carpeta 'descargas_cnbv'.")
        else:
            with st.spinner("Procesando archivos..."):
                dp.process_all_files(downloaded_files)
                st.success("🎉 ¡Procesamiento de archivos completado!")

with col2:
    if st.button("Guardar CSVs en PostgreSQL"):
        processed_files = glob.glob(os.path.join(PROCESSED_DIR, "*.csv"))
        if not processed_files:
            st.warning("⚠️ No hay archivos CSV procesados para guardar. Por favor, procesa los datos primero.")
        else:
            st.info("Iniciando guardado en PostgreSQL...")
            for file_path in processed_files:
                try:
                    df = pd.read_csv(file_path)
                    table_name = os.path.basename(file_path).replace(".csv", "").replace("consolidated_data_", "")
                    save_to_postgresql(df, table_name)
                except Exception as e:
                    st.error(f"❌ Error al guardar el archivo {os.path.basename(file_path)} en PostgreSQL: {e}")
                    st.error(f"Detalles del error: {traceback.format_exc()}")

st.markdown("---")

# Visualización de datos
available_files = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.csv")))
file_names = [os.path.basename(f) for f in available_files]

if not available_files:
    st.warning("⚠️ No hay archivos procesados disponibles. Por favor, procesa los datos primero.")
else:
    selected_file_name = st.selectbox("Selecciona el indicador a visualizar:", file_names)
    selected_file_path = os.path.join(PROCESSED_DIR, selected_file_name)

    df = pd.read_csv(selected_file_path)
    if not df.empty:
        show_data_visualization(df, selected_file_name)
