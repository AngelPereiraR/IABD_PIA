# Guía de Pruebas E2E

## Requisitos Previos

- Backend FastAPI ejecutándose en `http://localhost:7860` (puerto configurado en `.env`)
- Servidor de desarrollo frontend en `http://localhost:5173`
- Base de datos PostgreSQL conectada via `DATABASE_URL` en `.env`
- `data/cv_usuario.pdf` debe existir (requerido para análisis)
- Variables de entorno `.env` configuradas correctamente

---

## 🚀 Configuración e Inicio

### 1. Iniciar el Backend

```bash
# Con entorno virtual activado
python main.py
# O directamente con uvicorn
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

Verificar health en: `http://localhost:7860/health`

### 2. Iniciar el Servidor Frontend

```bash
cd frontend
npm run dev
```

Acceder a: `http://localhost:5173`

---

## ✅ Checklist de Pruebas Manuales

### Suite 1: Autenticación

#### 1.1 Registro de Usuario
- [ ] Navegar a `/auth/register`
- [ ] Rellenar nombre, email y contraseña
- [ ] Enviar formulario
- [ ] Debe redirigir al dashboard
- [ ] Verificar info del usuario en el sidebar

#### 1.2 Inicio de Sesión
- [ ] Navegar a `/auth/login`
- [ ] Introducir email y contraseña registrados
- [ ] Hacer click en "Login"
- [ ] Debe redirigir al dashboard
- [ ] Verificar token en localStorage

#### 1.3 Persistencia de Sesión
- [ ] Después del login, recargar la página
- [ ] El usuario debe seguir autenticado
- [ ] Comprobar que token y usuario están en localStorage

#### 1.4 Cierre de Sesión
- [ ] Hacer click en el botón de logout (navbar superior)
- [ ] Debe redirigir a la landing page
- [ ] localStorage debe quedar limpio
- [ ] Intentar acceder a `/dashboard` debe redirigir al login

#### 1.5 Expiración del Token
- [ ] Eliminar manualmente el token de localStorage
- [ ] Intentar acceder a una ruta protegida
- [ ] Debe redirigir al login

---

### Suite 2: Gestión del CV

#### 2.1 Subida de CV
- [ ] Navegar a `/dashboard/cv`
- [ ] Arrastrar y soltar un archivo PDF válido
- [ ] O hacer click en el área de subida y seleccionar archivo
- [ ] Debe mostrar el estado "CV subido"
- [ ] Debe aparecer la previsualización con información del archivo

#### 2.2 Archivo Inválido
- [ ] Intentar subir un archivo que no sea PDF
- [ ] Debe mostrarse un mensaje de error
- [ ] El error debe indicar tipo de archivo o tamaño inválido

#### 2.3 Previsualización del CV
- [ ] Tras una subida exitosa
- [ ] La previsualización debe mostrar el nombre del archivo
- [ ] El botón de eliminar debe ser visible

#### 2.4 Eliminación del CV
- [ ] Hacer click en el botón de eliminar
- [ ] Aparece diálogo de confirmación
- [ ] Confirmar la eliminación
- [ ] El CV debe quedar eliminado
- [ ] El estado debe cambiar a "Sin CV"

#### 2.5 Guarda de CV Requerido
- [ ] Sin CV subido, navegar a `/dashboard/analysis`
- [ ] Debe redirigir a `/dashboard/cv`

---

### Suite 3: Análisis de Ofertas de Empleo

#### 3.1 Análisis por URL
- [ ] Navegar a `/dashboard/analysis`
- [ ] Seleccionar la pestaña "URL"
- [ ] Pegar una URL de oferta válida (ej. LinkedIn, InfoJobs)
- [ ] Hacer click en "Analizar Oferta"
- [ ] Debe aparecer el spinner de carga
- [ ] Los resultados deben mostrar:
  - [ ] Título del puesto
  - [ ] Empresa
  - [ ] Puntuación de ajuste (0-100) con banda de clasificación:
    - 0-59 → ATS_BLOCK (rechazo automático)
    - 60-69 → Descarte (pasa ATS, débil en evaluación humana)
    - 70-79 → Apto
    - 80-89 → Fuerte
    - 90-100 → Ideal
  - [ ] Estado Válido/No apto (`is_valid = score >= 60`)
  - [ ] Salario (si está disponible)
  - [ ] Beneficios (si están disponibles)
  - [ ] Habilidades clave extraídas (hasta 10)

