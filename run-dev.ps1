Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "    INICIANDO SECURE RAG BFF GATEWAY     " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Levantar Backend en segundo plano
Write-Host "[BACKEND] Iniciando FastAPI en http://localhost:8000..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location E:\rag-secure-app\backend; .\venv\Scripts\uvicorn app.main:app --reload --port 8000"

# 2. Levantar Frontend en segundo plano/consola activa
Write-Host "[FRONTEND] Iniciando Vite en http://localhost:5173..." -ForegroundColor Green
Set-Location E:\rag-secure-app\frontend
npm run dev
