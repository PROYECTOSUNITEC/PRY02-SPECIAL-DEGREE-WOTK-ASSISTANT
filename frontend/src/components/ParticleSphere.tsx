import React, { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  z: number;
  px: number; // projected x
  py: number; // projected y
  color: string;
}

export const ParticleSphere: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const requestRef = useRef<number | null>(null);
  
  // Guardar coordenadas del mouse
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = canvas.width = canvas.offsetWidth;
    let height = canvas.height = canvas.offsetHeight;

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth;
      height = canvas.height = canvas.offsetHeight;
    };
    window.addEventListener('resize', handleResize);

    // Configuración de la esfera
    const particleCount = 280;
    const sphereRadius = Math.min(width, height) * 0.35;
    const particles: Particle[] = [];

    // Distribuir partículas uniformemente en una esfera (Algoritmo de Fibonacci)
    const phi = Math.PI * (3 - Math.sqrt(5)); // golden angle in radians

    for (let i = 0; i < particleCount; i++) {
      const y = 1 - (i / (particleCount - 1)) * 2; // y va de 1 a -1
      const radiusAtY = Math.sqrt(1 - y * y); // radio en este corte horizontal de la esfera

      const theta = phi * i; // rotación angular

      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;

      // Color de partícula bioluminiscente en degradado
      // Gradación aleatoria entre Tide Pool Teal (#007353) e Ice Mint (#d5f7ed)
      const ratio = Math.random();
      const color = ratio > 0.6 
        ? '#aefadc' // Luminous Mint Green
        : ratio > 0.2 
          ? '#007353' // Saturated Institutional Green
          : '#d5f7ed'; // Ice Mint Green Tint

      particles.push({
        x: x * sphereRadius,
        y: y * sphereRadius,
        z: z * sphereRadius,
        px: 0,
        py: 0,
        color
      });
    }

    // Ángulos de rotación iniciales
    let angleX = 0.002;
    let angleY = 0.003;

    // Control del mouse
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left - width / 2;
      const my = e.clientY - rect.top - height / 2;
      mouseRef.current.targetX = mx;
      mouseRef.current.targetY = my;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.active = false;
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    // Funciones de rotación 3D
    const rotateX = (p: Particle, angle: number) => {
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      const y1 = p.y * cos - p.z * sin;
      const z1 = p.z * cos + p.y * sin;
      p.y = y1;
      p.z = z1;
    };

    const rotateY = (p: Particle, angle: number) => {
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      const x1 = p.x * cos - p.z * sin;
      const z1 = p.z * cos + p.x * sin;
      p.x = x1;
      p.z = z1;
    };

    // Bucle de renderizado
    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Suavizar movimiento del mouse (Interpolación)
      const mouse = mouseRef.current;
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      // Velocidad de rotación influenciada por la interacción del mouse
      let currentAngleX = angleX;
      let currentAngleY = angleY;

      if (mouse.active) {
        currentAngleX += mouse.y * 0.00003;
        currentAngleY += mouse.x * 0.00003;
      }

      // Dibujar resplandor radial de fondo muy tenue (Twilight radial-ish effect)
      const radialGlow = ctx.createRadialGradient(
        width / 2, height / 2, 0,
        width / 2, height / 2, sphereRadius * 1.5
      );
      radialGlow.addColorStop(0, 'rgba(0, 115, 83, 0.06)');
      radialGlow.addColorStop(0.5, 'rgba(224, 235, 213, 0.01)');
      radialGlow.addColorStop(1, 'rgba(11, 26, 22, 0)');
      ctx.fillStyle = radialGlow;
      ctx.fillRect(0, 0, width, height);

      // Ordenar partículas por profundidad (Z) para pintarlas correctamente (Painters Algorithm)
      particles.sort((a, b) => b.z - a.z);

      // Proyectar y dibujar partículas
      const fov = 400; // Distancia focal
      const centerX = width / 2;
      const centerY = height / 2;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Rotar partícula
        rotateX(p, currentAngleX);
        rotateY(p, currentAngleY);

        // Proyección de perspectiva simple
        const scale = fov / (fov + p.z);
        p.px = centerX + p.x * scale;
        p.py = centerY + p.y * scale;

        // Calcular tamaño y opacidad según profundidad
        // El rango de Z es aprox [-sphereRadius, sphereRadius]
        const depthRatio = (p.z + sphereRadius) / (2 * sphereRadius); // 0 (al fondo) a 1 (al frente)
        const size = Math.max(0.5, scale * (1.2 + depthRatio * 1.6));
        const alpha = Math.max(0.08, 0.15 + depthRatio * 0.75);

        // Renderizar partícula con glow sutil
        ctx.beginPath();
        ctx.arc(p.px, p.py, size, 0, Math.PI * 2);
        
        // Puntos más cercanos tienen más brillo
        ctx.fillStyle = p.color;
        ctx.globalAlpha = alpha;
        ctx.fill();

        // Pequeño resplandor para las partículas más frontales
        if (depthRatio > 0.8) {
          ctx.beginPath();
          ctx.arc(p.px, p.py, size * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = '#aefadc';
          ctx.globalAlpha = alpha * 0.25;
          ctx.fill();
        }
      }
      
      ctx.globalAlpha = 1.0;

      // Dibujar algunas conexiones sutiles entre nodos cercanos
      // Sólo para partículas al frente para no saturar de líneas
      ctx.strokeStyle = 'rgba(174, 250, 220, 0.05)';
      ctx.lineWidth = 0.5;
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];
        if (p1.z < 0) continue; // Ignorar el hemisferio trasero

        let connections = 0;
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          if (p2.z < 0 || connections > 2) continue;

          // Distancia euclidiana 3D
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dz = p1.z - p2.z;
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

          // Si están cerca, trazar línea
          if (dist < sphereRadius * 0.3) {
            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.stroke();
            connections++;
          }
        }
      }

      requestRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (canvas) {
        canvas.removeEventListener('mousemove', handleMouseMove);
        canvas.removeEventListener('mouseleave', handleMouseLeave);
      }
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, []);

  return (
    <canvas 
      ref={canvasRef} 
      className="particle-canvas-container"
      style={{ width: '100%', height: '100%', display: 'block' }}
    />
  );
};
