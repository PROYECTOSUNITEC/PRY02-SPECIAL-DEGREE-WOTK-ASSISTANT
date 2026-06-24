import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { SourcesPanel } from './SourcesPanel';
import ReactMarkdown from 'react-markdown';
import { 
  Send, Plus, MessageSquare, Terminal, User, AlertTriangle, ShieldCheck, HelpCircle
} from 'lucide-react';
import { ParticleSphere } from './ParticleSphere';

interface Source {
  titulo_seccion: string;
  numero_pagina: number;
  snippet: string;
}

interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Source[];
}

interface Session {
  id: string;
  user_id: string;
  created_at: string;
}

export const Chat: React.FC = () => {
  const { user, logout, getWSTicket } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState<string>('');
  
  // Estados para streaming y UI
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [activeSources, setActiveSources] = useState<Source[]>([]);
  const [showSourcesPanel, setShowSourcesPanel] = useState<boolean>(false);
  const [wsError, setWsError] = useState<string | null>(null);

  // Estados para panel de Administración (Super Admin)
  const [showAdminPanel, setShowAdminPanel] = useState<boolean>(false);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [loadingAdminUsers, setLoadingAdminUsers] = useState<boolean>(false);
  const [passwordInputs, setPasswordInputs] = useState<{[userId: string]: string}>({});
  const [adminFeedback, setAdminFeedback] = useState<{[userId: string]: {text: string, isError: boolean} | null}>({});

  const fetchAdminUsers = async () => {
    setLoadingAdminUsers(true);
    try {
      const res = await fetch('/api/v1/auth/admin/users', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setAdminUsers(data);
      }
    } catch (err) {
      console.error("Error al obtener usuarios para admin:", err);
    } finally {
      setLoadingAdminUsers(false);
    }
  };

  const handleResetPassword = async (userId: string) => {
    const newPassword = passwordInputs[userId];
    if (!newPassword || newPassword.trim().length < 6) {
      setAdminFeedback(prev => ({
        ...prev,
        [userId]: { text: "La contraseña debe tener al menos 6 caracteres", isError: true }
      }));
      return;
    }

    try {
      const res = await fetch(`/api/v1/auth/admin/users/${userId}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: newPassword.trim() }),
        credentials: 'include'
      });
      if (res.ok) {
        setAdminFeedback(prev => ({
          ...prev,
          [userId]: { text: "¡Contraseña cambiada con éxito!", isError: false }
        }));
        setPasswordInputs(prev => ({ ...prev, [userId]: '' }));
      } else {
        const errData = await res.json();
        setAdminFeedback(prev => ({
          ...prev,
          [userId]: { text: errData.detail || "Error al cambiar contraseña", isError: true }
        }));
      }
    } catch (err) {
      setAdminFeedback(prev => ({
        ...prev,
        [userId]: { text: "Error de red", isError: true }
      }));
    }
  };

  const handleToggleRole = async (userId: string, currentIsAdmin: boolean) => {
    try {
      const res = await fetch(`/api/v1/auth/admin/users/${userId}/role`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_admin: !currentIsAdmin }),
        credentials: 'include'
      });
      if (res.ok) {
        fetchAdminUsers();
      } else {
        const errData = await res.json();
        alert(errData.detail || "Error al actualizar rol");
      }
    } catch (err) {
      console.error("Error al actualizar rol:", err);
    }
  };


  useEffect(() => {
    if (showAdminPanel && user?.is_admin) {
      fetchAdminUsers();
    }
  }, [showAdminPanel]);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll al recibir mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage, isProcessing]);

  // Cargar sesiones al inicio
  useEffect(() => {
    fetchSessions();
  }, []);

  // Cargar mensajes cuando cambia la sesión activa
  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
      connectWebSocket(activeSessionId);
    } else {
      setMessages([]);
      closeWebSocket();
    }
    return () => {
      closeWebSocket();
    };
  }, [activeSessionId]);

  const fetchSessions = async () => {
    try {
      const res = await fetch('/api/v1/chats/sessions', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0 && !activeSessionId) {
          setActiveSessionId(data[0].id);
        }
      }
    } catch (err) {
      console.error("Error al obtener sesiones:", err);
    }
  };

  const fetchMessages = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/v1/chats/sessions/${sessionId}/messages`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
        // Si el último mensaje tiene fuentes, mostrarlas
        const lastMsg = data[data.length - 1];
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.sources && lastMsg.sources.length > 0) {
          setActiveSources(lastMsg.sources);
          setShowSourcesPanel(true);
        } else {
          setActiveSources([]);
          setShowSourcesPanel(false);
        }
      }
    } catch (err) {
      console.error("Error al obtener historial de mensajes:", err);
    }
  };

  const createNewSession = async () => {
    try {
      const res = await fetch('/api/v1/chats/sessions', {
        method: 'POST',
        credentials: 'include'
      });
      if (res.ok) {
        const newSession = await res.json();
        setSessions([newSession, ...sessions]);
        setActiveSessionId(newSession.id);
      }
    } catch (err) {
      console.error("Error al crear sesión:", err);
    }
  };

  // Conexión segura al WebSocket BFF usando ticket
  const connectWebSocket = async (sessionId: string) => {
    closeWebSocket();
    setWsError(null);

    const ticket = await getWSTicket();
    if (!ticket) {
      setWsError("No se pudo obtener el ticket de autorización de WebSocket.");
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/chats/ws?ticket=${ticket}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.status === 'processing') {
        setIsProcessing(true);
        setStreamingMessage(data.ai_response);
      } 
      else if (data.status === 'completed') {
        setIsProcessing(false);
        setStreamingMessage('');
        
        // Agregar la respuesta final completada a la lista de mensajes
        const newAssistantMessage: Message = {
          id: data.message_id,
          session_id: sessionId,
          role: 'assistant',
          content: data.ai_response,
          timestamp: new Date().toISOString(),
          sources: data.sources
        };

        setMessages(prev => [...prev, newAssistantMessage]);
        
        if (data.sources && data.sources.length > 0) {
          setActiveSources(data.sources);
          setShowSourcesPanel(true);
        } else {
          setActiveSources([]);
          setShowSourcesPanel(false);
        }
      } 
      else if (data.status === 'error') {
        setIsProcessing(false);
        setStreamingMessage('');
        setWsError(data.error_detail || "Error en el flujo RAG de comunicación.");
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      setWsError("Error de comunicación de WebSocket seguro.");
      setIsProcessing(false);
    };

    ws.onclose = (event) => {
      if (event.code === 4001 || event.code === 3008) {
        setWsError("Tu ticket de sesión expiró o no tienes autorización para acceder a este canal.");
      }
    };
  };

  const closeWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !activeSessionId || !user) return;

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      // Intentar reconectar antes de enviar
      connectWebSocket(activeSessionId).then(() => {
        sendPayload();
      });
    } else {
      sendPayload();
    }
  };

  const sendPayload = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setWsError("Canal cerrado. Intenta recargar la sesión.");
      return;
    }

    const payload = {
      session_id: activeSessionId,
      user_id: user?.id,
      query: query.trim()
    };

    // Agregar mensaje local del usuario inmediatamente
    const newUserMessage: Message = {
      id: Math.random().toString(),
      session_id: activeSessionId!,
      role: 'user',
      content: query.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setIsProcessing(true);
    setWsError(null);
    
    wsRef.current.send(JSON.stringify(payload));
    setQuery('');
  };

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      {/* Top Navigation Bar - Luvalcapa style */}
      <header className="top-nav">
        <div className="top-nav-logo">
          <img src="/logo_universidad.png" alt="UNITEC Logo" style={{ height: '36px', objectFit: 'contain' }} />
        </div>
        
        <nav className="top-nav-menu">
          {user?.is_admin && (
            <a 
              href="#" 
              className="top-nav-link" 
              onClick={(e) => { e.preventDefault(); setShowAdminPanel(!showAdminPanel); }}
              style={{ color: showAdminPanel ? 'var(--color-ice-mist)' : 'var(--color-fog-veil)', fontWeight: 500 }}
            >
              [Administración]
            </a>
          )}
          <a 
            href="#" 
            className="top-nav-link" 
            onClick={(e) => { e.preventDefault(); setShowAdminPanel(false); }}
            style={{ color: !showAdminPanel ? 'var(--color-ice-mist)' : 'var(--color-fog-veil)' }}
          >
            Portal RAG
          </a>
          <a href="#" className="top-nav-link" onClick={(e) => e.preventDefault()}>Conexiones BFF</a>
        </nav>

        <div>
          <button className="btn-ghost-rounded" onClick={logout} style={{ padding: '8px 16px', fontSize: '10px' }}>
            CERRAR SESIÓN
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="chat-layout-auros">
        {/* Sidebar de Sesiones */}
        <aside className="sidebar-auros">
          <div className="sidebar-header-auros">
            <span className="section-eyebrow">Consultas Activas</span>
          </div>

          <div className="session-list-auros">
            <button className="btn-new-chat-auros" onClick={createNewSession}>
              <Plus size={14} />
              Nueva Consulta
            </button>

            {sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item-auros ${activeSessionId === session.id ? 'active' : ''}`}
                onClick={() => {
                  if (!isProcessing) {
                    setActiveSessionId(session.id);
                  }
                }}
              >
                <MessageSquare size={14} style={{ opacity: 0.7 }} />
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  Sesión {session.id.substring(0, 8).toUpperCase()}
                </div>
              </div>
            ))}
          </div>

          <div className="sidebar-footer-auros">
            <div className="user-info-auros">
              <div className="user-email-auros">{user?.email}</div>
              <div className="user-status-auros">
                <ShieldCheck size={12} />
                BFF ENCRIPTADO
              </div>
            </div>
          </div>
        </aside>

        {/* Área Central de Mensajes */}
        <main className="chat-main-auros">
          <div className="chat-header-auros">
            <div className="chat-header-title-auros">
              {showAdminPanel 
                ? 'SISTEMA CONTROL DE ACCESO // SUPER ADMIN' 
                : activeSessionId 
                  ? `SESIÓN DE CONSULTA RAG // ID: ${activeSessionId.substring(0, 8).toUpperCase()}` 
                  : 'SIN SESIÓN SELECCIONADA'}
            </div>
            {!showAdminPanel && activeSessionId && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="section-eyebrow" style={{ fontSize: '9px' }}>CANAL ACTIVO</span>
              </div>
            )}
          </div>

          {wsError && !showAdminPanel && (
            <div className="error-message-auros" style={{ margin: '20px var(--spacing-32)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertTriangle size={16} />
              <span>{wsError}</span>
            </div>
          )}

          {showAdminPanel ? (
            /* Vista del Panel de Administración para el Super Admin */
            <div className="messages-container-auros" style={{ zIndex: 5 }}>
              <div className="empty-state-auros" style={{ padding: '0 0 var(--spacing-32) 0', alignItems: 'flex-start', textAlign: 'left', margin: '0' }}>
                <div className="hero-eyebrow-container">
                  <div className="section-eyebrow">UNITEC CONTROL CENTER</div>
                </div>
                <h1 className="hero-headline-auros" style={{ fontSize: 'var(--text-heading)', margin: '12px 0 16px 0' }}>
                  Aprobación de Credenciales
                </h1>
                <p className="hero-subhead-auros" style={{ fontSize: 'var(--text-body-lg)', margin: '0 0 var(--spacing-32) 0', maxWidth: '100%' }}>
                  Como administrador del sistema, puedes verificar las solicitudes de registro e inactivar o activar cuentas. Las cuentas inactivas tienen el ingreso bloqueado en la pasarela.
                </p>

                {loadingAdminUsers ? (
                  <div style={{ display: 'flex', justifyContent: 'center', width: '100%', margin: '40px 0' }}>
                    <div className="spinner-auros"></div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
                    {adminUsers.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-fog-veil)', opacity: 0.5, border: '1px dashed var(--color-ash-gray)', borderRadius: 'var(--radius-cards)' }}>
                        No hay usuarios registrados en el sistema.
                      </div>
                    ) : (
                      adminUsers.map((u) => {
                        const feedback = adminFeedback[u.id];
                        const isSelf = u.id === user?.id;
                        
                        return (
                          <div 
                            key={u.id}
                            className="surface-level-1"
                            style={{ 
                              display: 'flex', 
                              flexDirection: 'column',
                              padding: '20px', 
                              borderRadius: 'var(--radius-cards)',
                              border: '1px solid var(--color-ash-gray)',
                              backgroundColor: 'var(--surface-trench)',
                              gap: '16px'
                            }}
                          >
                            {/* Fila 1: Datos del usuario */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                              <div style={{ color: 'var(--color-snow-sheet)', fontWeight: 500, fontSize: '15px', wordBreak: 'break-all' }}>
                                {u.email} {isSelf && <span style={{ fontSize: '11px', color: 'var(--color-lilac-wisp)' }}>(Tú)</span>}
                              </div>
                              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                <span style={{ 
                                  padding: '4px 8px', 
                                  borderRadius: '4px', 
                                  fontSize: '11px', 
                                  fontWeight: 500,
                                  backgroundColor: u.is_active ? '#e6fbf3' : '#ffebeb', 
                                  color: u.is_active ? '#007353' : '#d32f2f' 
                                }}>
                                  ● {u.is_active ? 'Aprobado' : 'Inactivo'}
                                </span>
                                <span style={{ 
                                  padding: '4px 8px', 
                                  borderRadius: '4px', 
                                  fontSize: '11px', 
                                  fontWeight: 500,
                                  backgroundColor: u.is_admin ? '#e8f0fe' : '#f1f5f9', 
                                  color: u.is_admin ? '#1a73e8' : '#475569' 
                                }}>
                                  {u.is_admin ? 'Super Admin' : 'Usuario'}
                                </span>
                              </div>
                            </div>

                            {/* Separador */}
                            <div style={{ height: '1px', backgroundColor: 'var(--color-ash-gray)', opacity: 0.5 }}></div>

                            {/* Fila 2: Acciones en grid */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
                              {/* Columna A: Control de accesos y roles */}
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', justifyContent: 'center' }}>
                                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-lilac-wisp)', letterSpacing: '0.5px' }}>
                                  GESTIÓN DE ACCESOS
                                </div>
                                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                  {/* Botón de Aprobar/Rechazar */}
                                  {u.is_active ? (
                                    <button 
                                      className="btn-ghost-rounded" 
                                      onClick={async () => {
                                        await fetch(`/api/v1/auth/admin/users/${u.id}/reject`, { method: 'POST', credentials: 'include' });
                                        fetchAdminUsers();
                                      }}
                                      style={{ padding: '8px 14px', fontSize: '11px', flex: 1, minWidth: '100px' }}
                                      disabled={isSelf}
                                    >
                                      Inactivar
                                    </button>
                                  ) : (
                                    <button 
                                      className="btn-primary-gradient" 
                                      onClick={async () => {
                                        await fetch(`/api/v1/auth/admin/users/${u.id}/approve`, { method: 'POST', credentials: 'include' });
                                        fetchAdminUsers();
                                      }}
                                      style={{ padding: '8px 14px', fontSize: '11px', flex: 1, minWidth: '100px' }}
                                    >
                                      Activar / Aprobar
                                    </button>
                                  )}

                                  {/* Botón de Rol (Promover/Degradar) */}
                                  <button 
                                    className="btn-ghost-rounded" 
                                    onClick={() => handleToggleRole(u.id, u.is_admin)}
                                    style={{ padding: '8px 14px', fontSize: '11px', flex: 1, minWidth: '100px' }}
                                    disabled={isSelf}
                                  >
                                    {u.is_admin ? 'Degradar a Usuario' : 'Hacer Super Admin'}
                                  </button>
                                </div>
                              </div>

                              {/* Columna B: Cambio de contraseña */}
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-lilac-wisp)', letterSpacing: '0.5px' }}>
                                  RESTABLECER CONTRASEÑA
                                </div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <input 
                                    type="password"
                                    placeholder="Nueva clave"
                                    value={passwordInputs[u.id] || ''}
                                    onChange={(e) => setPasswordInputs(prev => ({ ...prev, [u.id]: e.target.value }))}
                                    style={{ 
                                      padding: '8px 12px', 
                                      fontSize: '12px', 
                                      borderRadius: 'var(--radius-inputs)', 
                                      border: '1px solid var(--color-ash-gray)',
                                      flex: 1,
                                      height: '34px',
                                      backgroundColor: 'var(--color-midnight-current)',
                                      color: 'var(--color-snow-sheet)'
                                    }}
                                  />
                                  <button
                                    className="btn-primary-gradient"
                                    onClick={() => handleResetPassword(u.id)}
                                    style={{ padding: '0 12px', fontSize: '11px', height: '34px', whiteSpace: 'nowrap' }}
                                  >
                                    Guardar
                                  </button>
                                </div>
                                {feedback && (
                                  <div style={{ 
                                    fontSize: '11px', 
                                    fontWeight: 500,
                                    color: feedback.isError ? '#d32f2f' : '#007353',
                                    marginTop: '2px'
                                  }}>
                                    {feedback.text}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Vista del Chat Principal */
            <>
              <div className="messages-container-auros">
                {messages.length === 0 && !streamingMessage ? (
                  <div className="empty-state-auros" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    {/* Esfera de partículas rotando en el fondo */}
                    <div className="hero-sphere-placeholder">
                      <ParticleSphere />
                    </div>

                    {/* Logotipo banner oficial de la UNITEC */}
                    <div style={{ marginBottom: '28px', display: 'flex', justifyContent: 'center' }}>
                      <img src="/logo_universidad.png" alt="UNITEC Logo" style={{ height: '70px', objectFit: 'contain' }} />
                    </div>

                    <div className="hero-eyebrow-container">
                      <div className="section-eyebrow">PORTAL DE CONSULTAS RAG</div>
                    </div>

                    <h1 className="hero-headline-auros" style={{ marginTop: '12px' }}>
                      Sistema de Información Académica
                    </h1>
                    
                    <p className="hero-subhead-auros">
                      Bienvenido al sistema institucional de la Universidad Tecnológica del Centro (UNITEC). Realiza consultas estructuradas sobre los manuales académicos, normativas de egreso y reglamentos internos en tiempo real.
                    </p>

                    <div className="demo-trigger-container">
                      <button 
                        className="btn-primary-gradient" 
                        onClick={() => {
                          if (activeSessionId) {
                            setQuery("¿Cuáles son los requisitos obligatorios para presentar el Trabajo Especial de Grado (TEG)?");
                          } else {
                            // Crear sesión antes de disparar el query demo si no hay sesión
                            createNewSession().then(() => {
                              setQuery("¿Cuáles son los requisitos obligatorios para presentar el Trabajo Especial de Grado (TEG)?");
                            });
                          }
                        }}
                      >
                        <span>Requisitos de TEG (Demo RAG)</span>
                        <HelpCircle size={14} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    {messages.map((msg) => (
                      <div key={msg.id} className={`message-bubble-auros ${msg.role}`}>
                        <div className={`avatar-auros ${msg.role}`}>
                          {msg.role === 'user' ? <User size={14} /> : <Terminal size={14} />}
                        </div>
                        <div className="message-content-auros">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      </div>
                    ))}

                    {/* Streaming del mensaje actual en generación */}
                    {isProcessing && streamingMessage && (
                      <div className="message-bubble-auros assistant">
                        <div className="avatar-auros assistant">
                          <Terminal size={14} />
                        </div>
                        <div className="message-content-auros">
                          <ReactMarkdown>{streamingMessage}</ReactMarkdown>
                        </div>
                      </div>
                    )}

                    {/* Indicador de escritura sin texto aún */}
                    {isProcessing && !streamingMessage && (
                      <div className="typing-indicator-auros">
                        <div className="typing-dot-auros"></div>
                        <div className="typing-dot-auros"></div>
                        <div className="typing-dot-auros"></div>
                      </div>
                    )}
                  </>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Formulario de entrada de texto */}
              <div className="input-container-auros">
                <form onSubmit={handleSendMessage} className="input-box-auros">
                  <textarea
                    className="chat-input-auros"
                    placeholder="Haz tu consulta al manual del estudiante..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage(e);
                      }
                    }}
                    disabled={isProcessing || !activeSessionId}
                  />
                  <button 
                    type="submit" 
                    className="btn-primary-gradient" 
                    style={{ width: '38px', height: '38px', padding: '0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                    disabled={isProcessing || !query.trim() || !activeSessionId}
                  >
                    <Send size={14} />
                  </button>
                </form>
                <div className="chat-status-bar-auros">
                  <span>Canal Seguro WebSocket</span>
                  <div style={{ 
                    width: '6px', 
                    height: '6px', 
                    borderRadius: '50%', 
                    backgroundColor: isProcessing ? '#aefadc' : '#007353',
                    boxShadow: isProcessing ? '0 0 8px #aefadc' : 'none'
                  }}></div>
                </div>
              </div>
            </>
          )}
        </main>

        {/* Panel de Fuentes Documentales */}
        {showSourcesPanel && activeSources.length > 0 && (
          <SourcesPanel 
            sources={activeSources} 
            onClose={() => setShowSourcesPanel(false)} 
          />
        )}
      </div>
    </div>
  );
};
