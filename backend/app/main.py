import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# todo: descomentar cuando el modulo auth exista
# from modules.auth.router import router as auth_router
from modules.chats.routes.v1.chat import router as chats_router

app = FastAPI(title="Backend", version="0.1.0")

# app.include_router(auth_router)
app.include_router(chats_router)


@app.get("/", response_class=HTMLResponse)
def read_root() -> HTMLResponse:
    """Retorna la vista de chat HTML."""
    template_path = Path(__file__).resolve().parent / "templates" / "chat.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    return HTMLResponse(content="<h1>Vista del chat no encontrada</h1>", status_code=404)


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de vida para orquestadores."""
    return {"status": "ok"}

