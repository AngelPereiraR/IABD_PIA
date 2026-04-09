# Planes de Implementación — OptiCV Engine

Planificaciones detalladas por módulo. Ejecutar en orden.

## Orden de implementación

| # | Plan | Descripción | Dependencias |
|---|------|-------------|--------------|
| 00 | [Infraestructura Base](./00_infraestructura.md) | HF Spaces, Dockerfile, Neon BD, Cloudinary | — |
| 01 | [Módulo de Vigilancia](./01_modulo_vigilancia.md) | Gmail → LangChain/DeepSeek → Neon + Telegram botón | 00 |
| 02 | [Engine IA](./02_engine_ia.md) | Análisis JD + adaptación CV con DeepSeek | 00, 01 |
| 03 | [Compilador LaTeX](./03_latex_compiler.md) | pdflatex async → PDF → Cloudinary | 00, 02 |
| 04 | [API FastAPI](./04_api_fastapi.md) | Endpoints REST para dashboard y generación | 00, 02, 03 |
| 05 | [Dashboard Frontend](./05_dashboard_frontend.md) | React + Vite → Vercel | 04 |

## Checklist global

- [ ] **00** — Docker build OK + BD conectada + Cloudinary OK
- [ ] **01** — Brain con DeepSeek OK + oferta guardada en BD + botón Telegram funcional
- [ ] **02** — Engine genera `.tex` adaptado sin errores
- [ ] **03** — `pdflatex` compila PDF correctamente + sube a Cloudinary
- [ ] **04** — Todos los endpoints responden (verificar en `/docs`)
- [ ] **05** — Dashboard muestra ofertas + botón Generar CV funciona end-to-end

## Flujo completo (verificación final)

```
1. Email con oferta → mail_agent detecta
2. brain.py (DeepSeek) → score + análisis
3. Oferta guardada en Neon (status: pending)
4. Telegram: notificación + botón "Generar CV"
5. Usuario pulsa botón → POST /api/generate/{id}
6. engine.py: DeepSeek adapta CV → .tex generado
7. latex_compiler.py: pdflatex → PDF
8. PDF subido a Cloudinary → URL guardada en Neon (status: done)
9. Telegram: enlace al PDF enviado al usuario
10. Dashboard: oferta aparece con botón de descarga
```
