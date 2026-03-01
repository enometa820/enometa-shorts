import React, { useRef, useEffect } from "react";
import { VocabComponentProps } from "../../types";

/**
 * LightSource — 빛/희망/각성 표현
 * 중심 광원 + God Rays + 확산 파티클
 * scene_10, scene_11 (빛/희망) 용
 */

export const LightSource: React.FC<VocabComponentProps> = ({
  rays = 12,
  color = "#FFD700",
  audio,
  sceneProgress,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const cx = width / 2;
    const cy = height / 2;
    const time = sceneProgress * 10;

    // God Rays
    for (let i = 0; i < rays; i++) {
      const baseAngle = (i / rays) * Math.PI * 2;
      const angle = baseAngle + Math.sin(time * 0.5 + i) * 0.15;
      const rayLength = 350 + Math.sin(time + i * 1.5) * 80 + audio.mid * 100;
      const rayWidth = 0.08 + audio.rms * 0.06;

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      const x1 = cx + Math.cos(angle - rayWidth) * rayLength;
      const y1 = cy + Math.sin(angle - rayWidth) * rayLength;
      const x2 = cx + Math.cos(angle + rayWidth) * rayLength;
      const y2 = cy + Math.sin(angle + rayWidth) * rayLength;
      ctx.lineTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.closePath();

      const gradient = ctx.createLinearGradient(cx, cy,
        cx + Math.cos(angle) * rayLength,
        cy + Math.sin(angle) * rayLength
      );
      const alpha = 0.06 + audio.rms * 0.08 + Math.sin(time * 2 + i * 0.7) * 0.03;
      gradient.addColorStop(0, `rgba(255, 255, 200, ${alpha * 2})`);
      gradient.addColorStop(0.5, `rgba(255, 215, 0, ${alpha})`);
      gradient.addColorStop(1, "rgba(255, 215, 0, 0)");
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // 확산 링 (파동)
    const numRings = 4;
    for (let i = 0; i < numRings; i++) {
      const phase = (time * 1.5 + i * 2) % 8;
      const radius = phase * 60;
      const alpha = Math.max(0, 0.25 - phase * 0.03) * (0.5 + audio.rms * 0.5);

      if (radius > 0 && alpha > 0.01) {
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 215, 0, ${alpha})`;
        ctx.lineWidth = 2 + audio.bass * 3;
        ctx.stroke();
      }
    }

    // 확산 파티클
    const numParticles = 30;
    for (let i = 0; i < numParticles; i++) {
      const angle = (i / numParticles) * Math.PI * 2 + time * 0.3;
      const dist = 50 + ((time * 40 + i * 37) % 400);
      const x = cx + Math.cos(angle) * dist;
      const y = cy + Math.sin(angle) * dist;
      const size = 1.5 + Math.sin(time * 3 + i) * 1 + audio.high * 2;
      const pAlpha = Math.max(0, 0.5 - dist / 500) * (0.5 + audio.rms * 0.5);

      if (pAlpha > 0.01) {
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 200, ${pAlpha})`;
        ctx.fill();
      }
    }

    // 중심 광원
    const coreSize = 40 + audio.bass * 30 + Math.sin(time * 2) * 10;

    // 외부 글로우
    const outerGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreSize * 4);
    outerGlow.addColorStop(0, `rgba(255, 255, 240, ${0.15 + audio.rms * 0.2})`);
    outerGlow.addColorStop(0.3, `rgba(255, 215, 0, ${0.08 + audio.rms * 0.1})`);
    outerGlow.addColorStop(1, "rgba(255, 215, 0, 0)");
    ctx.beginPath();
    ctx.arc(cx, cy, coreSize * 4, 0, Math.PI * 2);
    ctx.fillStyle = outerGlow;
    ctx.fill();

    // 내부 코어
    const innerGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreSize);
    innerGlow.addColorStop(0, `rgba(255, 255, 255, ${0.7 + audio.rms * 0.3})`);
    innerGlow.addColorStop(0.5, `rgba(255, 240, 200, ${0.4 + audio.rms * 0.3})`);
    innerGlow.addColorStop(1, `rgba(255, 215, 0, ${0.1})`);
    ctx.beginPath();
    ctx.arc(cx, cy, coreSize, 0, Math.PI * 2);
    ctx.fillStyle = innerGlow;
    ctx.fill();
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
