import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.models.database import init_db
from app.api import auth, chats

# Inicializar Base de Datos SQLite
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configurar CORS para permitir credenciales y cookies del Frontend de desarrollo
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar enrutadores de API
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(chats.router, prefix=settings.API_V1_STR)

# Montar archivos estáticos del frontend
frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"message": "Secure RAG BFF Gateway is online (Frontend not compiled).", "docs": "/docs"}

