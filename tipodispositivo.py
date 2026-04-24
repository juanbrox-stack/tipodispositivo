import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import io

# Configuración de la página
st.set_page_config(page_title="Mapeador de Dispositivos", layout="wide")

st.title("🔄 Automatización de Mapeo de Dispositivos")
st.write("Sube tus archivos Excel para cruzar SKUs con tipos de dispositivo mediante similitud de texto.")

# --- SECCIÓN DE CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)

with col1:
    file_tipos = st.file_uploader("Archivo de TIPOS (Columna F)", type=['xlsx'])
with col2:
    file_sku = st.file_uploader("Archivo de SKUs (Col. A y B)", type=['xlsx'])

# --- LÓGICA DE PROCESAMIENTO ---
if file_tipos and file_sku:
    try:
        # Cargar datos
        df_tipos_raw = pd.read_excel(file_tipos)
        df_sku_raw = pd.read_excel(file_sku)

        st.success("Archivos cargados correctamente.")

        # Parámetro de precisión ajustable por el usuario
        umbral = st.slider("Umbral de similitud (0-100)", 0, 100, 80, 
                          help="80 es un buen equilibrio. Valores más altos requieren coincidencia más exacta.")

        if st.button("Ejecutar Mapeo"):
            # 1. Procesar lista de tipos (Columna F es índice 5)
            lista_tipos = []
            for item in df_tipos_raw.iloc[:, 5].dropna():
                partes = [p.strip() for p in str(item).split(',')]
                lista_tipos.extend(partes)
            lista_tipos = list(set(lista_tipos)) # Eliminar duplicados

            # 2. Función de búsqueda
            def match_tipo(texto):
                if pd.isna(texto): return "Vacío"
                # Buscamos en la lista de tipos generada
                match, score = process.extractOne(str(texto), lista_tipos)
                return match if score >= umbral else "Sin coincidencia"

            # 3. Crear DataFrame de salida
            with st.spinner('Procesando coincidencias...'):
                df_resultado = pd.DataFrame()
                df_resultado['SKU'] = df_sku_raw.iloc[:, 0] # Columna A
                # Columna B original para comparar contra lista de tipos
                df_resultado['Tipo de Dispositivo'] = df_sku_raw.iloc[:, 1].apply(match_tipo)

            # --- SECCIÓN DE DESCARGA ---
            st.subheader("Resultado Previo")
            st.dataframe(df_resultado.head(10))

            # Preparar Excel para descargar en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name='Mapeo')
            
            st.download_button(
                label="📥 Descargar Excel Resultante",
                data=output.getvalue(),
                file_name="mapeo_finalizado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error al procesar los archivos: {e}")
        st.info("Asegúrate de que el Fichero 1 tenga datos en la columna F y el Fichero 2 en las columnas A y B.")