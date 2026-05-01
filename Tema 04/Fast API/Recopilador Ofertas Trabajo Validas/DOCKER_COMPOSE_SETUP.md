# Docker Compose Setup - Windows con PowerShell

## Requisitos

- **Docker Desktop** instalado en Windows (incluye docker-compose)
- **PowerShell** (ya instalado en Windows 11)
- **.env file** en la raíz del proyecto con todas las variables de entorno

## Configuración Inicial

### 1. Verificar Docker Desktop está corriendo
```powershell
docker --version
docker-compose --version
```

### 2. Preparar variables de entorno
Asegúrate de que `.env` existe en la raíz del proyecto con:
```
DATABASE_URL=postgresql://...
DEEPSEEK_API_KEY=...
GOOGLE_CREDENTIALS_JSON=...
GOOGLE_TOKEN_JSON=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
JINA_API_KEY=...
FIRECRAWL_API_KEY=...
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

## Comandos en PowerShell

### Iniciar containers en foreground (ver logs en vivo)
```powershell
docker-compose up
```

### Iniciar containers en background
```powershell
docker-compose up -d
```

### Ver logs en tiempo real
```powershell
docker-compose logs -f
```

### Ver logs de un servicio específico
```powershell
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Detener containers
```powershell
docker-compose down
```

### Detener y limpiar volúmenes
```powershell
docker-compose down -v
```

### Reconstruir imágenes (si hay cambios en Dockerfile)
```powershell
docker-compose build --no-cache
```

### Reiniciar un servicio
```powershell
docker-compose restart backend
docker-compose restart frontend
```

## Acceso a la Aplicación

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:5173 | Vite dev server (hot reload) |
| Backend API | http://localhost:7860 | FastAPI server |
| Backend Health | http://localhost:7860/health | Health check |

## Verificar que está corriendo

```powershell
# Ver containers activos
docker ps

# Verificar logs
docker-compose logs
```

## Entrar en un container (debugging)

```powershell
# Backend Python
docker-compose exec backend bash

# Frontend Node
docker-compose exec frontend sh
```

## Troubleshooting

### Puerto ya está en uso
```powershell
# Ver qué ocupa puerto 5173
netstat -ano | findstr :5173

# Ver qué ocupa puerto 7860
netstat -ano | findstr :7860

# Matar proceso por PID
taskkill /PID <PID> /F
```

### Contenedor no inicia
```powershell
# Ver logs detallados
docker-compose logs backend
docker-compose logs frontend

# Reconstruir sin caché
docker-compose build --no-cache
docker-compose up
```

### Limpiar todo y empezar de nuevo
```powershell
docker-compose down -v
docker system prune -a --volumes
docker-compose up --build
```

## Despliegue en Producción

### HF Spaces (Backend)
- Usa el `Dockerfile` (para backend)
- HF construye automáticamente desde el repositorio

### Vercel (Frontend)
- El frontend en `frontend/` se despliega directo desde Vercel
- No necesita Docker (Vercel lo construye con `npm run build`)
- Configuración está en `frontend/vercel.json`

## Notes

- **Hot reload**: Cambios en `frontend/src` se recargan automáticamente en http://localhost:5173
- **Volúmenes**: `./data` está sincronizado entre host y container
- **Credenciales**: `credentials.json` y `token.json` se copian en READ-ONLY (no escribibles desde container)
