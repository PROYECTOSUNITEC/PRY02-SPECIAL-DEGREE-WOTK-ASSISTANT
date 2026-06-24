# Secure RAG BFF Gateway (PRY02-SPECIAL-DEGREE-WORK-ASSISTANT)

Este repositorio contiene el sistema de Asistencia para Trabajos Especiales de Grado (TEG), implementando una arquitectura RAG (Retrieval-Augmented Generation) segura mediante WebSockets.

## 📌 Información del Proyecto

El sistema está diseñado bajo el patrón **BFF (Backend for Frontend)**:
- **Frontend:** Aplicación SPA (Single Page Application) construida con React + Vite + TypeScript.
- **Backend:** API asíncrona construida con FastAPI (Python).
- **Comunicación:** Integración bidireccional de baja latencia mediante WebSockets, autenticada a través de tickets de un solo uso (WSTickets) para prevenir brechas de seguridad y exposición de tokens.

---

## 🚀 Guía de Despliegue Local (Desarrollo)

### Requisitos Previos
1. **Node.js** (v18 o superior)
2. **Python** (v3.10 o superior)
3. **PowerShell** (para ejecutar los scripts nativos en Windows)

### Pasos para iniciar el entorno
El proyecto incluye un script de automatización (`run-dev.ps1`) en la raíz que se encarga de levantar ambos servicios en paralelo.

1. Clona el repositorio:
   ```bash
   git clone https://github.com/PROYECTOSUNITEC/PRY02-SPECIAL-DEGREE-WOTK-ASSISTANT.git
   cd PRY02-SPECIAL-DEGREE-WOTK-ASSISTANT
   ```
2. Ejecuta el script de inicio en PowerShell:
   ```powershell
   .\run-dev.ps1
   ```
3. El sistema estará disponible en:
   - **Frontend UI:** [http://localhost:5173](http://localhost:5173)
   - **Backend API (Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)

*Nota: La contraseña predeterminada para pruebas administrativas suele ser `admin123` en el usuario administrador de la base de datos SQLite preconfigurada.*

---

## 📊 Estatus Actual del Proyecto

El cascarón arquitectónico está listo y operativo, pero el motor de inteligencia artificial está operando en un simulador (Mock).

**✅ Lo que ya está completado:**
- [x] Configuración de React (Vite) y FastAPI.
- [x] Base de datos local (SQLite) configurada con modelos de usuarios, sesiones y mensajes.
- [x] Sistema de Autenticación con JWT.
- [x] Protocolo de comunicación WebSocket implementado con seguridad robusta (WSTickets).
- [x] **Refactorización de la Capa de Servicio RAG:** La conexión WebSocket fue extraída a un servicio asíncrono (`rag_service.py`), permitiendo la transmisión asíncrona de tokens (Streaming) y la inyección del historial de mensajes para que la IA posea contexto cronológico.

**⚠️ Lo que falta (Trabajo Pendiente):**
- [ ] **Integración del Modelo de Lenguaje (LLM):** Reemplazar el diccionario estático (`mock_responses`) en `rag_service.py` por una conexión real a OpenAI, Anthropic o Llama.
- [ ] **Motor Vectorial (Embeddings):** Configurar LangChain / LlamaIndex junto con una base de datos vectorial (Qdrant, Pinecone o Chroma) para hacer las búsquedas en los manuales de grado.
- [ ] **Limpieza de Documentos:** Ingesta de los reglamentos del TEG y creación del pipeline de "Chunking".
- [ ] **Preparación para Producción:** Migrar la base de datos de SQLite a PostgreSQL y crear los Dockerfiles / pipelines CI/CD para subir la aplicación a un servidor en la nube.
