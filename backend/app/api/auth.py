import time
from datetime import datetime, timedelta
from typing import Optional, List
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from sqlalchemy.orm import Session
import uuid

from app.models.database import get_db, User, WSTicket
from app.schemas.schemas import UserCreate, UserResponse, WSTicketResponse, UserPasswordReset, UserRoleUpdate
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiting en memoria para autenticación
LOGIN_ATTEMPTS = defaultdict(list)
RATE_LIMIT_LIMIT = 5  # máximo 5 intentos
RATE_LIMIT_WINDOW = 60  # ventana de 60 segundos

def rate_limiter(request: Request):
    client_ip = request.client.host
    now = time.time()
    
    # Filtrar timestamps que estén dentro de la ventana de 60 segundos
    timestamps = [t for t in LOGIN_ATTEMPTS[client_ip] if now - t < RATE_LIMIT_WINDOW]
    LOGIN_ATTEMPTS[client_ip] = timestamps
    
    if len(timestamps) >= RATE_LIMIT_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de inicio de sesión. Por favor, inténtalo de nuevo en un minuto."
        )
    
    # Registrar intento actual
    LOGIN_ATTEMPTS[client_ip].append(now)

def get_current_user(
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado o sesión expirada",
    )
    if not access_token:
        raise credentials_exception
    
    user_id = decode_access_token(access_token)
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="El correo ya está registrado"
        )
    hashed_password = get_password_hash(user_in.password)
    
    # Si es el primer usuario en registrarse en la base de datos, hacerlo super admin y activarlo
    is_first = db.query(User).count() == 0
    
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True if is_first else False,
        is_admin=True if is_first else False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(
    user_in: UserCreate,
    response: Response,
    db: Session = Depends(get_db),
    _ = Depends(rate_limiter)
):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu cuenta está pendiente de aprobación por el Administrador. Contacta a un administrador para ingresar."
        )
    
    access_token = create_access_token(subject=user.id)
    
    is_secure = settings.ENV == "production"
    
    # Configurar el token en una cookie HttpOnly
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",  # Permite cookies en redirecciones estándar pero protege contra CSRF
        secure=is_secure, # Activo condicionalmente en producción (HTTPS)
    )
    return {"message": "Login exitoso", "user_id": user.id, "email": user.email, "is_active": user.is_active, "is_admin": user.is_admin}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/ws-ticket", response_model=WSTicketResponse)
def generate_ws_ticket(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Genera un ticket de un solo uso que expira en 30 segundos
    expires_at = datetime.utcnow() + timedelta(seconds=30)
    ticket = WSTicket(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        expires_at=expires_at
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return {"ticket_id": ticket.id, "expires_at": ticket.expires_at}


@router.get("/admin/users", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos de Administrador")
    
    return db.query(User).order_by(User.email.asc()).all()


@router.post("/admin/users/{user_id}/approve")
def approve_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos de Administrador")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user.is_active = True
    db.commit()
    return {"message": "Usuario aprobado con éxito"}


@router.post("/admin/users/{user_id}/reject")
def reject_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos de Administrador")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user.is_active = False
    db.commit()
    return {"message": "Usuario rechazado/desactivado con éxito"}


@router.post("/admin/users/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    password_data: UserPasswordReset,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos de Administrador")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    return {"message": "Contraseña restablecida con éxito"}


@router.post("/admin/users/{user_id}/role")
def update_user_role(
    user_id: str,
    role_data: UserRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="No tienes permisos de Administrador")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Prevenir que el admin se cambie el rol a sí mismo
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol")
    
    user.is_admin = role_data.is_admin
    db.commit()
    return {"message": "Rol de usuario actualizado con éxito"}

