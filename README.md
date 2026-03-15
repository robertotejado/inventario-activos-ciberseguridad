# 🛡️ Inventario de Activos — Ciberseguridad (ENS / NIS2 / OT)

Una herramienta de escritorio multiplataforma diseñada para facilitar a los auditores, CISOs y equipos de IT/OT la gestión de sus activos tecnológicos, garantizando el cumplimiento normativo.

Desarrollada en **Python** con una interfaz moderna tipo **Fluent/WinUI 3**, ofrece una base de datos local y autónoma (sin dependencias en la nube) orientada a la privacidad.

## ✨ Características Principales

* **Cumplimiento ENS (RD 311/2022):** Valoración integrada de las 5 dimensiones (Disponibilidad, Integridad, Confidencialidad, Autenticidad, Trazabilidad).
* **Adaptado a la Directiva NIS2:** Gestión de RTOs, criticidad de la cadena de suministro y dependencias entre sistemas.
* **Módulo OT/ICS Exclusivo:** Control de activos industriales basado en el Modelo Purdue, visibilidad de conectividad IT/Internet y evaluación de riesgos físicos (Safety).
* **Dashboard Analítico:** KPIs en tiempo real para visualizar rápidamente los activos críticos y el estado de la red.
* **Exportación para Auditorías:** Generación de informes en Excel (`.xlsx`) listos para entregar.
* **Privacidad Total:** Los datos se guardan en un archivo JSON local en tu máquina. Nada sale a internet.

## 📦 Descargas e Instalación

### 🪟 Windows
Descarga el instalador desde la sección de **Releases**.
1. Descarga `InventarioActivos_Setup.exe` (Estándar) o `InventarioActivosRetro_Setup.exe` (Modo oscuro).
2. Ejecuta el instalador y sigue los pasos.
3. El programa creará un acceso directo en tu escritorio.

### 🐧 Linux (Debian / Ubuntu)
1. Descarga el paquete `inventarioactivos.deb` desde **Releases**.
2. Instálalo usando dpkg:
   `sudo dpkg -i inventarioactivos.deb`
3. Si faltan dependencias, ejecuta:
   `sudo apt-get install -f`

### 📱 Android
*Versión móvil en desarrollo. ¡Próximamente!*



## 👨‍💻 Autor y Licencia

**Roberto Tejado Busto**
* [LinkedIn](https://www.linkedin.com/in/roberto-tejado/)
* [GitHub](https://github.com/robertotejado)

Este proyecto se distribuye bajo la **Licencia MIT**. Siéntete libre de usarlo, modificarlo y compartirlo, manteniendo siempre los créditos del autor original.
