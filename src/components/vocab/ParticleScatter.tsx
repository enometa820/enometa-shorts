import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
}

export const ParticleScatter: React.FC<VocabComponentProps> = ({
  count = 2000,
  color = "#8B5CF6",
  glow = false,
  expansion_speed = 0.3,
  audio,
  sceneProgress,
  frame,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const particles = useMemo(() => {
    const arr: Particle[] = [];
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 0.3 + Math.random() * 2;
      arr.push({
        x: width / 2,
        y: height / 2,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: 1 + Math.random() * 2,
      });
    }
    return arr;
  }, [count, width, height]);

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
      const px = p.x + p.vx * t;
      const py = p.y + p.vy * t;

      // 화면 밖이면 건너뜀
      if (px < 0 || px > width || py < 0 || py > height) continue;

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
