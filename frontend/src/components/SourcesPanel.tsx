import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText } from 'lucide-react';

interface Source {
  titulo_seccion: string;
  numero_pagina: number;
  snippet: string;
}

interface SourcesPanelProps {
  sources: Source[];
  onClose: () => void;
}

const SourceCard: React.FC<{ source: Source }> = ({ source }) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  return (
    <div className="source-card-auros">
      <div className="source-title-auros">{source.titulo_seccion}</div>
      <div className="source-badge-auros">Página {source.numero_pagina}</div>
      
      <div 
        className="source-snippet-header-auros" 
        onClick={() => setIsOpen(!isOpen)}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <FileText size={12} style={{ color: 'var(--color-ice-mist)' }} />
          Ver fragmento citado
        </span>
        {isOpen 
          ? <ChevronUp size={14} style={{ color: 'var(--color-snow-sheet)' }} /> 
          : <ChevronDown size={14} style={{ color: 'var(--color-fog-veil)' }} />
        }
      </div>
      
      {isOpen && (
        <div className="source-snippet-content-auros">
          {source.snippet}
        </div>
      )}
    </div>
  );
};

export const SourcesPanel: React.FC<SourcesPanelProps> = ({ sources, onClose }) => {
  return (
    <aside className="sources-panel-auros glass-auros">
      <div className="sources-header-auros">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--text-body)', fontWeight: 500 }}>
          <BookOpen size={16} style={{ color: 'var(--color-ice-mist)' }} />
          <span className="section-eyebrow" style={{ fontSize: '10px' }}>Fuentes Citadas ({sources.length})</span>
        </h3>
        <button className="btn-arrow-link" onClick={onClose} title="Cerrar Panel">
          ✕
        </button>
      </div>
      
      <div className="sources-container-auros">
        {sources.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--color-fog-veil)', opacity: 0.5, marginTop: '40px', fontSize: 'var(--text-caption)' }}>
            No hay fuentes citadas para esta respuesta.
          </div>
        ) : (
          sources.map((source, index) => (
            <SourceCard key={index} source={source} />
          ))
        )}
      </div>
    </aside>
  );
};
