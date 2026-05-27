# Contrato de Integración WebSocket - API v1 (/v1/chat)

Este documento define el estándar de comunicación bidireccional mediante WebSockets entre el frontend (React) y el motor RAG (FastAPI) para el manejo de consultas en tiempo real.

---

## 1. Objetivo
Establecer un canal de baja latencia para que el usuario envíe consultas y el sistema retorne la respuesta progresiva generada por el flujo RAG, junto con las fuentes documentales utilizadas.

---

## 2. Ciclo de Vida de la Conexión

### 2.1. Establecimiento de la Conexión
* **Ruta de Conexión:** `ws://<host>:<port>/api/v1/chats/ws`
* **Ruta Real en Backend:** `/chats/ws` (Reescrita por el proxy de Vite en desarrollo).

### 2.2. Protocolo de Comunicación
Toda la información intercambiada a través de este canal debe viajar en formato **JSON**.

---

## 3. Especificación del Contrato de Datos

### 3.1. Input (Client-to-Server / Frontend -> Backend)
Estructura JSON del mensaje enviado por el cliente:

```json
{
  "session_id": "string (UUID v4 de la sesión actual)",
  "user_id": "string (UUID v4 o identificador único del usuario)",
  "query": "string (consulta textual del usuario)"
}
```

#### Atributos de Entrada:
* **`session_id`**: Identificador de la sesión para mantener la trazabilidad y la memoria conversacional en el grafo.
* **`user_id`**: Identificador único del usuario.
* **`query`**: Pregunta o instrucción textual.

---

### 3.2. Output (Server-to-Client / RAG -> Frontend)
Estructura JSON de la respuesta asíncrona enviada por el servidor:

```json
{
  "message_id": "string (UUID v4 asignado a la respuesta)",
  "user_query": "string (eco de la consulta original enviada)",
  "ai_response": "string (respuesta generada en Markdown)",
  "status": "string ('processing' | 'completed' | 'error')",
  "error_detail": "string | null (detalle del fallo, si aplica)",
  "sources": [
    {
      "titulo_seccion": "string (título o sección de procedencia)",
      "numero_pagina": "integer (página exacta del manual)",
      "snippet": "string (fragmento de texto citado)"
    }
  ]
}
```

#### Atributos de Salida:
* **`message_id`**: Identificador único generado por el backend para el par pregunta-respuesta.
* **`user_query`**: Copia exacta de la consulta original.
* **`ai_response`**: Respuesta procesada por el LLM, formateada en **Markdown**.
* **`status`**: Estado actual del ciclo de vida del mensaje (Streaming):
  * `processing`: El modelo está generando texto. El frontend recibirá actualizaciones continuas con nuevos tokens en `ai_response`.
  * `completed`: El streaming ha finalizado. El payload contiene la respuesta definitiva y el arreglo de `sources` poblado.
  * `error`: Ocurrió un fallo en la orquestación o en la conexión con el LLM/VectorDB.
* **`error_detail`**: Contiene la descripción técnica o el mensaje de interfaz si el `status` es `'error'`. En flujos exitosos, se envía como `null`.
* **`sources`**: Referencias documentales recuperadas. (Generalmente se envían vacías durante el `processing` y se pueblan al emitir el evento `completed`).

---

## 4. Notas y Requisitos de Implementación para Frontend

> [!IMPORTANT]
> **Flujo de Streaming y Renderizado Markdown:**
> Al recibir eventos continuos con estatus `processing`, la interfaz debe actualizar iterativamente el contenido de `ai_response` para lograr el efecto de escritura en tiempo real. Dado que el texto se emite en formato Markdown, es imperativo utilizar librerías como `react-markdown` para garantizar un renderizado seguro y semántico que prevenga inyecciones HTML.

> [!TIP]
> **Maquetación del Panel Lateral (Sources) y Manejo de Errores:**
> * **Fuentes:** Al detectarse el evento `completed`, se debe habilitar un panel lateral dedicado iterando sobre el arreglo `sources`. Se requiere renderizar tarjetas (*cards*) dinámicas que muestren el `titulo_seccion`, un indicador para el `numero_pagina` y un bloque colapsable para previsualizar el `snippet`.
> * **Alertas:** Si se recibe un evento `error`, la interfaz debe detener los indicadores de carga (spinners/esqueletos) y desplegar una notificación al usuario consumiendo el string provisto en `error_detail`.