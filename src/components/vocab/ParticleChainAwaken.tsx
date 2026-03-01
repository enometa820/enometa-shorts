import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface AwakenParticle {
  angle: number;
  radius: number;
  size: number;
  awakenThreshold: number; // 0~1, 연쇄 점등 시점
}

export const ParticleChainAwaken: React.FC<VocabComponentProps> = ({
  count = 200,
  awaken_radius = 80,
  awaken_speed = 0.5,
  awaken_color = "#8B5CF6",
  chain_delay_ms = 100,
  audio,
  sceneProgress,
  frame,
  fps,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cx = width / 2;
  const cy = height / 2;

  const particles = useMemo(() => {
    const arr: AwakenParticle[] = [];
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 200 + Math.random() * 250;
      arr.push({
        angle,
        radius,
        size: 1.5 + Math.random() * 2,
        // 탈출 파티클에 가까운 것부터 깨어남
        awakenThreshold: 0.3 + (radius - 200) / 300 * 0.5 + Math.random() * 0.15,
      });
    }
    return arr.sort((a, b) => a.awakenThreshold - b.awakenThreshold);
  }, [count]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const glowBoost = audio.rms * 20;

    for (const p of particles) {
      const isAwake = sceneProgress > p.awakenThreshold;
      const awakeDuration = isAwake
        ? (sceneProgress - p.awakenThreshold) / (1 - p.awakenThreshold)
        : 0;

      const time = frame / fps;
      const px = cx + Math.cos(p.angle + time * 0.3) * p.radius;
      const py = cy + Math.sin(p.angle + time * 0.3) * p.radius;

      if (isAwake) {
        // 깨어난 파티클 — 밝은 색
        const alpha = Math.min(awakeDuration * 3, 1);

        ctx.beginPath();
        ctx.arc(px, py, p.size * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = awaken_color;
        ctx.globalAlpha = alpha;
        ctx.fill();

        // 글로우
        const glow = p.size * 4 + glowBoost * alpha;
        const gradient = ctx.createRadialGradient(px, py, 0, px, py, glow);
        gradient.addColorStop(0, awaken_color + "80");
        gradient.addColorStop(1, awaken_color + "00");
        ctx.beginPath();
        ctx.arc(px, py, glow, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.globalAlpha = alpha * 0.6;
        ctx.fill();
      } else {
        // 아직 잠든 파티클 — 어두운 색
        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fillStyle = "#555577";
        ctx.globalAlpha = 0.3;
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
