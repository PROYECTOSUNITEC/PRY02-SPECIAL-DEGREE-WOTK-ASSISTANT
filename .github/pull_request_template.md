## Descripción

<!-- Explica qué problema resuelve o qué funcionalidad añade. Enlaza issues si aplica (ej. Closes #12). -->

## Tipo de cambio

<!-- Marca con una x lo que corresponda: [x] -->

- [ ] Corrección de errores (cambio que no rompe compatibilidad hacia atrás)
- [ ] Nueva funcionalidad (cambio que no rompe compatibilidad hacia atrás)
- [ ] Cambio que rompe compatibilidad (fix o feature que requiere ajustes en consumidores)
- [ ] Refactor / mantenimiento / documentación
- [ ] Otro: <!-- describe brevemente -->

## Ámbito del repositorio

<!-- Marca las áreas tocadas -->

- [ ] `backend/` (FastAPI, WebSockets, servicios)
- [ ] `backend/app/ai/` (LangChain / LangGraph, prompts, tools)
- [ ] `core_ml/` (entrenamiento, inferencia, preprocesamiento)
- [ ] `data/` (datasets, documentación de datos; respeta políticas de tamaño y `.gitignore`)
- [ ] `frontend/` (cuando exista en el monorepo)
- [ ] `docker/` o `docker-compose.yml`
- [ ] Configuración / CI / documentación raíz
- [ ] Otro: <!-- ruta o módulo -->

## Comportamiento y pruebas

<!-- Cómo validaste el cambio -->

- [ ] Ejecuté tests relevantes (`pytest` en `backend/` cuando existan)
- [ ] Probé manualmente el flujo afectado (API, WebSocket, Compose, etc.)
- [ ] No aplica / pendiente de entorno: <!-- explica -->

## Checklist de calidad y seguridad

- [ ] No incluyo secretos, `.env` reales ni credenciales (solo variables documentadas en `.env.example` si aplica)
- [ ] No subo datasets pesados, modelos ni artefactos grandes no acordados (ver `ARQUITECTURE.md` y `data/`)
- [ ] Los endpoints / handlers WebSocket permanecen delgados y delegan en servicios o capa `ai/` cuando corresponde
- [ ] Código alineado con convenciones del proyecto (PEP 8, tipado y estilo existente en el módulo)

## Notas para revisores

<!-- Contexto adicional: decisiones de diseño, riesgos conocidos, follow-ups -->
