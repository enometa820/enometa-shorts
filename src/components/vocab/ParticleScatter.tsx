import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  spiralAngle?: number;
}

export const ParticleScatter: React.FC<VocabComponentProps> = ({
  count = 2000,
  color = "#8B5CF6",
  glow = false,
  expansion_speed = 0.3,
  variant = "default",
  audio,
  sceneProgress,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const particles = useMemo(() => {
    const arr: Particle[] = [];
    for (let i = 0; i < count; i++) {
      if (variant === "directional_wind") {
        arr.push({
          x: -10 - Math.random() * width * 0.3,
          y: Math.random() * height,
          vx: 1.0 + Math.random() * 2.0,
          vy: (Math.random() - 0.5) * 0.6,
          size: 1 + Math.random() * 2,
        });
      } else if (variant === "spiral_out") {
        const angle = (i / count) * Math.PI * 8;
        const speed = 0.5 + Math.random() * 1.5;
        arr.push({
          x: width / 2, y: height / 2,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 1 + Math.random() * 2,
          spiralAngle: angle,
        });
      } else {
        const angle = Math.random() * Math.PI * 2;
        const speed = 0.3 + Math.random() * 2;
        arr.push({
          x: width / 2, y: height / 2,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 1 + Math.random() * 2,
        });
      }
    }
    return arr;
  }, [count, width, height, variant]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const t = sceneProgress * 120 * expansion_speed;
    const sizeBoost = 1 + audio.bass * 4;
    const alpha = 0.3 + audio.rms * 0.8;

    for (const p of particles) {
      let px: number, py: number;

      if (variant === "spiral_out") {
        const spiralExtra = t * 0.02;
        const baseAngle = p.spiralAngle || 0;
        px = p.x + Math.cos(baseAngle + spiralExtra) * t * (Math.abs(p.vx) + 0.3);
        py = p.y + Math.sin(baseAngle + spiralExtra) * t * (Math.abs(p.vy) + 0.3);
      } else {
        px = p.x + p.vx * t;
        py = p.y + p.vy * t;
      }

      if (px < -20 || px > width + 20 || py < -20 || py > height + 20) continue;

      ctx.beginPath();
      ctx.arc(px, py, p.size * sizeBoost, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = alpha;
      ctx.fill();

      if (glow) {
        ctx.beginPath();
        ctx.arc(px, py, p.size * sizeBoost * 5, 0, Math.PI * 2);
        ctx.globalAlpha = alpha * 0.25;
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
  });

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ position: "absolute", top: 0, left: 0 }}
    />
  );
};