#### 3.2 Análisis por Texto
- [ ] Seleccionar la pestaña "Texto"
- [ ] Pegar la descripción de la oferta (50-5000 caracteres)
- [ ] Hacer click en "Analizar Oferta"
- [ ] Los resultados deben mostrar los mismos campos que el análisis por URL

#### 3.3 Validación del Formulario
- [ ] Intentar enviar el formulario vacío → Debe mostrar error
- [ ] Intentar texto corto (<50 caracteres) → Debe mostrar error
- [ ] Intentar URL inválida → Debe mostrar error

#### 3.4 Historial de Análisis
- [ ] Crear varios análisis
- [ ] Navegar a `/dashboard/analysis/history`
- [ ] Debe mostrar lista paginada
- [ ] Cada elemento debe mostrar:
  - [ ] Badge con la puntuación
  - [ ] Título y empresa
  - [ ] Badge Válido/No apto
  - [ ] Botón "Ver"

#### 3.5 Paginación del Historial
- [ ] Crear más de 10 análisis
- [ ] El historial debe paginar (límite 10 por página)
- [ ] Los botones Anterior/Siguiente deben funcionar
- [ ] El número de página debe actualizarse

#### 3.6 Ver Análisis Específico
- [ ] Desde el historial, hacer click en "Ver" en un elemento
- [ ] Debe navegar a `/dashboard/analysis/:id`
- [ ] Debe mostrar la tarjeta de resultado detallada
- [ ] Si is_valid=true (score >= 60), mostrar botón "Generar Adaptación de CV"
- [ ] Si is_valid=false, mostrar mensaje de que la oferta no supera el umbral mínimo

---

### Suite 4: Adaptación del CV

#### 4.1 Generar Adaptación
- [ ] Ver el resultado de una oferta válida (is_valid=true, score ≥ 60)
- [ ] Hacer click en el botón "Generar Adaptación de CV"
- [ ] Navegar a `/dashboard/adaptations/generate/:analysisId`
- [ ] Debe aparecer el spinner de carga con texto "Generando..."
- [ ] **⏱️ Esperar 30-60 segundos** (adaptación + compilación LaTeX)
  - Adaptación DeepSeek: 10-20s
  - Compilación LaTeX: 20-40s
- [ ] Tras la generación, debe redirigir a `/dashboard/adaptations/:adaptationId`

#### 4.2 Vista de Detalle de Adaptación
- [ ] Navegar a `/dashboard/adaptations/:adaptationId`
- [ ] Debe mostrar:
  - [ ] Título del puesto y empresa
  - [ ] Previsualización del CV adaptado (componente AdaptationPreview)
  - [ ] Botón "Descargar PDF" (descarga desde Cloudinary)
  - [ ] Botón "Volver" (navega al historial o al resultado del análisis según contexto)
- [ ] La descarga del PDF debe funcionar (ver 4.4)

#### 4.3 Historial de Adaptaciones
- [ ] Navegar a `/dashboard/adaptations` (a través de "Mis Adaptaciones" en el sidebar)
- [ ] Debe mostrar la lista paginada de todas las adaptaciones anteriores (AdaptationsHistoryPage)
- [ ] Cada elemento debe mostrar:
  - [ ] Título del puesto
  - [ ] Empresa
  - [ ] Fecha de creación
  - [ ] Al hacer click en la tarjeta (CardItem) debe navegar a la vista de detalle
- [ ] Pagination via URL param `?page=N` — Previous/Next buttons con ChevronLeft/ChevronRight
- [ ] Muestra total count y mensaje "No adapted CVs yet" cuando está vacío

#### 4.4 Descarga de PDF
- [ ] En la página de detalle, el componente AdaptationPreview debe renderizar el CV adaptado
- [ ] Hacer click en el botón "Descargar PDF" (PDFDownloadButton)
- [ ] El PDF se sirve desde Cloudinary (URL almacenada en `adapted_cv_url`)
- [ ] El PDF está generado vía compilación LaTeX — verificar que es legible y bien formateado
- [ ] El nombre del archivo corresponde a la oferta analizada

#### 4.5 Oferta No Válida
- [ ] Para ofertas no válidas (is_valid=false), el botón de adaptación no debe aparecer
- [ ] Si se navega directamente debe mostrar mensaje de oferta no válida

---

### Suite 5: Perfil y Configuración

