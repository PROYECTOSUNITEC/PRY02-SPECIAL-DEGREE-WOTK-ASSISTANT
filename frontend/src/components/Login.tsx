import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import { ParticleSphere } from './ParticleSphere';

// Logotipo de la Universidad Tecnológica del Centro (UNITEC) en formato SVG Premium
export const UnimetLogo: React.FC<{ size?: number }> = ({ size = 24 }) => {
  return (
    <svg viewBox="0 0 100 120" width={size} height={size * 1.2} style={{ display: 'block' }}>
      {/* Fondo blanco del escudo */}
      <path d="M10,10 L90,10 L90,60 C90,85 50,110 50,110 C50,110 10,85 10,60 Z" fill="#ffffff" />
      
      {/* Escudo Exterior (Borde doble en color gris oscuro/negro) */}
      <path d="M10,10 L90,10 L90,60 C90,85 50,110 50,110 C50,110 10,85 10,60 Z" fill="none" stroke="#1e293b" strokeWidth="4" />
      <path d="M14,14 L86,14 L86,60 C86,81 50,103 50,103 C50,103 14,81 14,60 Z" fill="none" stroke="#475569" strokeWidth="1.5" />
      
      {/* División horizontal */}
      <line x1="10" y1="62" x2="90" y2="62" stroke="#1e293b" strokeWidth="3" />
      
      {/* Bandera / Libro (Superior) */}
      {/* Mitad Izquierda (Azul UNITEC) */}
      <path d="M22,22 Q36,17 50,22 L50,52 Q36,47 22,52 Z" fill="#00479e" />
      {/* Mitad Derecha (Gris UNITEC) */}
      <path d="M50,22 Q64,27 78,22 L78,52 Q64,57 50,52 Z" fill="#bbc7c6" />
      
      {/* Engranaje (Inferior) en negro */}
      <circle cx="50" cy="85" r="11" fill="none" stroke="#1a1a1a" strokeWidth="4.5" />
      <path d="M50,71 L50,75 M50,95 L50,99 M36,85 L40,85 M60,85 L64,85 M40,75 L43,78 M57,92 L60,95 M40,95 L43,92 M57,75 L60,78" stroke="#1a1a1a" strokeWidth="3.5" strokeLinecap="round" />
    </svg>
  );
};

export const Login: React.FC = () => {
  const { login, register, error, clearError } = useAuth();
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    
    setLoading(true);
    if (isRegister) {
      await register(email, password);
    } else {
      await login(email, password);
    }
    setLoading(false);
  };

  const toggleMode = () => {
    setIsRegister(!isRegister);
    clearError();
    setEmail('');
    setPassword('');
  };

  return (
    <div className="login-container-grid">
      {/* Columna Izquierda: Formulario de Login/Registro */}
      <div className="login-form-pane">
        <div style={{ position: 'absolute', top: '32px', left: '40px', display: 'flex', alignItems: 'center' }}>
          <img src="/logo_universidad.png" alt="UNITEC Logo" style={{ height: '36px', objectFit: 'contain' }} />
        </div>

        <div className="auth-card-auros">
          <div className="auth-header-auros">
            <div className="section-eyebrow" style={{ marginBottom: '12px' }}>
              {isRegister ? 'REGISTRO DE CREDENCIAL' : 'VERIFICACIÓN DE ACCESO'}
            </div>
            <h1 className="auth-logo-auros">
              {isRegister ? 'Crear Cuenta' : 'Ingresar al Portal'}
            </h1>
            <p className="auth-subtitle-auros">
              {isRegister 
                ? 'Establece tu firma de acceso encriptada para el observatorio.' 
                : 'Acceso seguro al sistema de procesamiento RAG interno.'}
            </p>
          </div>

          {error && <div className="error-message-auros">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group-auros">
              <label className="form-label-auros" htmlFor="email">Correo Institucional</label>
              <div style={{ position: 'relative' }}>
                <Mail 
                  size={16} 
                  style={{ 
                    position: 'absolute', 
                    left: '14px', 
                    top: '50%', 
                    transform: 'translateY(-50%)', 
                    color: 'var(--color-fog-veil)',
                    opacity: 0.5 
                  }} 
                />
                <input
                  id="email"
                  type="email"
                  className="form-input-auros"
                  style={{ paddingLeft: '42px' }}
                  placeholder="usuario@unitec.edu.ve"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group-auros">
              <label className="form-label-auros" htmlFor="password">Contraseña</label>
              <div style={{ position: 'relative' }}>
                <Lock 
                  size={16} 
                  style={{ 
                    position: 'absolute', 
                    left: '14px', 
                    top: '50%', 
                    transform: 'translateY(-50%)', 
                    color: 'var(--color-fog-veil)',
                    opacity: 0.5 
                  }} 
                />
                <input
                  id="password"
                  type="password"
                  className="form-input-auros"
                  style={{ paddingLeft: '42px' }}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn-primary-gradient" style={{ width: '100%', marginTop: '8px' }} disabled={loading}>
              {loading ? (
                <div className="spinner-auros"></div>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {isRegister ? 'Registrar y Entrar' : 'Verificar y Entrar'}
                  <ArrowRight size={14} />
                </span>
              )}
            </button>
          </form>

          <div className="auth-switch-auros">
            {isRegister ? '¿Ya tienes una cuenta?' : '¿No tienes acceso registrado?'}
            <span className="auth-switch-link-auros" onClick={toggleMode}>
              {isRegister ? 'Inicia Sesión' : 'Regístrate aquí'}
            </span>
          </div>
        </div>

        <div style={{ position: 'absolute', bottom: '32px', left: '40px', fontSize: '10px', color: 'var(--color-fog-veil)', opacity: 0.4, letterSpacing: '1px' }}>
          CANAL BFF ENCRIPTADO / CONEXIÓN SEGURA
        </div>
      </div>

      {/* Columna Derecha: Hero Brand Panel con la Esfera de Partículas */}
      <div className="login-hero-pane">
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', zIndex: 5 }}>
          <div className="section-eyebrow">UNITEC PORTAL</div>
          <div style={{ fontSize: '10px', color: 'var(--color-fog-veil)', opacity: 0.5, letterSpacing: '1px' }}>SYSTEM: ONLINE</div>
        </div>

        <div style={{ position: 'relative', zIndex: 5, margin: 'auto 0' }}>
          <div className="section-eyebrow" style={{ marginBottom: '16px' }}>SECURE GATEWAY</div>
          <h1 style={{ 
            fontFamily: 'var(--font-matter)',
            fontSize: 'var(--text-display)', 
            letterSpacing: 'var(--tracking-display)', 
            lineHeight: 'var(--leading-display)',
            textTransform: 'uppercase',
            color: 'var(--color-snow-sheet)',
            marginBottom: '20px'
          }}>
            UNITEC
          </h1>
          <p style={{ 
            fontSize: 'var(--text-body-lg)', 
            lineHeight: 'var(--leading-body-lg)',
            color: 'var(--color-fog-veil)', 
            maxWidth: '460px' 
          }}>
            Portal institucional de procesamiento RAG y consultas de datos. Seguridad blindada por la pasarela de control de la UNITEC, WebSockets de alta velocidad y tokenización de un solo uso.
          </p>
        </div>

        <div style={{ zIndex: 5 }}>
          <span className="section-eyebrow">CONSTELACIÓN DE DATOS ACTIVA</span>
        </div>

        {/* Esfera de partículas 3D en el fondo */}
        <div className="particle-canvas-container">
          <ParticleSphere />
        </div>
      </div>
    </div>
  );
};
