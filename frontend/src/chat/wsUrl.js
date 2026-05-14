/**
 * URL del WebSocket de chat. En desarrollo usa el proxy de Vite (/api → backend).
 * Opcional: VITE_CHAT_WS_URL=wss://api.ejemplo.com/api/v1/chats/ws
 */
export function getChatWebSocketUrl() {
  const explicit = import.meta.env.VITE_CHAT_WS_URL;
  if (explicit) {
    return explicit;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/v1/chats/ws`;
}
