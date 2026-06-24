import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  getWSTicket: () => Promise<string | null>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  // Verificar si hay sesión activa al montar el componente
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/v1/auth/me', {
          credentials: 'include' // Obligatorio para cookies HttpOnly
        });
        if (res.ok) {
          const data = await res.json();
          setUser(data);
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error("Error al validar sesión:", err);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok) {
        setUser({
          id: data.user_id,
          email: data.email,
          is_active: data.is_active,
          is_admin: data.is_admin
        });
        return true;
      } else {
        setError(data.detail || "Error al iniciar sesión");
        return false;
      }
    } catch (err) {
      setError("Error de red al conectar con el servidor.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include'
      });
      const data = await res.json();
      if (res.ok) {
        // Registrar exitoso, ahora iniciamos sesión automáticamente
        return await login(email, password);
      } else {
        setError(data.detail || "Error en el registro");
        return false;
      }
    } catch (err) {
      setError("Error de red al conectar con el servidor.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } catch (err) {
      console.error("Error al cerrar sesión:", err);
    } finally {
      setUser(null);
      setLoading(false);
    }
  };

  // Solicitar ticket de WebSocket seguro de un solo uso
  const getWSTicket = async (): Promise<string | null> => {
    try {
      const res = await fetch('/api/v1/auth/ws-ticket', {
        method: 'POST',
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        return data.ticket_id;
      }
      return null;
    } catch (err) {
      console.error("Error al obtener ticket de WebSocket:", err);
      return null;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout, getWSTicket, clearError }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
};
