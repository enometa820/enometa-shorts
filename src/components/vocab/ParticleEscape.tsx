import React, { useRef, useEffect } from "react";
import { VocabComponentProps } from "../../types";

export const ParticleEscape: React.FC<VocabComponentProps> = ({
  escape_count = 1,
  escape_speed = 3.0,
  escape_color = "#FFFFFF",
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

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    // 씬 20% 이후 이탈 시작
    if (sceneProgress < 0.2) return;

    const escapeProgress = (sceneProgress - 0.2) / 0.8;
    const time = frame / fps;

    for (let i = 0; i < escape_count; i++) {
      const angleOffset = (i / escape_count) * Math.PI * 2;
      const orbitAngle = time * 0.5 + angleOffset;

      // 궤도에서 점점 멀어지는 이탈 궤적
      const orbitRadius = 300;
      const escapeRadius = orbitRadius + escapeProgress * escape_speed * 200;

      const px = cx + Math.cos(orbitAngle) * escapeRadius;
      const py = cy + Math.sin(orbitAngle) * escapeRadius;

      // 오디오 리액티브
      const audioBoost = audio.onset ? 2.0 : 1.0;
      const glowSize = 10 + audio.rms * 30;
      const particleSize = 4 * audioBoost;

      // 이탈 파티클 — 밝은 점
      ctx.beginPath();
      ctx.arc(px, py, particleSize, 0, Math.PI * 2);
      ctx.fillStyle = escape_color;
      ctx.globalAlpha = 1;
      ctx.fill();

      // 글로우
      const gradient = ctx.createRadialGradient(px, py, 0, px, py, glowSize);
      gradient.addColorStop(0, escape_color + "AA");
      gradient.addColorStop(1, escape_color + "00");
      ctx.beginPath();
      ctx.arc(px, py, glowSize, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.globalAlpha = 0.8;
      ctx.fill();

      // 궤적 잔상
      const trailStartX = cx + Math.cos(orbitAngle) * orbitRadius;
      const trailStartY = cy + Math.sin(orbitAngle) * orbitRadius;
      ctx.beginPath();
      ctx.moveTo(trailStartX, trailStartY);
      ctx.lineTo(px, py);
      ctx.strokeStyle = escape_color + "40";
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.5 * escapeProgress;
      ctx.stroke();
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
