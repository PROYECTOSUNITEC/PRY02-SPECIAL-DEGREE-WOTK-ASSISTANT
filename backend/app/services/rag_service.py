import asyncio
from typing import AsyncGenerator, Dict, Any, List

class RAGEngineService:
    def __init__(self):
        # Mock responses
        self.mock_responses = {
            "teg": {
                "text": "Para presentar el Trabajo Especial de Grado (TEG), el estudiante debe cumplir con los siguientes requisitos obligatorios:\n\n1. **Aprobación Académica**: Haber aprobado el 100% de las asignaturas del plan de estudio.\n2. **Solvencia Administrativa**: Estar al día con los pagos y obligaciones financieras en la institución.\n3. **Tutor Académico**: Contar con la carta de aceptación firmada por un tutor avalado.\n4. **Servicio Comunitario**: Presentar constancia de culminación de dicho servicio.\n\n*Nota: El borrador debe ser consignado ante el Comité Técnico con un mínimo de 15 días hábiles de anticipación a la fecha de defensa.*",
                "sources": [
                    {
                        "titulo_seccion": "Manual del Estudiante - Sección 4.2 (Requisitos de Egresados)",
                        "numero_pagina": 18,
                        "snippet": "El estudiante que opte a la presentación del Trabajo Especial de Grado (TEG) deberá demostrar solvencia académica total (100% de créditos aprobados) y solvencia administrativa vigente."
                    },
                    {
                        "titulo_seccion": "Reglamento del Trabajo Especial de Grado - Artículo 12",
                        "numero_pagina": 5,
                        "snippet": "Es requisito indispensable para la inscripción formal del TEG la postulación y aceptación firmada de un tutor académico calificado."
                    }
                ]
            },
            "default": {
                "text": "He procesado tu consulta dentro del sistema de documentación interna. Lamentablemente, no encontré detalles explícitos sobre ese tema en particular.\n\nSin embargo, te sugiero revisar las secciones generales del **Manual de Convivencia** o ponerte en contacto con la **Coordinación Académica** para obtener información actualizada sobre tu caso.",
                "sources": [
                    {
                        "titulo_seccion": "Manual de Convivencia - Glosario",
                        "numero_pagina": 45,
                        "snippet": "Para cualquier trámite no contemplado en el presente manual, el estudiante deberá acudir a la Coordinación respectiva de su Escuela."
                    }
                ]
            }
        }

    async def stream_response(self, query: str, chat_history: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Simula la interacción con un LLM real devolviendo un stream asíncrono de tokens.
        `chat_history` recibe una lista de mensajes en formato:
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        query_lower = query.lower()
        
        # En una integración real, se le pasa `chat_history` y `query` a LangChain u OpenAI.
        # Imprimir history para verificar por terminal
        print(f"[RAGEngine] Chat history injectado: {len(chat_history)} mensajes previos.")
        
        # Por ahora determinamos la respuesta mock:
        response_data = self.mock_responses["teg"] if "teg" in query_lower or "trabajo" in query_lower or "grado" in query_lower else self.mock_responses["default"]
        
        full_text = response_data["text"]
        
        # Simulamos fragmentos de texto (chunks) en lugar de palabras enteras
        chunk_size = 5
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i:i+chunk_size]
            
            yield {
                "type": "content_chunk",
                "chunk": chunk
            }
            # Latencia de procesamiento de LLM realista
            await asyncio.sleep(0.02)
            
        # Emitimos el evento final con las fuentes y el texto completo
        yield {
            "type": "final_result",
            "full_text": full_text,
            "sources": response_data["sources"]
        }
