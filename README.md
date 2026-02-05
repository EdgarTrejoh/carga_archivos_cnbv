# Descargador de Boletines de la CNBV -- Banca Múltiple

> **App minimalista en Streamlit** para descargar, en un par de clics, los boletines de la **Banca Múltiple** publicados por la **CNBV**. Seleccionas **año** y **mes**, y listo: el archivo XLSX se guarda localmente.

![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Resumen

Esta herramienta automatiza la descarga de boletines que, de otra forma, implican navegar manualmente por el **Portafolio de Información de la CNBV**. Está pensada para **analistas**, **equipos de datos** e **investigadores** que necesitan construir pipelines o análisis recurrentes con estos archivos.

* **Interfaz interactiva**: construida con **Streamlit**, simple y directa.
* **Código modular**: separación entre capa de UI y lógica de descarga.
* **Configuración segura**: la URL base vive en `.streamlit/secrets.toml`, fuera del código.

> **Nota**: El proyecto no rompe ningún candado ni evita autenticaciones. Solo **descarga archivos públicos** con una convención de nombres establecida por la propia CNBV.

---

## 📦 Requisitos

* **Python 3.10+**
* **pip** (o **pipx/poetry** si prefieres)

Instala dependencias:

```bash
pip install -r requirements.txt
```

> Sugerido: usa un entorno virtual `python -m venv .venv && source .venv/bin/activate` (en Windows: `.venv\\Scripts\\activate`).

---

## 🧰 Estructura del proyecto

```
.
├── .streamlit/
│   └── secrets.toml            # Configuración (BASE_URL)
├── descargas_cnbv/             # Carpeta destino de los boletines
│   └── .gitkeep                # Mantener el directorio en Git
├── main.py                      # Interfaz Streamlit
├── cnbv_downloader.py          # Lógica de descarga
└── requirements.txt            # Dependencias
```

* **`main.py`**: lógica de la interfaz (widgets, validaciones, mensajes). Se ejecuta con `streamlit run main.py`.
* **`cnbv_downloader.py`**: funciones puras para construir URL, validar parámetros y descargar el archivo.
* **`.streamlit/secrets.toml`**: variables de configuración. **No** lo subas a repos públicos.
* **`descargas_cnbv/`**: destino por defecto de los archivos descargados.

---

## 🔐 Configuración (secrets)

Crea el archivo `.streamlit/secrets.toml` en la raíz del proyecto con **la URL patrón** que usa CNBV para los boletines (ajústala si cambia en el portal):

```toml
# .streamlit/secrets.toml
BASE_URL = "inserta_liga"
```

> Si la CNBV modifica rutas o nombres, actualiza `BASE_URL` sin tocar el código.

---

## ▶️ Ejecución

1. Activa tu entorno y corre Streamlit:

```bash
streamlit run main.py
```

2. En el navegador:

* Elige **Año** y **Mes**.
* Clic en **Descargar Boletín**.
* El archivo se guardará en `./descargas_cnbv/` 

> La app muestra mensajes de éxito/error y valida formato de fechas.

---

## 🧱 Buenas prácticas incluidas

* **Validaciones**: año/mes, existencia de carpeta, sobrescritura opcional.
* **Manejo de errores**: respuestas HTTP no exitosas, tiempo de espera, cambios de ruta.
* **Registro** (opcional): puedes agregar `logging` a `cnbv_downloader.py` para bitácoras.

Ejemplo mínimo de logging:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
```
---

## ⚖️ Aviso y uso responsable

Los archivos descargados son públicos y provienen del portal de la CNBV.

Verifica siempre términos de uso y frecuencia de acceso razonable.

Si automatizas descargas periódicas, respeta ventanas y evita sobrecargar el servidor.

CNBV: Comisión Nacional Bancaria y de Valores (México). Portal de referencia: "Portafolio de Información".

---

## 📄 Licencia

Este proyecto se distribuye bajo la Licencia MIT. Consulta el archivo LICENSE si se incluye en el repo.

---

## 🧩 Créditos

Diseño e implementación: [![LinkedIn](https://img.shields.io/badge/LinkedIn-Edgar%20Trejo-blueviolet?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/edgarm-trejoh/)


Datos: CNBV – Portafolio de Información (Banca Múltiple).