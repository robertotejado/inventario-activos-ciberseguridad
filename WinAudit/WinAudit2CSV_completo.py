import csv
import pandas as pd
import os
import re

def limpiar_valor(val):
    return val.strip()

def pedir_valor(mensaje, opciones_validas):
    """
    Pide un valor por consola y obliga al usuario a elegir una opción válida.
    No es sensible a mayúsculas/minúsculas.
    """
    opciones_lower = [op.lower() for op in opciones_validas]
    while True:
        valor = input(mensaje).strip()
        if valor.lower() in opciones_lower:
            idx = opciones_lower.index(valor.lower())
            return opciones_validas[idx]
        else:
            print(f"  ⚠️ Error: Valor no válido. Por favor, elige entre: {', '.join(opciones_validas)}")

def procesar_winaudit():
    print("=== PROCESADOR DE HARDWARE Y SOFTWARE WINAUDIT ===")
    
    # 1. Petición interactiva de datos iniciales
    archivo_entrada = input("Introduce el nombre del archivo origen (ej. winaudit.csv): ")
    
    if not os.path.exists(archivo_entrada):
        print(f"ERROR: No se encuentra el archivo '{archivo_entrada}'. Comprueba el nombre.")
        return

    responsable = input("Introduce el responsable o asignado: ")
    ubicacion = input("Introduce la ubicación: ")
    clave = input("Introduce la clave del software (deja en blanco si no hay): ")

    # --- NUEVAS PREGUNTAS CON VALIDACIÓN: HARDWARE ---
    print("\n--- VALORACIÓN DE HARDWARE ---")
    hw_criticidad = pedir_valor("Criticidad del Hardware [Baja/Media/Alta]: ", ["Baja", "Media", "Alta"])
    hw_ens_d = pedir_valor("ENS Disponibilidad [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    hw_ens_i = pedir_valor("ENS Integridad [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    hw_ens_c = pedir_valor("ENS Confidencialidad [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    hw_ens_a = pedir_valor("ENS Autenticidad [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    hw_ens_t = pedir_valor("ENS Trazabilidad [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    hw_crit_prov = pedir_valor("Criticidad Proveedor HW [Baja/Media/Alta/Critica]: ", ["Baja", "Media", "Alta", "Critica"])
    hw_rto = input("RTO del Hardware (Ej. 4h, 24h) [Opcional]: ")
    hw_dependencias = input("Dependencias del Hardware [Opcional]: ")

    # --- NUEVAS PREGUNTAS CON VALIDACIÓN: SOFTWARE ---
    print("\n--- VALORACIÓN DE SOFTWARE (Aplicará a todos los programas extraídos) ---")
    sw_criticidad = pedir_valor("Criticidad del Software [Baja/Media/Alta]: ", ["Baja", "Media", "Alta"])
    sw_ens_c = pedir_valor("ENS Confidencialidad SW [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    sw_ens_i = pedir_valor("ENS Integridad SW [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    sw_ens_d = pedir_valor("ENS Disponibilidad SW [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    sw_crit_prov = pedir_valor("Criticidad Proveedor SW [Baja/Media/Alta/Critica]: ", ["Baja", "Media", "Alta", "Critica"])
    sw_rto = input("RTO del Software (Ej. 4h, 24h) [Opcional]: ")
    sw_dependencias = input("Dependencias del Software [Opcional]: ")

    # 2. Generar nombres de salida dinámicos
    nombre_base = os.path.basename(archivo_entrada)
    if nombre_base.lower().endswith(".csv"):
        nombre_sin_ext = nombre_base[:-4]
    else:
        nombre_sin_ext = nombre_base
        
    archivo_hw_salida = f"HW_{nombre_sin_ext}_para_Importar.csv"
    archivo_sw_salida = f"SW_{nombre_sin_ext}_para_Importar.csv"

    # Estructuras de las plantillas destino
    columnas_sw = [
        'id', 'nombre', 'fabricante', 'version', 'categoria', 'tipo_lic', 
        'cantidad', 'clave', 'caducidad', 'responsable', 'ubicacion', 
        'criticidad', 'ens_c', 'ens_i', 'ens_d', 'rto', 'crit_prov', 
        'dependencias', 'notas'
    ]
    
    columnas_hw = [
        'id', 'categoria', 'tipo', 'marca', 'modelo', 'serie', 'hostname', 
        'ip_mac', 'so', 'asignado', 'ubicacion', 'estado', 'criticidad', 
        'ens_d', 'ens_i', 'ens_c', 'ens_a', 'ens_t', 'rto', 'crit_prov', 
        'dependencias', 'fecha', 'notas'
    ]

    # 3. Lectura binaria inteligente
    with open(archivo_entrada, 'rb') as f:
        datos_crudos = f.read()
    
    if datos_crudos.startswith(b'\xff\xfe') or datos_crudos.startswith(b'\xfe\xff'):
        contenido = datos_crudos.decode('utf-16')
    elif datos_crudos.startswith(b'\xef\xbb\xbf'):
        contenido = datos_crudos.decode('utf-8-sig')
    else:
        try:
            contenido = datos_crudos.decode('utf-8')
        except UnicodeDecodeError:
            contenido = datos_crudos.decode('latin-1')

    # 4. Manejo del separador
    lineas = contenido.splitlines()
    separador = ','
    
    if lineas and lineas[0].lower().startswith('sep='):
        separador = lineas[0].split('=')[1].strip()
        lineas = lineas[1:]

    programas_extraidos = []
    datos_hw = {col: '' for col in columnas_hw}
    hw_encontrado = False
    
    # Variables temporales para la red
    ip_encontrada = ""
    mac_encontrada = ""
    
    lineas_limpias = [linea.replace('\x00', '') for linea in lineas if linea.strip()]
    lector_csv = csv.reader(lineas_limpias, delimiter=separador, quotechar='"')
    
    for fila in lector_csv:
        if not fila or len(fila) < 3:
            continue
        
        codigo = limpiar_valor(fila[0])
        fila_texto = " ".join(fila).lower()
        
        # --- EXTRACCIÓN BÚSQUEDA PROFUNDA DE RED (IP y MAC) ---
        if codigo.startswith('20') or 'red' in fila_texto or 'network' in fila_texto or 'ip' in fila_texto or 'mac' in fila_texto:
            for celda in fila:
                texto_celda = limpiar_valor(celda)
                
                if not ip_encontrada:
                    match_ip = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', texto_celda)
                    if match_ip:
                        ip_cand = match_ip.group(0)
                        if ip_cand not in ['127.0.0.1', '0.0.0.0'] and not ip_cand.startswith('255.'):
                            ip_encontrada = ip_cand
                
                if not mac_encontrada:
                    match_mac = re.search(r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b', texto_celda)
                    if match_mac:
                        mac_encontrada = match_mac.group(0).upper().replace('-', ':')

        # --- EXTRACCIÓN DE HARDWARE (Código 300) ---
        if codigo == '300':
            hw_encontrado = True
            datos_hw['id'] = 'HW-001'
            datos_hw['categoria'] = 'Hardware Usuario'
            datos_hw['tipo'] = 'Ordenador / PC'
            datos_hw['estado'] = 'Activo'
            datos_hw['hostname'] = limpiar_valor(fila[2])
            datos_hw['so'] = limpiar_valor(fila[7])
            datos_hw['marca'] = limpiar_valor(fila[8])
            datos_hw['modelo'] = limpiar_valor(fila[9])
            datos_hw['serie'] = limpiar_valor(fila[10])
            
            # Aplicar campos interactivos al hardware
            datos_hw['asignado'] = responsable
            datos_hw['ubicacion'] = ubicacion
            datos_hw['criticidad'] = hw_criticidad
            datos_hw['ens_d'] = hw_ens_d
            datos_hw['ens_i'] = hw_ens_i
            datos_hw['ens_c'] = hw_ens_c
            datos_hw['ens_a'] = hw_ens_a
            datos_hw['ens_t'] = hw_ens_t
            datos_hw['rto'] = hw_rto
            datos_hw['crit_prov'] = hw_crit_prov
            datos_hw['dependencias'] = hw_dependencias
            
            cpu = limpiar_valor(fila[13]) if len(fila) > 13 else ""
            ram = limpiar_valor(fila[14]) if len(fila) > 14 else ""
            disco = limpiar_valor(fila[15]) if len(fila) > 15 else ""
            datos_hw['notas'] = f"CPU: {cpu} | RAM: {ram} | Disco: {disco}"

        # --- EXTRACCIÓN DE SOFTWARE (Solo Código 500 - Software Instalado) ---
        elif codigo == '500':
            nombre_original = limpiar_valor(fila[2])
            if not nombre_original: continue
            
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

    # --- ASIGNAR IP Y MAC AL HARDWARE (Formato solicitado) ---
    if hw_encontrado:
        if ip_encontrada and mac_encontrada:
            datos_hw['ip_mac'] = f"{ip_encontrada} / {mac_encontrada}"
        elif ip_encontrada:
             datos_hw['ip_mac'] = ip_encontrada
        elif mac_encontrada:
             datos_hw['ip_mac'] = mac_encontrada

    print("\nProcesando y limpiando datos...")

    # --- GUARDAR HARDWARE ---
    if hw_encontrado:
        df_hw = pd.DataFrame([datos_hw])
        df_hw = df_hw[columnas_hw]
        df_hw.to_csv(archivo_hw_salida, index=False, encoding='utf-8-sig')
        print(f"✅ HARDWARE: '{datos_hw['hostname']}' guardado en {archivo_hw_salida}")
    else:
        print("⚠️ No se detectó información de Hardware (Código 300).")

    # --- GUARDAR SOFTWARE (Compactado y Limpiado) ---
    if programas_extraidos:
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

        # --- AGRUPAR DATOS ---
        df_sw_compacto = df_sw.groupby(['nombre', 'fabricante'], as_index=False).agg({
            'version': lambda x: " / ".join(sorted(list(set(filter(None, x))))),
            'categoria': 'first',
            'notas': lambda x: " // ".join(list(dict.fromkeys(filter(None, x))))
        })

        # --- APLICAR VALORES ---
        for col in columnas_sw:
            if col not in df_sw_compacto.columns:
                df_sw_compacto[col] = ''
        
        df_sw_compacto['cantidad'] = 1
        df_sw_compacto['responsable'] = responsable
        df_sw_compacto['ubicacion'] = ubicacion
        df_sw_compacto['clave'] = clave if clave.strip() != "" else ""
        
        # Aplicar los nuevos campos de Software
        df_sw_compacto['criticidad'] = sw_criticidad
        df_sw_compacto['ens_c'] = sw_ens_c
        df_sw_compacto['ens_i'] = sw_ens_i
        df_sw_compacto['ens_d'] = sw_ens_d
        df_sw_compacto['rto'] = sw_rto
        df_sw_compacto['crit_prov'] = sw_crit_prov
        df_sw_compacto['dependencias'] = sw_dependencias
        
        # --- ORDENAR Y EXPORTAR ---
        df_sw_compacto = df_sw_compacto.sort_values(['categoria', 'nombre']).reset_index(drop=True)
        df_sw_compacto['id'] = [f"SW-{i+1:03d}" for i in range(len(df_sw_compacto))]

        df_sw_compacto = df_sw_compacto[columnas_sw]
        df_sw_compacto.to_csv(archivo_sw_salida, index=False, encoding='utf-8-sig')
        print(f"✅ SOFTWARE: {len(df_sw_compacto)} programas limpios guardados en {archivo_sw_salida}")
    else:
        print("⚠️ No se detectó información de Software (Código 500).")

if __name__ == "__main__":
    procesar_winaudit()