"""Punto de entrada de la API FastAPI."""

from fastapi import FastAPI

app = FastAPI(title="Backend", version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    """Saludo de comprobación."""
    return {"message": "Hola mundo"}


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de vida para orquestadores."""
    return {"status": "ok"}
