import csv
import pandas as pd
import os
import re

def limpiar_valor(val):
    return val.strip()

def convertir_winaudit(archivo_entrada, archivo_salida, responsable_input, ubicacion_input):
    columnas_destino = [
        'id', 'nombre', 'fabricante', 'version', 'categoria', 'tipo_lic', 
        'cantidad', 'clave', 'caducidad', 'responsable', 'ubicacion', 
        'criticidad', 'ens_c', 'ens_i', 'ens_d', 'rto', 'crit_prov', 
        'dependencias', 'notas'
    ]

    if not os.path.exists(archivo_entrada):
        print(f"ERROR: No se encuentra el archivo '{archivo_entrada}'")
        return

    # 1. Lectura binaria inteligente
    with open(archivo_entrada, 'rb') as f:
        datos_crudos = f.read()
    
    # Detectar el formato exacto para evitar caracteres "fantasma"
    if datos_crudos.startswith(b'\xff\xfe') or datos_crudos.startswith(b'\xfe\xff'):
        contenido = datos_crudos.decode('utf-16')
    elif datos_crudos.startswith(b'\xef\xbb\xbf'):
        contenido = datos_crudos.decode('utf-8-sig')
    else:
        try:
            contenido = datos_crudos.decode('utf-8')
        except UnicodeDecodeError:
            contenido = datos_crudos.decode('latin-1')

    # 2. Manejo inteligente del separador
    lineas = contenido.splitlines()
    separador = ','
    if lineas and lineas[0].lower().startswith('sep='):
        separador = lineas[0].split('=')[1].strip()
        lineas = lineas[1:]

    programas_extraidos = []
    
    # Procesamos las líneas limpiando saltos de línea y nulos
    lineas_limpias = [linea.replace('\x00', '') for linea in lineas if linea.strip()]
    lector_csv = csv.reader(lineas_limpias, delimiter=separador, quotechar='"')
    
    for fila in lector_csv:
        if not fila or len(fila) < 3:
            continue
        
        codigo = limpiar_valor(fila[0])
        
        # WinAudit: AHORA SOLO PROCESAMOS EL 500 (Software Instalado)
        # Ignoramos completamente el 400 (Componente Sistema)
        if codigo == '500':
            nombre_original = limpiar_valor(fila[2])
            if not nombre_original: continue
            
            # Limpiar etiquetas de arquitectura para agrupar mejor
            nombre_limpio = re.sub(r'\s*\(?(64-bit|x64|64bit|32-bit|x86)\)?', '', nombre_original, flags=re.I).strip()
            
            fabricante = limpiar_valor(fila[3]) if len(fila) > 3 else ""
            version = limpiar_valor(fila[4]) if len(fila) > 4 else ""
            categoria = "Software Instalado"
            info_extra = " | ".join([limpiar_valor(x) for x in fila[5:] if x.strip()])
            detalle_completo = f"{nombre_original}: {info_extra}" if info_extra else nombre_original
            
            programas_extraidos.append({
                'nombre': nombre_limpio,
                'fabricante': fabricante,
                'version': version,
                'categoria': categoria,
                'notas': detalle_completo
            })

    if not programas_extraidos:
        print("⚠️ No se encontró Software Instalado (código 500) en el archivo.")
        return

    df_sw = pd.DataFrame(programas_extraidos)

    # --- REGLAS DE LIMPIEZA ESPECÍFICAS ---
    # 1. Unificar Python
    mask_python = df_sw['nombre'].str.contains('Python', na=False, case=False)
    if mask_python.any():
        df_sw.loc[mask_python, 'nombre'] = 'Python 3.13.12'
            
    # 2. Eliminar Runtimes secundarios de Microsoft Visual C++
    mask_vcpp = df_sw['nombre'].str.contains('Additional Runtime|Minimum Runtime', na=False, case=False)
    df_sw = df_sw[~mask_vcpp]
        
    # 3. Unificar Microsoft Edge (WebView2)
    mask_edge = df_sw['nombre'].str.contains('WebView2 Runtime de Microsoft Edge', na=False, case=False)
    df_sw.loc[mask_edge, 'nombre'] = 'Microsoft Edge'

    # 3. Compactar / Eliminar Duplicados
    df_sw_compacto = df_sw.groupby(['nombre', 'fabricante'], as_index=False).agg({
        'version': lambda x: " / ".join(sorted(list(set(filter(None, x))))),
        'categoria': 'first',
        'notas': lambda x: " // ".join(list(dict.fromkeys(filter(None, x))))
    })

    # Preparar el dataframe de salida rellenando columnas vacías
    for col in columnas_destino:
        if col not in df_sw_compacto.columns:
            df_sw_compacto[col] = ''

    # --- APLICAMOS LOS DATOS DEL PROMPT Y VALORES POR DEFECTO ---
    df_sw_compacto['responsable'] = responsable_input
    df_sw_compacto['ubicacion'] = ubicacion_input
    df_sw_compacto['cantidad'] = 1  # Establecer la cantidad siempre a 1
    
    # 4. Formato Final
    df_sw_compacto = df_sw_compacto.sort_values(['categoria', 'nombre']).reset_index(drop=True)
    
    # Generar los IDs consecutivos con el formato SW-001, SW-002...
    df_sw_compacto['id'] = [f"SW-{i+1:03d}" for i in range(len(df_sw_compacto))]

    df_sw_final = df_sw_compacto[columnas_destino]

    # Exportar asegurando compatibilidad con Excel (utf-8-sig)
    df_sw_final.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print(f"\n✅ SOFTWARE: {len(df_sw_final)} programas limpios guardados en {archivo_salida}")

if __name__ == "__main__":
    print("=== PROCESADOR DE SOFTWARE WINAUDIT ===")
    # 1. Pedimos los datos por consola
    archivo = input("Archivo de entrada (ej: winaudit.csv): ")
    responsable = input("Responsable / Asignado (ej: Roberto Tejado): ")
    ubicacion = input("Ubicación (ej: Dpto. Oficinas): ")

    # 2. Construimos el nombre de salida con el sufijo
    nombre_base = os.path.basename(archivo)
    if nombre_base.lower().endswith(".csv"):
        nombre_sin_ext = nombre_base[:-4]
    else:
        nombre_sin_ext = nombre_base
        
    salida = f"SW_{nombre_sin_ext}_para_Importar.csv"

    # 3. Ejecutamos la función
    convertir_winaudit(archivo, salida, responsable, ubicacion)