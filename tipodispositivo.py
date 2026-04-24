import streamlit as st
import pandas as pd
from fuzzywuzzy import process
import io
import re

st.set_page_config(page_title="Mapeador de Dispositivos", layout="wide")

st.title("🎯 Mapeador Ultra-Rápido")

# --- CARGA DE ARCHIVOS ---
col_file1, col_file2 = st.columns(2)
with col_file1:
    file_tipos = st.file_uploader("Archivo con Tipos (Columna F)", type=['xlsx'])
with col_file2:
    file_sku = st.file_uploader("Archivo de SKUs (Col. A y B)", type=['xlsx'])

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    umbral = st.slider("Umbral de similitud", 0, 100, 80)

if file_tipos and file_sku:
    if st.button("🚀 Ejecutar Mapeo Rápido", use_container_width=True):
        try:
            df_tipos_raw = pd.read_excel(file_tipos)
            df_sku_raw = pd.read_excel(file_sku)

            # 1. Preparar lista de tipos únicos
            lista_tipos = []
            for celda in df_tipos_raw.iloc[:, 5].dropna().astype(str):
                partes = re.split(r'[;,]', celda)
                lista_tipos.extend([p.strip() for p in partes if p.strip()])
            lista_tipos = list(set(lista_tipos))

            # 2. DICCIONARIO DE CACHÉ (La clave de la velocidad)
            cache_mapeo = {}

            def match_optimizado(texto):
                texto = str(texto).strip()
                if not texto or texto == "nan": return "Sin datos"
                
                # Si ya calculamos este texto antes, devolver el resultado guardado
                if texto in cache_mapeo:
                    return cache_mapeo[texto]
                
                # Si hay coincidencia exacta, es instantáneo
                if texto in lista_tipos:
                    cache_mapeo[texto] = texto
                    return texto

                # Solo si lo anterior falla, usamos Fuzzy (lo lento)
                resultado = process.extractOne(texto, lista_tipos)
                if resultado:
                    match, score = resultado
                    final = match if score >= umbral else "Sin coincidencia"
                else:
                    final = "Sin coincidencia"
                
                # Guardar en caché para la próxima vez que aparezca este texto
                cache_mapeo[texto] = final
                return final

            # 3. Procesamiento
            with st.spinner('Procesando con optimización de caché...'):
                # Extraemos las columnas A (SKU) y B (Nombre para comparar)
                sku_col = df_sku_raw.iloc[:, 4] # Según tu archivo es la E (index 4) o cámbialo a 0
                nombre_col = df_sku_raw.iloc[:, 1] # Columna B (index 1)
                
                resultados = []
                # Barra de progreso real
                progreso = st.progress(0)
                total = len(df_sku_raw)
                
                for i, valor in enumerate(nombre_col):
                    resultados.append(match_optimizado(valor))
                    if i % 100 == 0: progreso.progress(i / total)
                progreso.empty()

                df_final = pd.DataFrame({
                    'SKU': sku_col,
                    'Tipo de Dispositivo': resultados
                })

            st.success(f"¡Hecho! Se procesaron {len(df_sku_raw)} filas rápidamente gracias a la caché.")
            st.dataframe(df_final.head(50), use_container_width=True)

            # Botón de descarga
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button("📥 Descargar Resultado", output.getvalue(), "mapeo_rapido.xlsx")

        except Exception as e:
            st.error(f"Error: {e}")