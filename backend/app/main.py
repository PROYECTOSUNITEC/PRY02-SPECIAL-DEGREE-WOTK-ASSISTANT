"""Punto de entrada de la API FastAPI."""

from fastapi import FastAPI

from modules.auth.router import router as auth_router
from modules.chats.routes.v1.chat import router as chats_router

app = FastAPI(title="Backend", version="0.1.0")

app.include_router(auth_router)
app.include_router(chats_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Saludo de comprobación."""
    return {"message": "Hola mundo"}


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de vida para orquestadores."""
    return {"status": "ok"}
