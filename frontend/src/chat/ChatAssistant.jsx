import { useCallback, useEffect, useRef, useState } from "react";
import { getChatWebSocketUrl } from "./wsUrl.js";
import "./ChatAssistant.css";

function nextId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function ChatAssistant() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [conn, setConn] = useState("idle");
  const wsRef = useRef(null);

  const appendMessage = useCallback((role, text) => {
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role, text, at: Date.now() },
    ]);
  }, []);

  useEffect(() => {
    const url = getChatWebSocketUrl();
    setConn("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConn("open");
    ws.onclose = () => {
      setConn("closed");
      wsRef.current = null;
    };
    ws.onerror = () => setConn("error");
    ws.onmessage = (ev) => {
      const text = typeof ev.data === "string" ? ev.data : "";
      appendMessage("assistant", text);
    };

    return () => {
      ws.onopen = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.onmessage = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      wsRef.current = null;
    };
  }, [appendMessage]);

  const send = useCallback(() => {
    const trimmed = draft.trim();
    if (!trimmed) return;
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    appendMessage("user", trimmed);
    ws.send(trimmed);
    setDraft("");
  }, [draft, appendMessage]);

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="chat-shell" aria-live="polite">
      <header className="chat-head">
        <div className="chat-head__titles">
          <h1 className="chat-head__title">Asistente</h1>
          <p className="chat-head__sub">Canal en vivo · respuesta del servidor</p>
        </div>
        <span className={`chat-pill chat-pill--${conn}`} title="Estado del socket">
          {conn === "open" && "En línea"}
          {conn === "connecting" && "Conectando…"}
          {conn === "closed" && "Desconectado"}
          {conn === "error" && "Error"}
          {conn === "idle" && "—"}
        </span>
      </header>

      <ol className="chat-log">
        {messages.length === 0 && (
          <li className="chat-empty">Escribe un mensaje; la respuesta será el texto que devuelve el WebSocket.</li>
        )}
        {messages.map((m, i) => (
          <li
            key={m.id}
            className={`chat-bubble chat-bubble--${m.role}`}
            style={{ animationDelay: `${Math.min(i, 12) * 45}ms` }}
          >
            <span className="chat-bubble__label">{m.role === "user" ? "Tú" : "Respuesta"}</span>
            <p className="chat-bubble__text">{m.text}</p>
          </li>
        ))}
      </ol>

      <footer className="chat-compose">
        <textarea
          className="chat-input"
          rows={2}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Mensaje… (Enter envía, Mayús+Enter salto)"
          disabled={conn !== "open"}
          aria-label="Mensaje para el asistente"
        />
        <button
          type="button"
          className="chat-send"
          onClick={send}
          disabled={conn !== "open" || !draft.trim()}
        >
          Enviar
        </button>
      </footer>
    </div>
  );
}
