# Ticketera de Pendientes (Desktop local para Windows)

Aplicativo de escritorio para gestionar tareas en formato de cards, con persistencia local y creación automática vía webhook.

## ¿Por qué SQLite en vez de CSV?
SQLite es mejor para este caso porque mantiene integridad de datos, permite filtros/consultas robustas (prioridad/estado/histórico), evita errores de concurrencia comunes en CSV y facilita escalar o migrar el modelo sin romper compatibilidad.

## Arquitectura propuesta
- **GUI:** Tkinter (`app/gui.py`)
- **Persistencia local:** SQLite (`app/database.py`) en `<carpeta del exe>/data/cards.db`
- **Webhook local:** Flask (`app/webhook_server.py`) en `http://127.0.0.1:5000/webhook/card`
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
│   ├── gui.py
│   └── webhook_server.py
├── tests/
│   ├── test_database.py
│   └── test_webhook.py
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

## Funcionalidades implementadas
- Creación manual de cards con:
  - título
  - descripción
  - prioridad (Alta/Media/Baja)
  - estado (No iniciado/Pendiente/Terminado)
  - fecha de creación (automática)
  - fecha de término (automática al pasar a Terminado)
- Vista principal con cards activas (No iniciado, Pendiente)
- Histórico con cards terminadas
- Filtros en vista activa por prioridad y estado
- Edición de cards
- Cambio rápido de estado
- Eliminación permanente (UI + SQLite, sin papelera)
- Persistencia local: los datos permanecen al reiniciar la app
- Webhook local para alta automática desde n8n

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

## Webhook local para n8n

### Endpoint
- `POST http://127.0.0.1:5000/webhook/card`

### JSON mínimo

```json
{
  "titulo": "Responder correo urgente",
  "descripcion": "Cliente solicita respuesta sobre avance del proyecto",
  "prioridad": "Alta"
}
```

### JSON con estado opcional

```json
{
  "titulo": "Responder correo urgente",
  "descripcion": "Cliente solicita respuesta sobre avance del proyecto",
  "prioridad": "Alta",
  "estado": "No iniciado"
}
```

> Si `estado` no llega, se usa `No iniciado`. Si no llega `fecha_creacion`, se genera automáticamente.

### Ejemplo rápido en n8n
- Nodo previo (ej. Gmail) detecta correo por condición.
- Nodo **HTTP Request**:
  - Method: `POST`
  - URL: `http://127.0.0.1:5000/webhook/card`
  - Body Content Type: `JSON`
  - Body:

```json
{
  "titulo": "{{$json.subject}}",
  "descripcion": "{{$json.text}}",
  "prioridad": "Alta",
  "estado": "No iniciado"
}
```

## Validación rápida

```bash
python -m unittest discover -v
```

## Primera versión funcional mínima (MVP)
Esta versión ya cumple:
- operación 100% local
- gestión completa de cards activas e histórico
- persistencia local robusta
- integración webhook local

## Sugerencias de mejora
- Drag & drop tipo Kanban por columnas de estado
- Backup/restore de base SQLite desde la UI
- Exportación CSV/PDF
- Búsqueda de texto completo y etiquetas
