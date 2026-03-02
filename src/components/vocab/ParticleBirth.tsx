import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  birthProgress: number;
  angle?: number;
}

export const ParticleBirth: React.FC<VocabComponentProps> = ({
  count = 2000,
  spawn_duration_sec = 4.0,
  initial_color = "#8B5CF6",
  initial_opacity = 0.6,
  size_range = [1, 3],
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
      const bp = i / count;
      const sz = size_range[0] + Math.random() * (size_range[1] - size_range[0]);

      if (variant === "triangles_rise") {
        arr.push({
          x: Math.random() * width,
          y: height * 0.7 + Math.random() * height * 0.3,
          vx: (Math.random() - 0.5) * 0.3,
          vy: -(0.5 + Math.random() * 1.5),
          size: sz, birthProgress: bp,
        });
      } else if (variant === "lines_scatter") {
        arr.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.8,
          vy: (Math.random() - 0.5) * 0.8,
          size: sz, birthProgress: bp,
          angle: Math.random() * Math.PI,
        });
      } else if (variant === "dots_grid") {
        const gridCols = Math.ceil(Math.sqrt(count * (width / height)));
        const gridRows = Math.ceil(count / gridCols);
        const col = i % gridCols;
        const row = Math.floor(i / gridCols);
        arr.push({
          x: (col / gridCols) * width + (Math.random() - 0.5) * 5,
          y: (row / gridRows) * height + (Math.random() - 0.5) * 5,
          vx: (Math.random() - 0.5) * 0.2,
          vy: (Math.random() - 0.5) * 0.2,
          size: sz * 0.5, birthProgress: bp,
        });
      } else {
        arr.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.5,
          vy: (Math.random() - 0.5) * 0.5,
          size: sz, birthProgress: bp,
        });
      }
    }
    return arr;
  }, [count, width, height, size_range[0], size_range[1], variant]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const spawnProgress = Math.min(sceneProgress * (1 / (spawn_duration_sec / 6)), 1);
    const sizeBoost = 1 + audio.bass * 4;
    const brightnessBoost = 0.2 + audio.rms * 0.9;

    for (const p of particles) {
      if (p.birthProgress > spawnProgress) continue;

      const lifeProgress = (spawnProgress - p.birthProgress) / (1 - p.birthProgress + 0.01);
      const alpha = Math.min(lifeProgress * 3, 1) * initial_opacity * brightnessBoost;

      const px = ((p.x + p.vx * sceneProgress * 60) % width + width) % width;
      const py = ((p.y + p.vy * sceneProgress * 60) % height + height) % height;

      ctx.globalAlpha = alpha;

      if (variant === "triangles_rise") {
        const s = p.size * sizeBoost * 3;
        ctx.beginPath();
        ctx.moveTo(px, py - s);
        ctx.lineTo(px - s * 0.7, py + s * 0.5);
        ctx.lineTo(px + s * 0.7, py + s * 0.5);
        ctx.closePath();
        ctx.fillStyle = initial_color;
        ctx.fill();
      } else if (variant === "lines_scatter") {
        const len = p.size * sizeBoost * 6;
        const a = p.angle || 0;
        ctx.beginPath();
        ctx.moveTo(px - Math.cos(a) * len, py - Math.sin(a) * len);
        ctx.lineTo(px + Math.cos(a) * len, py + Math.sin(a) * len);
        ctx.strokeStyle = initial_color;
        ctx.lineWidth = 0.8 + audio.bass * 1.5;
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.arc(px, py, p.size * sizeBoost, 0, Math.PI * 2);
        ctx.fillStyle = initial_color;
        ctx.fill();
      }

      if (audio.onset && Math.random() < 0.3) {
        ctx.beginPath();
        ctx.arc(px, py, p.size * sizeBoost * 6, 0, Math.PI * 2);
        ctx.fillStyle = initial_color;
        ctx.globalAlpha = alpha * 0.4;
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
