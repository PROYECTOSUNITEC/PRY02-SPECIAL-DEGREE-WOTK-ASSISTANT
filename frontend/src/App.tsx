import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './components/Login';
import { Chat } from './components/Chat';
import { Shield } from 'lucide-react';

// Web Audio API Synthesizer Configuration
let audioCtx: AudioContext | null = null;
let isPlaying = false;
let currentSpeed = 1.0;
let currentPhase: 'cucaracha' | 'rickroll' = 'cucaracha';
let activeTimeout: any = null;

// Melody 1: La Cucaracha
const cucarachaNotes = [
  { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, // La cu-ca
  { freq: 349.23, dur: 0.45 }, // ra
  { freq: 440.00, dur: 0.45 }, // cha
  
  { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, // la cu-ca
  { freq: 349.23, dur: 0.45 }, // ra
  { freq: 440.00, dur: 0.45 }, // cha
  
  { freq: 349.23, dur: 0.3 }, { freq: 349.23, dur: 0.15 }, // ya no
  { freq: 329.63, dur: 0.3 }, { freq: 329.63, dur: 0.15 }, // pue-de
  { freq: 293.66, dur: 0.3 }, { freq: 293.66, dur: 0.15 }, // ca-mi
  { freq: 261.63, dur: 0.6 }, // nar
  
  { freq: 0, dur: 0.3 },
  
  { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, // Por-que
  { freq: 329.63, dur: 0.45 }, // no
  { freq: 392.00, dur: 0.45 }, // tie
  
  { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, { freq: 261.63, dur: 0.15 }, // ne, por-que
  { freq: 329.63, dur: 0.45 }, // le
  { freq: 392.00, dur: 0.45 }, // fal
  
  { freq: 466.16, dur: 0.3 }, { freq: 440.00, dur: 0.3 }, // tan las
  { freq: 392.00, dur: 0.3 }, { freq: 349.23, dur: 0.3 }, // dos pa
  { freq: 261.63, dur: 0.45 }, // titas
  { freq: 349.23, dur: 0.6 } // tras
];

// Melody 2: Never Gonna Give You Up (Rickroll)
const rickrollNotes = [
  { freq: 466.16, dur: 0.15 }, // Bb4
  { freq: 523.25, dur: 0.15 }, // C5
  { freq: 587.33, dur: 0.15 }, // D5
  { freq: 587.33, dur: 0.3 },  // D5
  { freq: 523.25, dur: 0.3 },  // C5
  { freq: 466.16, dur: 0.15 }, // Bb4
  { freq: 523.25, dur: 0.15 }, // C5
  { freq: 587.33, dur: 0.15 }, // D5
  { freq: 349.23, dur: 0.45 }, // F4
  
  { freq: 0, dur: 0.15 },
  
  { freq: 466.16, dur: 0.15 }, // Bb4
  { freq: 523.25, dur: 0.15 }, // C5
  { freq: 587.33, dur: 0.15 }, // D5
  { freq: 587.33, dur: 0.3 },  // D5
  { freq: 523.25, dur: 0.3 },  // C5
  { freq: 466.16, dur: 0.15 }, // Bb4
  { freq: 523.25, dur: 0.15 }, // C5
  { freq: 698.46, dur: 0.3 },  // F5
  { freq: 523.25, dur: 0.45 }, // C5
  
  { freq: 0, dur: 0.15 },
  
  { freq: 466.16, dur: 0.15 }, // Bb4
  { freq: 523.25, dur: 0.15 }, // C5
  { freq: 587.33, dur: 0.15 }, // D5
  { freq: 587.33, dur: 0.3 },  // D5
  { freq: 523.25, dur: 0.3 },  // C5
  { freq: 466.16, dur: 0.15 }, // Bb4
  { freq: 523.25, dur: 0.15 }, // C5
  { freq: 587.33, dur: 0.15 }, // D5
  { freq: 349.23, dur: 0.45 }, // F4
  
  { freq: 0, dur: 0.15 },
  
  { freq: 349.23, dur: 0.15 }, // F4
  { freq: 392.00, dur: 0.15 }, // G4
  { freq: 440.00, dur: 0.15 }, // A4
  { freq: 466.16, dur: 0.3 },  // Bb4
  { freq: 523.25, dur: 0.45 }  // C5
];

const playNote = (frequency: number, startTime: number, duration: number) => {
  if (!audioCtx) return;
  const osc = audioCtx.createOscillator();
  const gainNode = audioCtx.createGain();
  
  osc.type = currentPhase === 'rickroll' ? "triangle" : "sawtooth"; // Softer sound for Rickroll
  osc.frequency.setValueAtTime(frequency, startTime);
  
  gainNode.gain.setValueAtTime(0.12, startTime);
  gainNode.gain.exponentialRampToValueAtTime(0.001, startTime + duration - 0.02);
  
  osc.connect(gainNode);
  gainNode.connect(audioCtx.destination);
  
  osc.start(startTime);
  osc.stop(startTime + duration);
};

const playMelody = (onTransition: (phase: 'cucaracha' | 'rickroll', speed: number) => void) => {
  if (isPlaying) return;
  isPlaying = true;
  currentSpeed = 1.0;
  currentPhase = 'cucaracha';
  
  audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  let loopCount = 0;
  
  const playSequence = () => {
    if (!audioCtx || !isPlaying) return;
    let time = audioCtx.currentTime;
    
    if (currentPhase === 'cucaracha') {
      const pitchScale = 1.0 + (currentSpeed - 1.0) * 0.20;
      cucarachaNotes.forEach((note) => {
        const freq = note.freq * pitchScale;
        const dur = note.dur / currentSpeed;
        if (note.freq > 0) {
          playNote(freq, time, dur);
        }
        time += dur + (0.04 / currentSpeed);
      });
      
      const totalDuration = cucarachaNotes.reduce((sum, n) => sum + (n.dur / currentSpeed) + (0.04 / currentSpeed), 0);
      
      activeTimeout = setTimeout(() => {
        if (isPlaying) {
          loopCount += 1;
          if (loopCount >= 2) {
            // Transition to Rickroll Phase!
            currentPhase = 'rickroll';
            onTransition('rickroll', 1.0);
          } else {
            currentSpeed = Math.min(currentSpeed + 0.25, 3.0);
            onTransition('cucaracha', currentSpeed);
          }
          playSequence();
        }
      }, totalDuration * 1000);
    } 
    else {
      // Rickroll Phase
      rickrollNotes.forEach((note) => {
        if (note.freq > 0) {
          playNote(note.freq, time, note.dur);
        }
        time += note.dur + 0.05;
      });
      
      const totalDuration = rickrollNotes.reduce((sum, n) => sum + n.dur + 0.05, 0);
      
      activeTimeout = setTimeout(() => {
        if (isPlaying) {
          playSequence();
        }
      }, totalDuration * 1000);
    }
  };
  
  playSequence();
};

const stopAudio = () => {
  isPlaying = false;
  if (activeTimeout) {
    clearTimeout(activeTimeout);
    activeTimeout = null;
  }
  if (audioCtx) {
    audioCtx.close();
    audioCtx = null;
  }
};

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [cucarachaActive, setCucarachaActive] = useState<boolean>(false);
  const [phase, setPhase] = useState<'cucaracha' | 'rickroll'>('cucaracha');
  const [intensity, setIntensity] = useState<number>(1.0);

  // DevTools detection & Prevention
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isF12 = e.key === 'F12';
      const isInspect = (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C'));
      const isViewSource = (e.ctrlKey && e.key === 'U');
      
      if (isF12 || isInspect || isViewSource) {
        e.preventDefault();
        setCucarachaActive(true);
      }
    };

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('contextmenu', handleContextMenu);
    
    // Periodical DevTools Detection Loop (debugger check + window dimension check)
    const checkInterval = setInterval(() => {
      const threshold = 160;
      const widthDiff = window.outerWidth - window.innerWidth;
      const heightDiff = window.outerHeight - window.innerHeight;
      if (widthDiff > threshold || heightDiff > threshold) {
        setCucarachaActive(true);
      }

      // Debugger detection
      const start = performance.now();
      debugger;
      const end = performance.now();
      if (end - start > 100) {
        setCucarachaActive(true);
      }
    }, 1500);

    // Initial console warning banner
    console.log(
      "%c¡ALTO! %cEsta consola está protegida y monitoreada para fines académicos de la UNITEC. Intentar alterar el código activará la alarma.",
      "color: red; font-size: 30px; font-weight: bold;",
      "color: #475569; font-size: 14px;"
    );

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('contextmenu', handleContextMenu);
      clearInterval(checkInterval);
    };
  }, []);

  // Control Audio & Console Deactivation
  useEffect(() => {
    if (cucarachaActive) {
      const noop = () => {};
      try {
        (window as any).console.log = noop;
        (window as any).console.warn = noop;
        (window as any).console.error = noop;
        (window as any).console.info = noop;
        (window as any).console.debug = noop;
        (window as any).console.clear();
      } catch (e) {}

      setIntensity(1.0);
      setPhase('cucaracha');
      playMelody((currentPhase, speed) => {
        setPhase(currentPhase);
        setIntensity(speed);
      });
    } else {
      stopAudio();
      setIntensity(1.0);
      setPhase('cucaracha');
    }
    return () => stopAudio();
  }, [cucarachaActive]);

  if (cucarachaActive) {
    const isRickroll = phase === 'rickroll';
    
    return (
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          color: '#ffffff',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 999999,
          fontFamily: 'var(--font-matter)',
          textAlign: 'center',
          padding: '20px',
          transition: 'all 0.5s ease',
          animation: isRickroll 
            ? 'disco-lights 3s linear infinite alternate' 
            : `flash-alert ${1.5 / intensity}s ease-in-out infinite alternate`
        }}
      >
        <div style={{
          animation: isRickroll ? 'disco-bounce 1s infinite alternate' : 'pulse 1.2s infinite alternate',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '20px'
        }}>
          {isRickroll && (
            <div style={{ fontSize: '3rem', animation: 'spin-cockroach 10s linear infinite', position: 'absolute', top: '-100px' }}>
              🪩
            </div>
          )}
          
          <img 
            src="/hacker_cockroach.png" 
            alt="Cucaracha Hacker" 
            style={{ 
              height: '200px', 
              borderRadius: '50%', 
              border: isRickroll ? '6px solid #ec4899' : `${4 + intensity * 2}px solid #22c55e`,
              boxShadow: isRickroll ? '0 0 40px #ec4899' : `0 0 ${20 + intensity * 15}px #22c55e`,
              animation: isRickroll 
                ? 'wiggle-dance 0.5s ease-in-out infinite alternate' 
                : `spin-cockroach ${4 / intensity}s linear infinite`
            }} 
          />
          
          <h1 style={{ 
            color: isRickroll ? '#f472b6' : '#ef4444', 
            fontSize: '2.2rem', 
            fontWeight: 'bold', 
            letterSpacing: '2px', 
            margin: '10px 0',
            textShadow: isRickroll ? '0 0 10px #ec4899' : 'none'
          }}>
            {isRickroll ? '🎉 ¡RICKROLL ALUMNI UNITEC! 🎉' : '🚨 ¡CUCARACHA HACKER DETECTADA! 🚨'}
          </h1>
          
          <p style={{ color: '#cbd5e1', fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto 10px auto' }}>
            {isRickroll 
              ? 'El sistema de seguridad de la UNITEC determinó que tienes un gusto impecable. ¡Disfruta de este clásico de Rick Astley mientras cierras la consola!'
              : 'Se ha detectado el intento de inspeccionar el código fuente del portal. La Inteligencia Artificial ha activado el protocolo de alarma sonora.'}
          </p>
          
          <div style={{ fontStyle: 'italic', color: isRickroll ? '#38bdf8' : '#22c55e', fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '20px' }}>
            {isRickroll 
              ? '"Never gonna give you up, never gonna let you down..." 🕺🎵'
              : `"La cucaracha, la cucaracha, ya no puede caminar..." 🎵 (Intensidad: ${intensity.toFixed(2)}x)`}
          </div>
          
          <button 
            className="btn-primary-gradient" 
            onClick={() => setCucarachaActive(false)}
            style={{ 
              padding: '12px 28px', 
              fontSize: '12px', 
              cursor: 'pointer', 
              border: 'none', 
              borderRadius: 'var(--radius-tags)',
              backgroundColor: isRickroll ? 'var(--gradient-aurora)' : undefined,
              boxShadow: isRickroll ? '0 0 15px #ec4899' : undefined
            }}
          >
            {isRickroll ? 'PROMETO PORTARME BIEN (VOLVER)' : 'DESACTIVAR ALARMA Y VOLVER'}
          </button>
        </div>
        
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes spin-cockroach {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          @keyframes pulse {
            0% { transform: scale(0.97); }
            100% { transform: scale(1.03); }
          }
          @keyframes flash-alert {
            0% { background-color: #0f172a; }
            100% { background-color: #450a0a; }
          }
          @keyframes disco-lights {
            0% { background-color: #4c1d95; } /* Purple */
            33% { background-color: #172554; } /* Blue */
            66% { background-color: #4c0519; } /* Dark Pink */
            100% { background-color: #022c22; } /* Teal */
          }
          @keyframes disco-bounce {
            0% { transform: translateY(-5px); }
            100% { transform: translateY(5px); }
          }
          @keyframes wiggle-dance {
            0% { transform: rotate(-10deg) scale(1.05); }
            100% { transform: rotate(10deg) scale(0.95); }
          }
        `}} />
      </div>
    );
  }

  if (loading) {
    return (
      <div 
        style={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh', 
          width: '100vw',
          backgroundColor: 'var(--bg-primary)',
          gap: '20px'
        }}
      >
        <div className="avatar assistant glow-active" style={{ width: '64px', height: '64px' }}>
          <Shield size={32} />
        </div>
        <div className="spinner" style={{ width: '24px', height: '24px' }}></div>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', letterSpacing: '0.05em' }}>
          VERIFICANDO CREDENCIALES
        </span>
      </div>
    );
  }

  return user ? <Chat /> : <Login />;
};

function App() {
  return (
    <AuthProvider>
      <div className="app-container">
        <AppContent />
      </div>
    </AuthProvider>
  );
}

export default App;
