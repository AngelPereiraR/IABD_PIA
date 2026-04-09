# Testing Guide - Plan 01 y Plan 02

---

## Plan 02 Tests (Nuevo)

### Ejecutar Tests Plan 02
```bash
python tests/test_plan_02_apis.py
```

### Características
- ✅ 29 tests funcionales (unittest)
- ✅ Sin pytest
- ✅ Cobertura completa del Paso 0
- ✅ Validación de estructura modular
- ✅ Salida clara y detallada

### Tests Incluidos (29 Total)

**TestPlan02Schemas (4 tests)**
- OfferDetail model structure
- CVUploadResponse validation
- CVGenerationResponse validation

**TestPlan02Dependencies (2 tests)**
- get_user_id callable
- get_user_id is async

**TestPlan02Routes (6 tests)**
- CV router exists and has routes
- Offers router exists and has routes
- Upload endpoint registered
- Generate endpoint registered
- List offers endpoint registered

**TestPlan02APIEndpoints (5 tests)**
- main.py imports without errors
- cv_router included
- offers_router included
- Health endpoint exists
- Home endpoint exists

**TestPlan02Integration (6 tests)**
- API module structure correct
- Schemas exports available
- Routes imports working
- Dependencies functions exist
- Endpoint methods correct (POST/GET)

**TestPlan02FileStructure (6 tests)**
- __init__.py files content validated
- CV router file structure
- Offers router file structure
- Routes organization

---

## Plan 01 Tests Simplificados (Recomendado)

### Ejecutar Tests Plan 01
```bash
python tests/test_plan_01_simple.py
```

### Características
- ✅ Sin dependencias de pytest
- ✅ Sin configuración compleja
- ✅ Funciona directamente en Windows
- ✅ 10 tests funcionales
- ✅ Salida clara y legible

### Output Esperado
```
======================================================================
🧪 PLAN 01 - TESTS SIMPLES (sin pytest)
======================================================================

✅ test_imports: Todos los módulos importados
✅ test_telegram_keyboard: Estructura válida
✅ test_database_config: DATABASE_URL válida
✅ test_user_config: Configuración correcta
✅ test_fastapi_endpoints: Todos los endpoints presentes
✅ test_callback_handler: Handler implementado
✅ test_cv_generator_methods: Todos los métodos presentes
✅ test_save_offer_function: Función correcta
✅ test_requirements: Dependencias correctas
✅ test_offer_persistence: Persistencia correcta

======================================================================
📊 RESUMEN DE TESTS
======================================================================
✅ Pasados:  10
❌ Fallidos: 0
⏭️  Saltados: 0
📈 Total:    10

🎉 ¡TODOS LOS TESTS PASARON!
======================================================================
```

## Tests Incluidos (10 Total)

| # | Test | Qué Prueba |
|---|------|-----------|
| 1 | test_imports | Todos los módulos Python importan correctamente |
| 2 | test_telegram_keyboard | Estructura JSON del teclado Telegram |
| 3 | test_database_config | DATABASE_URL configurada en .env |
| 4 | test_user_config | USER_ID y USER_EMAIL válidos |
| 5 | test_fastapi_endpoints | Endpoints GET / , /health, POST /api/generate/{offer_id} |
| 6 | test_callback_handler | Método async handle_generate_cv_callback implementado |
| 7 | test_cv_generator_methods | Métodos generate_for_offer, _compile_latex, _build_latex_template |
| 8 | test_save_offer_function | Función async save_offer_to_db con firma correcta |
| 9 | test_requirements | Dependencias críticas en requirements.txt |
| 10 | test_offer_persistence | Persistencia de ofertas en PostgreSQL (async) |

## Versión Pytest (Alternativa)

Si prefieres usar pytest (requiere configuración adicional en Windows):

```bash
pip install pytest pytest-asyncio
python -m pytest tests/test_plan_01_integration.py -v
```

**Nota:** En Windows, es necesario:
- Archivo `conftest.py` que configura WindowsSelectorEventLoopPolicy
- Archivo `pytest.ini` que configura pytest-asyncio

## Comparación

| Aspecto | Simple | Pytest |
|---------|--------|--------|
| Setup | 0 pasos | Requiere conftest.py + pytest.ini |
| Dependencias | Standard library | pytest + pytest-asyncio |
| Windows | ✅ Funciona | ✅ Funciona (con config) |
| Facilidad | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Reporte | Claro | Detallado |

## Guía de Ejecución

### Plan 01 (Completo)
```bash
# Tests simplificados - RECOMENDADO
python tests/test_plan_01_simple.py
```

### Plan 02 Paso 0 (Apis Críticas + Refactorización)
```bash
# Tests modular API - RECOMENDADO
python tests/test_plan_02_apis.py
```

### Ejecutar Todos los Tests
```bash
# Ejecutar Plan 01
python tests/test_plan_01_simple.py

# Ejecutar Plan 02
python tests/test_plan_02_apis.py
```

---

## Reporte Detallado

Ver detalles completos en:
- `tests/TEST_RESULTS_PLAN_02.md` - Resultados Plan 02 (29 tests)
- `tests/test_plan_01_simple.py` - Tests Plan 01 (10 tests)
- `tests/test_plan_02_apis.py` - Tests Plan 02 (29 tests)

---

## Status

| Plan | Tests | Status | Cobertura |
|------|-------|--------|-----------|
| Plan 01 | 10 | ✅ ALL PASSING | Módulos, Endpoints, BD |
| Plan 02 P0 | 29 | ✅ ALL PASSING | Schemas, Routes, Dependencies |

**Overall Status:** ✅ **39/39 TESTS PASSING**

---

**Última actualización:** 2026-04-09
**Framework:** unittest (sin pytest)
