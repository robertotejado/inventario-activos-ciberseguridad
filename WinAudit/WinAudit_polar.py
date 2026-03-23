import polars as pl
import re
import os
import csv

def procesar_winaudit_polar():
    # 1. Entradas del usuario
    archivo_entrada = input("Introduce el nombre del archivo origen de WinAudit (ej. winaudit.csv): ")
    
    if not os.path.exists(archivo_entrada):
        print(f"Error: No se encuentra el archivo '{archivo_entrada}'")
        return

    responsable = input("Introduce el responsable o asignado: ")
    ubicacion = input("Introduce la ubicación: ")

    # 2. Lectura del archivo
    with open(archivo_entrada, 'rb') as f:
        datos_crudos = f.read()
    
    if datos_crudos.startswith(b'\xff\xfe'):
        contenido = datos_crudos.decode('utf-16')
    else:
        try:
            contenido = datos_crudos.decode('utf-8-sig')
        except UnicodeDecodeError:
            contenido = datos_crudos.decode('latin-1', errors='replace')

    lineas = contenido.splitlines()
    if lineas and lineas[0].lower().startswith('sep='):
        lineas = lineas[1:]

    # 3. Estructuras de las plantillas
    hw_cols = ['id', 'categoria', 'tipo', 'marca', 'modelo', 'serie', 'hostname', 'ip_mac', 'so', 'asignado', 'ubicacion', 'estado', 'criticidad', 'ens_d', 'ens_i', 'ens_c', 'ens_a', 'ens_t', 'rto', 'crit_prov', 'dependencias', 'fecha', 'notas']
    sw_cols = ['id', 'nombre', 'fabricante', 'version', 'categoria', 'tipo_lic', 'cantidad', 'clave', 'caducidad', 'responsable', 'ubicacion', 'criticidad', 'ens_c', 'ens_i', 'ens_d', 'rto', 'crit_prov', 'dependencias', 'notas']

    hw_data = {col: "" for col in hw_cols}
    sw_list = []
    
    ip_encontrada = ""
    mac_encontrada = ""
    
    lector = csv.reader(lineas, delimiter=',', quotechar='"')
    
    for fila in lector:
        if not fila or len(fila) < 3: continue
        
        codigo = fila[0].strip()

        # --- EXTRACCIÓN INFALIBLE DE IP Y MAC (Código 2600) ---
        if codigo == '2600':
            estado = fila[18].strip() if len(fila) > 18 else ""
            if estado == 'Connected':
                col_ips = fila[6] if len(fila) > 6 else ""
                col_mac = fila[17] if len(fila) > 17 else ""

                if not ip_encontrada:
                    m_ip = re.search(r'\b(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.\d+\.\d+\.\d+)\b', col_ips)
                    if m_ip:
                        cand_ip = m_ip.group(1)
                        if not cand_ip.startswith("192.168.56.") and not cand_ip.endswith(".255"):
                            ip_encontrada = cand_ip
                
                if not mac_encontrada:
                    m_mac = re.search(r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b', col_mac)
                    if m_mac:
                        cand_mac = m_mac.group(0).upper().replace('-', ':')
                        if not cand_mac.startswith("0A:00:27") and not cand_mac.startswith("08:00:27"):
                            mac_encontrada = cand_mac

        # --- HARDWARE (Código 300) ---
        elif codigo == '300':
            hw_data.update({
                "id": "HW-001",
                "categoria": "Hardware Usuario",
                "tipo": "Ordenador / PC",
                "hostname": fila[2].strip() if len(fila) > 2 else "",
                "so": fila[7].strip() if len(fila) > 7 else "",
                "marca": fila[8].strip() if len(fila) > 8 else "",
                "modelo": fila[9].strip() if len(fila) > 9 else "",
                "serie": fila[10].strip() if len(fila) > 10 else "",
                "asignado": responsable,
                "ubicacion": ubicacion,
                "estado": "Activo",
                "notas": f"CPU: {fila[13] if len(fila)>13 else ''} | RAM: {fila[14] if len(fila)>14 else ''}"
            })

        # --- SOFTWARE (Código 500) ---
        elif codigo == '500':
            nombre = fila[2].strip()
            
            # 1. Filtro basura de Windows Store y .NET
            if any(x in nombre for x in ["[Store App]", "Microsoft.NET", "Microsoft.VCLibs", "Actualización"]):
                continue
            
            # 2. Filtro de Runtimes secundarios (que el otro programa no muestra)
            if any(x in nombre for x in ["Additional Runtime", "Minimum Runtime", "WebView2 Runtime"]):
                continue
                
            # 3. Consolidación de Python
            # Si encuentra "Python 3.x.x" agrupa todo menos el "Launcher"
            m_py = re.match(r'(Python\s\d+\.\d+\.\d+)', nombre, re.IGNORECASE)
            if m_py and 'Launcher' not in nombre:
                nombre = f"{m_py.group(1)} (64-bit)"
            
            sw_row = {col: "" for col in sw_cols}
            sw_row.update({
                "nombre": nombre,
                "fabricante": fila[3].strip() if len(fila) > 3 else "",
                "version": fila[4].strip() if len(fila) > 4 else "",
                "categoria": "Software Instalado",
                "cantidad": 1,
                "responsable": responsable,
                "ubicacion": ubicacion,
                "notas": f"Original: {nombre}"
            })
            sw_list.append(sw_row)

    # 4. Finalizar
    if not ip_encontrada:
        ip_encontrada = "IP_No_Detectada"
        
    hw_data["ip_mac"] = f"{ip_encontrada} / {mac_encontrada}".strip(" / ")
    prefijo = ip_encontrada if ip_encontrada != "IP_No_Detectada" else os.path.splitext(archivo_entrada)[0]

    # 5. DataFrames
    df_hw = pl.DataFrame([hw_data]).select(hw_cols)
    
    if sw_list:
        # Polars unirá automáticamente todos los módulos de Python que hemos renombrado igual
        df_sw = pl.DataFrame(sw_list).unique(subset=["nombre", "version"])
        df_sw = df_sw.with_columns(
            pl.format("SW-{}", pl.int_range(1, pl.len() + 1).cast(pl.String).str.zfill(3)).alias("id")
        ).select(sw_cols)
    else:
        df_sw = pl.DataFrame([], schema={col: pl.String for col in sw_cols})

    # 6. Generar nombres y guardar
    nombre_hw = f"{prefijo}_hardware_winaudit_polar.csv"
    nombre_sw = f"{prefijo}_software_winaudit_polar.csv"

    df_hw.write_csv(nombre_hw)
    df_sw.write_csv(nombre_sw)

    print(f"\n[OK] Procesado y Limpiado correctamente:")
    print(f"- IP Detectada: {ip_encontrada}")
    print(f"- {nombre_hw}")
    print(f"- {nombre_sw} ({len(df_sw)} programas tras la limpieza)")

if __name__ == "__main__":
    procesar_winaudit_polar()