#### 5.1 Página de Perfil
- [ ] Navegar a `/dashboard/profile` a través del sidebar
- [ ] Debe mostrar la información del usuario:
  - [ ] Dirección de email
  - [ ] Fecha de creación de la cuenta
  - [ ] Información de último acceso
- [ ] El perfil debe cargarse sin errores

---

### Suite 6: UI/UX

#### 6.1 Navegación
- [ ] Los enlaces del sidebar deben funcionar:
  - [ ] Dashboard → `/dashboard`
  - [ ] Mi CV → `/dashboard/cv`
  - [ ] Analizar Ofertas → `/dashboard/analysis`
  - [ ] Mis Adaptaciones → `/dashboard/adaptations`
  - [ ] Perfil → `/dashboard/profile`
- [ ] El estado activo debe resaltar la página actual
- [ ] El logo debe navegar a inicio (`/`)

#### 6.2 Diseño Responsive
- [ ] Probar en móvil (375px de ancho)
- [ ] Probar en tablet (768px de ancho)
- [ ] Probar en escritorio (1920px de ancho)
- [ ] El sidebar debe colapsar en móvil
- [ ] Los formularios deben apilarse verticalmente

#### 6.3 Manejo de Errores
- [ ] Error de red → Debe mostrar mensaje amigable al usuario
- [ ] 401 No autorizado → Debe redirigir al login
- [ ] 404 No encontrado → Debe mostrar mensaje de "No encontrado"
- [ ] 429 Demasiadas peticiones → Debe mostrar mensaje de límite de tasa
- [ ] 500 Error del servidor → Debe mostrar "Inténtalo más tarde"

#### 6.4 Estados de Carga
- [ ] Formulario de auth: texto del botón "Iniciando sesión..." / "Registrando..."
- [ ] Subida de CV: spinner de progreso visible
- [ ] Análisis: componente Spinner con texto "Analizando..." (⏱️ 12-25 segundos)
- [ ] Generación de adaptación: componente Spinner con texto "Generando..." (⏱️ 30-60 segundos)
  - Debe mostrar mensaje informativo sobre el tiempo esperado
  - Spinner debe mantener usuario informado durante espera
- [ ] Transiciones de página: Spinner con texto "Cargando..."

#### 6.5 Notificaciones Toast
- [ ] Mensaje de éxito tras el login
- [ ] Mensaje de error si falla la subida
- [ ] Confirmación tras eliminar el CV
- [ ] Mensaje de error ante fallos de la API

---

## 🔍 Pruebas con DevTools del Navegador

### 1. Pestaña de Red (Network)
- [ ] Verificar que todas las llamadas a la API van a `http://localhost:7860` (configurado en `apiClient.js`)
- [ ] Comprobar que las cabeceras incluyen `Authorization: Bearer <token>` (añadido por interceptor)
- [ ] Verificar los códigos de respuesta HTTP (200, 201, 400, 401, 422, 429, etc.)
- [ ] Comprobar que los payloads de respuesta coinciden con la estructura esperada

### 2. Pestaña de Aplicación (Application)
- [ ] El localStorage debe contener:
  - [ ] `token` (cadena JWT)
  - [ ] `user` (JSON con email, id, etc.)
- [ ] Verificar que los datos se limpian al cerrar sesión

### 3. Consola (Console)
- [ ] Sin errores de JavaScript
- [ ] Sin errores 404 de assets
- [ ] Comprobar si hay advertencias de deprecación

---

## 🚨 Escenarios de Error

### Escenario 1: Sin Conexión a la Red
1. Deshabilitar la red en DevTools del navegador
2. Intentar analizar una oferta
3. Debe mostrar mensaje de "Error de red"
4. Volver a habilitar la red, el reintento debe funcionar

### Escenario 2: Token Inválido
1. Iniciar sesión correctamente
2. Modificar manualmente el token en localStorage (corromperlo)
3. Intentar una llamada a la API
4. Debe obtener 401 y redirigir al login

### Escenario 3: Múltiples Pestañas
1. Iniciar sesión en la pestaña A
2. Abrir la app en la pestaña B
3. Ambas deben estar autenticadas
4. Cerrar sesión en la pestaña A
5. La pestaña B también debe cerrar sesión en la próxima acción

---

## 📊 Pruebas de Rendimiento

### Rendimiento del Build
```bash
npm run build
# Comprobar tamaño de la carpeta dist/ (objetivo: <500KB)
# Comprobar tamaño gzip (objetivo: <150KB)
```

