import streamlit as st
from datetime import datetime
import cnbv_downloader

# Diccionario para mapear los nombres de los meses a sus números
MONTHS_ES = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12,
}

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
        try:
            cnbv_downloader.download_file(selected_year, selected_month)
            st.success(f"✅ ¡Descarga completa! Archivo guardado en la carpeta **./descargas_cnbv**")
        except Exception as e:
            st.error(f"Ocurrió un error durante la descarga: {e}")
            st.info("Es posible que no haya un boletín para el mes y año seleccionados. Por favor, intente con otra fecha.")

if __name__ == "__main__":
    main()