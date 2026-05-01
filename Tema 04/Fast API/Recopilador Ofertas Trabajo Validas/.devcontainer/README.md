# Dev Container Setup

## ¿Qué es un Dev Container?

Dev Containers permite desarrollar **dentro de un contenedor Docker** desde VSCode. Tienes un entorno aislado y reproducible sin contaminar tu máquina local.

## Requisitos

- **VSCode** (cualquier versión reciente)
- **Remote - Containers extension** (VSCode instalará automáticamente)
- **Docker Desktop** ejecutándose

## Primeros pasos

### 1. Abrir el repo en VSCode

```powershell
code .
```

### 2. VSCode detectará el Dev Container

Verás una notificación azul:
```
Workspace folder contains a dev container configuration file.
```

Haz clic en **"Reopen in Container"** o:
- Pulsa `F1` → `Dev Containers: Reopen in Container`

### 3. Espera a que se construya la imagen

- Primera vez: ~2-3 minutos (descarga imagen + instala dependencias)
- Siguientes veces: ~30 segundos (caché de Docker)

### 4. Verás en la esquina inferior izquierda

```
[Dev Container] Job Offers Intelligence
```

✅ **Ya estás dentro del contenedor**

## Ejecutar el proyecto

### Terminal 1 - Backend

```bash
source .venv/bin/activate
python main.py
```

### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

### Abrir nuevas terminales en VSCode

- `Ctrl + `` (backtick) abre/cierra terminal
- `Ctrl + Shift + `` abre nueva terminal
- Puedes tener múltiples terminales abiertas

## URLs de acceso

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:7860 |
| Health Check | http://localhost:7860/health |

## Características

✅ Python 3.12 + Node 22 pre-instalados  
✅ LaTeX instalado (para CV a PDF)  
✅ Extensiones VSCode automáticas:
   - Python + Pylance + Black formatter
   - ESLint + Prettier
   - Tailwind CSS
   - GitHub Copilot

✅ Variables de entorno pre-configuradas  
✅ Port forwarding automático (5173, 7860)  
✅ Git integrado

## Archivos de configuración

| Archivo | Propósito |
|---------|-----------|
| `devcontainer.json` | Configuración principal del dev container |
| `Dockerfile` | Imagen Docker (Python 3.12 + Node 22) |
| `post-create.sh` | Script que se ejecuta después de crear el contenedor |

## Troubleshooting

### "Remote Container Extension not installed"

1. Abre VSCode
2. Extensiones (`Ctrl + Shift + X`)
3. Busca "Dev Containers"
4. Instala la de Microsoft

### El contenedor no se abre

```powershell
# Asegúrate que Docker Desktop está corriendo
docker ps

# Si falla, reinicia Docker Desktop
```

### Puerto ya está en uso

Si 5173 o 7860 ya están ocupados:

```powershell
# Ver qué ocupa el puerto
netstat -ano | findstr :5173

# Matar el proceso (reemplaza PID)
taskkill /PID <PID> /F
```

### Reconstruir el contenedor

```
F1 → Dev Containers: Rebuild Container
```

O eliminar y recrear:
```powershell
# En PowerShell (fuera del contenedor)
docker ps -a
docker rm <container_id>
```

## Dentro vs Fuera del Contenedor

| Acción | Dentro Container | Fuera Container |
|--------|-----------------|-----------------|
| Editar código | ✅ Sí (automático) | ✅ Sí (automático) |
| pip install | ✅ Sí (en .venv) | ❌ No (se pierde) |
| npm install | ✅ Sí (en container) | ❌ No (se pierde) |
| git commit | ✅ Sí | ✅ Sí |
| Extensiones VSCode | ✅ Dentro | ❌ Fuera no funciona igual |

## Desactivar Dev Container

Para volver a tu entorno local:
- `F1` → `Dev Containers: Reopen Folder Locally`

El contenedor se sigue guardando, puedes volver cuando quieras.

## Más información

- [VSCode Dev Containers Docs](https://code.visualstudio.com/docs/remote/containers)
- [devcontainers.json Reference](https://containers.dev/implementors/json_reference/)