### Rendimiento en Tiempo de Ejecución
1. Abrir DevTools → Pestaña Rendimiento (Performance)
2. Analizar la carga inicial de la página
3. Analizar la navegación entre páginas
4. Comprobar fugas de memoria (abrir múltiples análisis)

---

## 📝 Plantilla de Informe de Pruebas

Crear `tests/E2E_RESULTS.md`:

```markdown
# Resultados de Pruebas E2E

**Fecha:** AAAA-MM-DD  
**Tester:** Nombre  
**Versión Frontend:** [git commit]  
**Versión Backend:** [git commit]

## Suites de Prueba

### Suite 1: Autenticación ✅/❌
- Registro: ✅/❌
- Login: ✅/❌
- Persistencia de sesión: ✅/❌
- Logout: ✅/❌
- Expiración de token: ✅/❌

### Suite 2: Gestión de CV ✅/❌
- Subida: ✅/❌
- Archivo inválido: ✅/❌
- Previsualización: ✅/❌
- Eliminación: ✅/❌
- Guarda de CV requerido: ✅/❌

### Suite 3: Análisis ✅/❌
- Análisis por URL: ✅/❌
- Análisis por texto: ✅/❌
- Validación del formulario: ✅/❌
- Listado del historial: ✅/❌
- Paginación: ✅/❌
- Ver resultado específico: ✅/❌

### Suite 4: Adaptación ✅/❌
- Generar adaptación: ✅/❌
- Vista de detalle: ✅/❌
- Historial/Lista: ✅/❌
- Previsualización: ✅/❌
- Descarga de PDF: ✅/❌

### Suite 5: Perfil ✅/❌
- Carga de la página de perfil: ✅/❌
- Visualización de datos del usuario: ✅/❌

### Suite 6: UI/UX ✅/❌
- Navegación: ✅/❌
- Diseño responsive: ✅/❌
- Manejo de errores: ✅/❌
- Estados de carga: ✅/❌
- Notificaciones toast: ✅/❌

## Incidencias Encontradas
- [Incidencia #1 - Descripción]
- [Incidencia #2 - Descripción]

## Notas
- Rendimiento bueno/aceptable/necesita mejoras
- Sin problemas bloqueantes graves
```

---

## 🎯 Criterios de Éxito

Todas las pruebas pasan cuando:
- ✅ Todos los flujos de autenticación funcionan
- ✅ Gestión de CV funcional (subida, previsualización, eliminación)
- ✅ El análisis crea resultados correctamente con scoring de 5 bandas
- ✅ La adaptación genera y descarga PDFs vía LaTeX/Cloudinary
- ✅ Responsive en todos los tamaños de pantalla
- ✅ Sin errores de JavaScript en la consola
- ✅ Todas las llamadas a la API son exitosas
- ✅ Los mensajes de error son claros y útiles
- ✅ Los estados de carga son visibles
- ✅ La gestión de sesión funciona correctamente

---

## 📍 Rutas de la Aplicación

### Rutas Públicas
- `/` - Landing page
- `/auth/login` - Página de login (redirige a `/dashboard` si ya tiene token)
- `/auth/register` - Página de registro (redirige a `/dashboard` si ya tiene token)
- `/auth/google-callback` - Manejador de callback OAuth de Google

### Rutas Protegidas (Solo requieren autenticación)
- `/dashboard` - Dashboard principal
- `/dashboard/cv` - Gestión del CV (subida, vista, eliminación)
- `/dashboard/profile` - Página de perfil del usuario

### Rutas Protegidas (Requieren autenticación + CV subido)
- `/dashboard/analysis` - Create job offer analysis
- `/dashboard/analysis/:id` - View analysis results
- `/dashboard/analysis/history` - View all past analyses (paginado)
- `/dashboard/adaptations` - Historial de adaptaciones (AdaptationsHistoryPage, paginado)
- `/dashboard/adaptations/:adaptationId` - Ver adaptación específica + descarga PDF
- `/dashboard/adaptations/generate/:analysisId` - Generar adaptación desde un análisis válido

---

## 🔗 Enlaces Rápidos

### Desarrollo Local
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:7860`
- Backend Docs (Swagger): `http://localhost:7860/docs`
- Backend ReDoc: `http://localhost:7860/redoc`
- Health check: `http://localhost:7860/health`

### Producción
- Frontend: `https://opticv.vercel.app`
- Backend: `https://opticv-engine.hf.space`
- Health check: `https://opticv-engine.hf.space/health`
