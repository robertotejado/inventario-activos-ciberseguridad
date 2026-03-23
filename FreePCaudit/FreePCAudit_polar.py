import polars as pl
import re
import os

def procesar_inventario_manual():
    # 1. Entradas del usuario
    archivo_txt = input("Introduce el nombre del archivo TXT (ej. Mipc.txt): ")
    
    if not os.path.exists(archivo_txt):
        print(f"Error: No se encuentra el archivo '{archivo_txt}' en la carpeta actual.")
        return

    responsable = input("Introduce el responsable o asignado: ")
    ubicacion = input("Introduce la ubicación: ")

    # 2. Leer el archivo con codificación compatible (latin-1)
    with open(archivo_txt, 'r', encoding='latin-1', errors='replace') as f:
        texto = f.read()

    # --- EXTRACCIÓN DE HARDWARE ---
    def buscar(patron, texto_fuente):
        res = re.search(patron, texto_fuente)
        return res.group(1).strip() if res else ""

    # Extraemos la IP para el nombre del archivo (buscando específicamente la de red local)
    ip_extraida = buscar(r"Adapter IP-address:\s+(192\..*)", texto)
    # Si no encuentra IP 192, busca cualquier dirección IP
    if not ip_extraida:
        ip_extraida = buscar(r"Adapter IP-address:\s+(\d+\.\d+\.\d+\.\d+)", texto)
    
    # Prefijo para los archivos de salida
    prefijo = ip_extraida if ip_extraida else os.path.splitext(archivo_txt)[0]

    hostname = buscar(r"Host name:\s+(.*)", texto)
    so = buscar(r"Operating system: (.*)", texto).split('(')[0].strip()
    marca = buscar(r"Manufacturer:\s+(.*)", texto)
    modelo = buscar(r"Model:\s+(.*)", texto)
    serie = buscar(r"Serial number:\s+(.*)", texto)
    cpu = buscar(r"Processor:\s+(.*)", texto).split('(')[0].strip()
    ram = buscar(r"Physical memory:\s+(.*)", texto)
    disco = buscar(r"Disk:\s+(.*?)\s\(", texto)
    mac = buscar(r"Adapter MAC-address:\s+(.*)", texto)

    # Definición de columnas según tu modelo HW
    hw_cols = ['id', 'categoria', 'tipo', 'marca', 'modelo', 'serie', 'hostname', 'ip_mac', 'so', 'asignado', 'ubicacion', 'estado', 'criticidad', 'ens_d', 'ens_i', 'ens_c', 'ens_a', 'ens_t', 'rto', 'crit_prov', 'dependencias', 'fecha', 'notas']
    
    hw_row = {col: "" for col in hw_cols}
    hw_row.update({
        "id": "HW-001",
        "categoria": "Hardware Usuario",
        "tipo": "Ordenador / PC",
        "marca": marca,
        "modelo": modelo,
        "serie": serie,
        "hostname": hostname,
        "ip_mac": f"{ip_extraida} / {mac}",
        "so": so,
        "asignado": responsable,
        "ubicacion": ubicacion,
        "estado": "Activo",
        "notas": f"CPU: {cpu} | RAM: {ram} | Disco: {disco}"
    })

    # --- EXTRACCIÓN DE SOFTWARE ---
    sw_cols = ['id', 'nombre', 'fabricante', 'version', 'categoria', 'tipo_lic', 'cantidad', 'clave', 'caducidad', 'responsable', 'ubicacion', 'criticidad', 'ens_c', 'ens_i', 'ens_d', 'rto', 'crit_prov', 'dependencias', 'notas']
    sw_list = []

    if "SOFTWARE" in texto:
        bloque_sw = texto.split("SOFTWARE")[-1].strip()
        lineas_sw = [l.strip() for l in bloque_sw.split('\n') if l.strip() and "======" not in l]

        contador_sw = 1
        for linea in lineas_sw:
            # Filtro para solo software instalado real
            if any(x in linea for x in ["[Store App]", "Microsoft.Visual C++", "Microsoft.NET", "Microsoft.VCLibs"]):
                continue
            
            match = re.match(r"^(.*?),\sVersion:\s(.*?),\sPublisher:\s(.*)$", linea)
            if match:
                nombre_raw, version, fab_raw = match.groups()
                nombre = nombre_raw.split(',')[0].strip()
                fabricante = fab_raw.split(',')[0].strip()
                
                sw_row = {col: "" for col in sw_cols}
                sw_row.update({
                    "id": f"SW-{contador_sw:03d}",
                    "nombre": nombre,
                    "fabricante": fabricante,
                    "version": version,
                    "categoria": "Software Instalado",
                    "cantidad": 1,
                    "responsable": responsable,
                    "ubicacion": ubicacion,
                    "notas": linea
                })
                sw_list.append(sw_row)
                contador_sw += 1

    # 3. Guardar con el formato IP_hardware_polar.csv e IP_software_polar.csv
    nombre_hw = f"{prefijo}_hardware_polar.csv"
    nombre_sw = f"{prefijo}_software_polar.csv"

    df_hw = pl.DataFrame([hw_row]).select(hw_cols)
    df_sw = pl.DataFrame(sw_list).select(sw_cols)

    df_hw.write_csv(nombre_hw)
    df_sw.write_csv(nombre_sw)

    print(f"\n[OK] Generados con éxito:")
    print(f"- {nombre_hw}")
    print(f"- {nombre_sw}")

if __name__ == "__main__":
    procesar_inventario_manual()