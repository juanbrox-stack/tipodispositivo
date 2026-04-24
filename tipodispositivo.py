import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import io
import re

# Configuración visual de la página
st.set_page_config(page_title="Mapeador Pro", layout="wide", page_icon="🎯")

st.title("🎯 Optimizador de Mapeo de Dispositivos")
st.markdown("""
Esta herramienta analiza tus SKUs y encuentra el **único tipo de dispositivo más parecido** basándose en un listado de referencia.
""")

# --- BARRA LATERAL PARA PARÁMETROS ---
st.sidebar.header("Configuración")
umbral = st.sidebar.slider(
    "Umbral de precisión (Score)", 
    min_value=0, 
    max_value=100, 
    value=80,
    help="Sube el valor para coincidencias más exactas, bájalo si quieres ser más flexible."
)

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Referencia de Tipos")
    file_tipos = st.file_uploader("Subir Excel con Tipos (Columna F)", type=['xlsx'], key="tipos")
    st.caption("Se buscarán los tipos en la columna F separados por ',' o ';'")

with col2:
    st.subheader("2. Archivo de SKUs")
    file_sku = st.file_uploader("Subir Excel de SKUs (Col. A y B)", type=['xlsx'], key="skus")
    st.caption("Col A: SKU | Col B: Texto para comparar")

# --- PROCESAMIENTO ---
if file_tipos and file_sku:
    try:
        # Cargar DataFrames
        df_tipos_raw = pd.read_excel(file_tipos)
        df_sku_raw = pd.read_excel(file_sku)

        if st.button("🚀 Iniciar Mapeo de Coincidencia Única"):
            
            # PASO 1: Aplanar la lista de tipos
            # Extraemos cada palabra individual de la columna F
            st.info("Analizando y desglosando lista de tipos...")
            lista_tipos_unificados = []
            
            # Suponemos columna F (índice 5)
            col_f_datos = df_tipos_raw.iloc[:, 5].dropna().astype(str)
            
            for celda in col_f_datos:
                # Separar por comas o punto y coma usando regex
                partes = re.split(r'[;,]', celda)
                for p in partes:
                    limpio = p.strip()
                    if limpio:
                        lista_tipos_unificados.append(limpio)
            
            # Eliminar duplicados para optimizar búsqueda
            lista_tipos_unificados = list(set(lista_tipos_unificados))
            
            # PASO 2: Función de Match Único
            def buscar_mejor_match(texto_usuario):
                if pd.isna(texto_usuario) or str(texto_usuario).strip() == "":
                    return "Sin datos"
                
                # fuzzywuzzy devuelve (resultado, puntuación)
                resultado = process.extractOne(str(texto_usuario), lista_tipos_unificados)
                
                if resultado:
                    match, score = resultado
                    return match if score >= umbral else "Sin coincidencia"
                return "Sin coincidencia"

            # PASO 3: Ejecutar mapeo
            with st.spinner('Comparando SKUs contra tipos individuales...'):
                # Creamos el DataFrame final con 2 columnas como pediste
                df_final = pd.DataFrame()
                df_final['SKU'] = df_sku_raw.iloc[:, 0] # Columna A
                # Buscamos el match individual para la columna B
                df_final['Tipo de Dispositivo'] = df_sku_raw.iloc[:, 1].apply(buscar_mejor_match)

            # --- RESULTADOS Y DESCARGA ---
            st.success("¡Mapeo finalizado!")
            
            col_res1, col_res2 = st.columns([2, 1])
            
            with col_res1:
                st.write("### Vista previa (20 primeras filas)")
                st.dataframe(df_final.head(20), use_container_width=True)
            
            with col_res2:
                st.write("### Exportar")
                # Crear Excel en memoria
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Mapeo_Unico')
                
                st.download_button(
                    label="📥 Descargar Resultado (Excel)",
                    data=buffer.getvalue(),
                    file_name="mapeo_dispositivos_final.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Se produjo un error: {e}")
else:
    st.warning("Por favor, sube ambos archivos para comenzar.")