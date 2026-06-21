# Ticketera de Pendientes (Desktop local para Windows)

Aplicativo de escritorio para gestionar tareas en formato de cards, con persistencia local SQLite.

## ¿Por qué SQLite en vez de CSV?
SQLite es mejor para este caso porque mantiene integridad de datos, permite filtros/consultas robustas (prioridad/estado/histórico), evita errores de concurrencia comunes en CSV y facilita escalar o migrar el modelo sin romper compatibilidad.

## Arquitectura
- **GUI:** Tkinter (`app/gui.py`) — diseño inspirado en [ui-test-copy](https://github.com/alesoander/ui-test-copy), con cards, header, navegación y badges de prioridad/estado.
- **Persistencia local:** SQLite (`app/database.py`) en `<carpeta del exe>/data/cards.db`
- **Punto de entrada:** `main.py`

## Estructura del proyecto

```text
Ticketera-de-pendientes/
├── .github/
│   └── workflows/
│       └── build-exe.yml   # CI que genera ticketera.exe en Windows
├── app/
│   ├── constants.py
│   ├── database.py
│   └── gui.py
├── tests/
│   └── test_database.py
├── build.ps1               # script de compilación para el desarrollador
├── main.py
├── requirements.txt
├── ticketera.spec          # configuración reproducible de PyInstaller
└── README.md
```

## Uso para el usuario final (doble clic)

1. Descarga `ticketera.exe` desde la pestaña **Releases** de este repositorio
   (o del artefacto del último workflow en la pestaña **Actions**).
2. Coloca el archivo en cualquier carpeta donde tengas permisos de escritura
   (por ejemplo `Documentos\Ticketera\`).
3. Haz **doble clic** en `ticketera.exe`.
4. La base de datos SQLite se crea automáticamente en
   `<carpeta donde está el .exe>\data\cards.db` la primera vez que abres la app.

> No se requiere instalar Python, pip, ni ninguna dependencia. No se abre
> ninguna ventana de consola.

## Funcionalidades
- Creación de tareas con:
  - título
  - descripción
  - prioridad (Alta / Media / Baja)
  - estado (No iniciado / Pendiente / Terminado)
  - fecha de creación (automática)
  - fecha de término (automática al pasar a Terminado)
- Vista **Activas**: tareas con estado No iniciado o Pendiente, en formato cards
- Vista **Histórico**: tareas terminadas con fecha de creación y completado
- Filtros en vista Activa por prioridad y estado
- Filtro en Histórico por prioridad
- Edición de tareas desde el menú de cada card
- Cambio de estado directo desde el badge de estado en la card
- Eliminación permanente (UI + SQLite, sin papelera)
- Persistencia local: los datos permanecen al reiniciar la app

## Ejecución local desde código fuente (desarrolladores)

1. Crear y activar entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

> La app solo usa la biblioteca estándar de Python (`tkinter`, `sqlite3`), por lo que
> no hay dependencias externas que instalar.

3. Ejecutar app:

```powershell
python main.py
```

## Compilar el `.exe` manualmente

### Opción A — script automático (recomendado)

Ejecuta el script de build incluido. Crea el entorno virtual, instala todo y
genera el ejecutable en un solo paso:

```powershell
.\build.ps1
```

El ejecutable queda en `dist\ticketera.exe`.

### Opción B — comandos manuales

```powershell
pip install pyinstaller
pyinstaller ticketera.spec
```

Ejecutable generado en:

```text
dist/ticketera.exe
```

## Generación automática de `.exe` con GitHub Actions

El workflow `.github/workflows/build-exe.yml` construye el ejecutable en un
runner de Windows y lo publica automáticamente:

- **En cualquier push de tag** `v*` (ej. `v1.0.0`): crea una GitHub Release y
  adjunta `ticketera.exe`.
- **Manualmente**: abre la pestaña **Actions → Build Windows EXE → Run
  workflow**.

Para publicar una nueva versión:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Validación rápida

```bash
python -m unittest discover -v
```

## Sugerencias de mejora
- Drag & drop tipo Kanban por columnas de estado
- Backup/restore de base SQLite desde la UI
- Exportación CSV/PDF
- Búsqueda de texto completo y etiquetas
