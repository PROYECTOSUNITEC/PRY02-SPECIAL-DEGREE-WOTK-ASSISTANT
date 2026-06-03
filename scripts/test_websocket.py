import asyncio
import json
import sys
from pathlib import Path

try:
    import websockets
except ImportError:
    print("❌ Instala la dependencia: pip install websockets")
    sys.exit(1)

WS_URL = "ws://127.0.0.1:8000/chats/ws"

MOCK_REQUEST = {
    "session_id": "a3b9c8d7-e6f5-4a3b-2c1d-0e9f8a7b6c5d",
    "user_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
    "query": "Cómo puedo enfocar mi trabajo especial de grado cuantitativo?",
}


async def test_chat():
    print(f"🔌 Conectando a {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Conexión establecida\n")

            # enviar consulta
            payload = json.dumps(MOCK_REQUEST, ensure_ascii=False)
            print(f"📤 Enviando:\n{json.dumps(MOCK_REQUEST, indent=2, ensure_ascii=False)}\n")
            await ws.send(payload)

            # recibir respuestas
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=120)
                data = json.loads(raw)
                status = data.get("status", "unknown")

                print(f"{'─' * 60}")
                print(f"📥 Status: {status}")

                if status == "processing":
                    print("⏳ El backend está procesando la consulta...")

                elif status == "completed":
                    print(f"🆔 Message ID: {data['message_id']}")
                    print(f"\n📝 Respuesta:\n{data['ai_response']}")
                    print(f"\n📚 Fuentes ({len(data['sources'])}):")
                    for i, src in enumerate(data["sources"], 1):
                        print(f"   {i}. {src['titulo_seccion']} (p. {src['numero_pagina']})")
                        print(f"      └─ {src['snippet'][:120]}...")
                    break

                elif status == "error":
                    print(f"❌ Error: {data.get('error_detail', 'Sin detalle')}")
                    break

            print(f"\n{'─' * 60}")
            print("✅ Test finalizado.")

    except ConnectionRefusedError:
        print("❌ No se pudo conectar. ¿Está corriendo el backend?")
    except asyncio.TimeoutError:
        print("❌ Timeout.")


if __name__ == "__main__":
    asyncio.run(test_chat())
