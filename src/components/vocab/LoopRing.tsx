import React, { useRef, useEffect } from "react";
import { VocabComponentProps } from "../../types";

/**
 * LoopRing — 루프/반복/순환 표현
 * 동심원 + 왜곡 + 궤도 글로우
 * scene_03, scene_04, scene_07 (루프/반복) 용
 */

export const LoopRing: React.FC<VocabComponentProps> = ({
  rings = 8,
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
    const time = sceneProgress * 12;
    const maxRadius = 420;

    // 동심원 링
    for (let i = 0; i < rings; i++) {
      const baseRadius = (maxRadius / rings) * (i + 1);
      const radiusWobble = Math.sin(time * 2 + i * 0.8) * 15 * audio.bass;
      const radius = baseRadius + radiusWobble;

      // 링 회전 속도 (안쪽이 빠르게)
      const rotSpeed = (rings - i) * 0.3;
      const rot = time * rotSpeed;

      ctx.beginPath();
      const segments = 120;
      for (let s = 0; s <= segments; s++) {
        const angle = (s / segments) * Math.PI * 2 + rot;
        // 왜곡: 오디오 리액티브 + 프로그레스 기반
        const distort = Math.sin(angle * 3 + time) * (5 + audio.mid * 20);
        const r = radius + distort;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        if (s === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }

      const alpha = 0.15 + (i / rings) * 0.25 + audio.rms * 0.2;
      ctx.strokeStyle = `rgba(255, 215, 0, ${alpha})`;
      ctx.lineWidth = 1.5 + audio.bass * 2;
      ctx.stroke();

      // 글로우 링
      ctx.strokeStyle = `rgba(255, 215, 0, ${alpha * 0.3})`;
      ctx.lineWidth = 4 + audio.bass * 6;
      ctx.stroke();
    }

    // 궤도 글로우 파티클 (링 위를 도는 빛나는 점)
    for (let i = 0; i < rings; i++) {
      const baseRadius = (maxRadius / rings) * (i + 1);
      const rotSpeed = (rings - i) * 0.3;
      const angle = time * rotSpeed + i * 1.2;
      const x = cx + Math.cos(angle) * baseRadius;
      const y = cy + Math.sin(angle) * baseRadius;

      const glow = ctx.createRadialGradient(x, y, 0, x, y, 12 + audio.rms * 15);
      glow.addColorStop(0, `rgba(255, 255, 200, ${0.5 + audio.rms * 0.4})`);
      glow.addColorStop(1, "rgba(255, 215, 0, 0)");
      ctx.beginPath();
      ctx.arc(x, y, 12 + audio.rms * 15, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.fill();
    }

    // 중심 코어 — 루프의 원점
    const coreGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, 30 + audio.bass * 20);
    coreGlow.addColorStop(0, `rgba(255, 255, 255, ${0.3 + audio.rms * 0.4})`);
    coreGlow.addColorStop(0.5, `rgba(255, 215, 0, ${0.15 + audio.rms * 0.2})`);
    coreGlow.addColorStop(1, "rgba(255, 215, 0, 0)");
    ctx.beginPath();
    ctx.arc(cx, cy, 30 + audio.bass * 20, 0, Math.PI * 2);
    ctx.fillStyle = coreGlow;
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
