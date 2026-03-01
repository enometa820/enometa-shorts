import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";
import { lerp, smoothstep } from "../../utils/easing";

interface Particle {
  startX: number;
  startY: number;
  targetX: number;
  targetY: number;
  size: number;
  delay: number; // 0~1, 수렴 시작 지연
}

export const ParticleConverge: React.FC<VocabComponentProps> = ({
  count = 2000,
  color = "#8B5CF6",
  target_shape = "circle",
  target_radius = 200,
  audio,
  sceneProgress,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cx = width / 2;
  const cy = height / 2;

  const particles = useMemo(() => {
    const arr: Particle[] = [];
    for (let i = 0; i < count; i++) {
      // 타겟 위치: 원형
      const angle = (i / count) * Math.PI * 2;
      const r = target_radius * (0.3 + Math.random() * 0.7);

      arr.push({
        startX: Math.random() * width,
        startY: Math.random() * height,
        targetX: cx + Math.cos(angle) * r,
        targetY: cy + Math.sin(angle) * r,
        size: 1 + Math.random() * 2,
        delay: Math.random() * 0.4,
      });
    }
    return arr;
  }, [count, width, height, target_radius, cx, cy]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const sizeBoost = 1 + audio.bass * 3.5;
    const alpha = 0.3 + audio.rms * 0.8;

    for (const p of particles) {
      const t = Math.max(0, Math.min(1, (sceneProgress - p.delay) / (1 - p.delay)));
      const eased = smoothstep(t);

      const px = lerp(p.startX, p.targetX, eased);
      const py = lerp(p.startY, p.targetY, eased);

      ctx.beginPath();
      ctx.arc(px, py, p.size * sizeBoost, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = alpha;
      ctx.fill();
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
