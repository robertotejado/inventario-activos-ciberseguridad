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
            # Devuelve el valor con el formato exacto de 'opciones_validas'
            idx = opciones_lower.index(valor.lower())
            return opciones_validas[idx]
        else:
            print(f"  ⚠️ Error: Valor no válido. Por favor, elige entre: {', '.join(opciones_validas)}")

def procesar_freepcaudit():
    print("=== PROCESADOR DE HARDWARE Y SOFTWARE FREE PC AUDIT ===")
    
    # 1. Petición interactiva inicial
    archivo_entrada = input("Introduce el nombre del archivo de texto origen (ej. mipc.txt): ")
    
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
    # RTO y Dependencias siguen siendo texto libre
    hw_rto = input("RTO del Hardware (Ej. 4h, 24h) [Opcional]: ")
    hw_dependencias = input("Dependencias del Hardware [Opcional]: ")

    # --- NUEVAS PREGUNTAS CON VALIDACIÓN: SOFTWARE ---
    print("\n--- VALORACIÓN DE SOFTWARE (Aplicará a todos los programas extraídos) ---")
    sw_criticidad = pedir_valor("Criticidad del Software [Baja/Media/Alta]: ", ["Baja", "Media", "Alta"])
    sw_ens_c = pedir_valor("ENS Confidencialidad SW [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    sw_ens_i = pedir_valor("ENS Integridad SW [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    sw_ens_d = pedir_valor("ENS Disponibilidad SW [Bajo/Medio/Alto]: ", ["Bajo", "Medio", "Alto"])
    sw_crit_prov = pedir_valor("Criticidad Proveedor SW [Baja/Media/Alta/Critica]: ", ["Baja", "Media", "Alta", "Critica"])
    # RTO y Dependencias siguen siendo texto libre
    sw_rto = input("RTO del Software (Ej. 4h, 24h) [Opcional]: ")
    sw_dependencias = input("Dependencias del Software [Opcional]: ")

    # Nombres de salida
    nombre_base = os.path.basename(archivo_entrada)
    nombre_sin_ext = os.path.splitext(nombre_base)[0]
    
    archivo_hw_salida = f"HW_{nombre_sin_ext}_para_Importar.csv"
    archivo_sw_salida = f"SW_{nombre_sin_ext}_para_Importar.csv"

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

    # Leer archivo completo
    try:
        with open(archivo_entrada, 'r', encoding='utf-8', errors='ignore') as f:
            texto_completo = f.read()
    except Exception as e:
         print(f"Error al leer el archivo: {e}")
         return

    datos_hw = {col: '' for col in columnas_hw}
    programas_extraidos = []

    print("\nExtrayendo información de Hardware y Red...")

    # --- EXTRACCIÓN DE HARDWARE (Expresiones Regulares en el Texto) ---
    datos_hw['id'] = 'HW-001'
    datos_hw['categoria'] = 'Hardware Usuario'
    datos_hw['tipo'] = 'Ordenador / PC'
    datos_hw['estado'] = 'Activo'
    datos_hw['asignado'] = responsable
    datos_hw['ubicacion'] = ubicacion
    
    # Asignación de los nuevos campos de Hardware
    datos_hw['criticidad'] = hw_criticidad
    datos_hw['ens_d'] = hw_ens_d
    datos_hw['ens_i'] = hw_ens_i
    datos_hw['ens_c'] = hw_ens_c
    datos_hw['ens_a'] = hw_ens_a
    datos_hw['ens_t'] = hw_ens_t
    datos_hw['rto'] = hw_rto
    datos_hw['crit_prov'] = hw_crit_prov
    datos_hw['dependencias'] = hw_dependencias

    # Hostname
    match = re.search(r'Host name:\s*(.*)', texto_completo)
    if match: datos_hw['hostname'] = match.group(1).strip()

    # SO
    match = re.search(r'Operating system:\s*(.*)', texto_completo)
    if match: datos_hw['so'] = match.group(1).split('(')[0].strip()

    # Marca/Fabricante
    match = re.search(r'Motherboard: (.*?)\s*\(', texto_completo)
    if not match: match = re.search(r'BIOS: (.*?)\s*\(', texto_completo)
    if match: datos_hw['marca'] = match.group(1).strip()

    # Modelo
    match = re.search(r'Model:\s*(.*)', texto_completo)
    if match: datos_hw['modelo'] = match.group(1).strip()

    # Serie
    match = re.search(r'Serial number:\s*(.*)', texto_completo)
    if match: datos_hw['serie'] = match.group(1).strip()

    # CPU, RAM, Disco (Anotaciones)
    cpu_match = re.search(r'Processor:\s*(.*?)\s*\(', texto_completo)
    cpu = cpu_match.group(1).strip() if cpu_match else ""
    
    ram_match = re.search(r'Physical memory:\s*(.*)', texto_completo)
    ram = ram_match.group(1).strip() if ram_match else ""
    
    disco_match = re.search(r'Disk:\s*(.*?)\s*\(', texto_completo)
    disco = disco_match.group(1).strip() if disco_match else ""

    datos_hw['notas'] = f"CPU: {cpu} | RAM: {ram} | Disco: {disco}"

    # --- EXTRACCIÓN DE RED (IP y MAC combinada) ---
    ip = ""
    mac = ""
    ip_match = re.search(r'IP-address:\s*([0-9\.]+)', texto_completo)
    if ip_match and ip_match.group(1) != '127.0.0.1':
        ip = ip_match.group(1).strip()
    
    mac_match = re.search(r'Adapter MAC-address:\s*([0-9A-Fa-f:]+)', texto_completo)
    if mac_match:
        mac = mac_match.group(1).strip()
        
    if ip and mac:
        datos_hw['ip_mac'] = f"{ip} / {mac}"
    elif ip: datos_hw['ip_mac'] = ip
    elif mac: datos_hw['ip_mac'] = mac

    # --- EXTRACCIÓN DE SOFTWARE ---
    print("Extrayendo información de Software...")
    if 'SOFTWARE\n========' in texto_completo:
        bloque_sw = texto_completo.split('SOFTWARE\n========')[1]
        
        if 'PROCESSES\n========' in bloque_sw:
             bloque_sw = bloque_sw.split('PROCESSES\n========')[0]
             
        lineas_sw = [l for l in bloque_sw.split('\n') if l.strip()]
        
        for linea in lineas_sw:
            partes = [p.strip() for p in linea.split(', ')]
            
            nombre_original = partes[0].replace(' [Store App]', '')
            nombre_limpio = re.sub(r'\s*\(?(64-bit|x64|64bit|32-bit|x86)\)?', '', nombre_original, flags=re.I).strip()
            
            version = ""
            fabricante = ""
            
            for parte in partes[1:]:
                if parte.startswith('Version:'):
                     version = parte.replace('Version:', '').strip()
                elif parte.startswith('Publisher:'):
                     fabricante = parte.replace('Publisher:', '').strip()

            programas_extraidos.append({
                'nombre': nombre_limpio,
                'fabricante': fabricante,
                'version': version,
                'categoria': 'Software Instalado',
                'notas': linea
            })

    # --- GUARDAR HARDWARE ---
    df_hw = pd.DataFrame([datos_hw])
    df_hw = df_hw[columnas_hw]
    df_hw.to_csv(archivo_hw_salida, index=False, encoding='utf-8-sig')
    print(f"\n✅ HARDWARE: '{datos_hw['hostname']}' guardado en {archivo_hw_salida}")

    # --- GUARDAR SOFTWARE (Compactado y Limpiado) ---
    if programas_extraidos:
        df_sw = pd.DataFrame(programas_extraidos)
        
        mask_ruido = df_sw['notas'].str.contains(r'\[Store App\]', na=False)
        df_sw = df_sw[~mask_ruido]

        mask_python = df_sw['nombre'].str.contains('Python', na=False, case=False)
        if mask_python.any():
            df_sw.loc[mask_python, 'nombre'] = 'Python 3.13.12'
            
        mask_edge = df_sw['nombre'].str.contains('WebView2 Runtime de Microsoft Edge|Microsoft Edge', na=False, case=False)
        if mask_edge.any():
            df_sw.loc[mask_edge, 'nombre'] = 'Microsoft Edge'

        df_sw_compacto = df_sw.groupby(['nombre', 'fabricante'], as_index=False).agg({
            'version': lambda x: " / ".join(sorted(list(set(filter(None, x))))),
            'categoria': 'first',
            'notas': 'first'
        })

        for col in columnas_sw:
            if col not in df_sw_compacto.columns:
                df_sw_compacto[col] = ''
        
        df_sw_compacto['cantidad'] = 1
        df_sw_compacto['responsable'] = responsable
        df_sw_compacto['ubicacion'] = ubicacion
        df_sw_compacto['clave'] = clave if clave.strip() != "" else ""

        # Asignación de los nuevos campos de Software
        df_sw_compacto['criticidad'] = sw_criticidad
        df_sw_compacto['ens_c'] = sw_ens_c
        df_sw_compacto['ens_i'] = sw_ens_i
        df_sw_compacto['ens_d'] = sw_ens_d
        df_sw_compacto['rto'] = sw_rto
        df_sw_compacto['crit_prov'] = sw_crit_prov
        df_sw_compacto['dependencias'] = sw_dependencias
        
        df_sw_compacto = df_sw_compacto.sort_values(['categoria', 'nombre']).reset_index(drop=True)
        df_sw_compacto['id'] = [f"SW-{i+1:03d}" for i in range(len(df_sw_compacto))]

        df_sw_compacto = df_sw_compacto[columnas_sw]
        df_sw_compacto.to_csv(archivo_sw_salida, index=False, encoding='utf-8-sig')
        print(f"✅ SOFTWARE: {len(df_sw_compacto)} programas limpios guardados en {archivo_sw_salida}")
    else:
        print("⚠️ No se detectó información de Software.")

if __name__ == "__main__":
    procesar_freepcaudit()