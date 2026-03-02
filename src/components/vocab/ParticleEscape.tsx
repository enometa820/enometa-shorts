import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface EscapeParticle {
  angleOffset: number;
  speed: number;
  size: number;
}

export const ParticleEscape: React.FC<VocabComponentProps> = ({
  escape_count = 1,
  escape_speed = 3.0,
  escape_color = "#FFFFFF",
  variant = "default",
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

  const actualCount = variant === "explosion" ? Math.max(escape_count, 40)
    : variant === "chain_break" ? Math.max(escape_count, 8)
    : escape_count;

  const escapeParticles = useMemo(() => {
    const arr: EscapeParticle[] = [];
    for (let i = 0; i < actualCount; i++) {
      arr.push({
        angleOffset: (i / actualCount) * Math.PI * 2,
        speed: variant === "explosion"
          ? 1.5 + Math.random() * 4.0
          : escape_speed * (0.8 + Math.random() * 0.4),
        size: variant === "explosion" ? 2 + Math.random() * 4 : 4,
      });
    }
    return arr;
  }, [actualCount, escape_speed, variant]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    if (sceneProgress < 0.2) return;

    const escapeProgress = (sceneProgress - 0.2) / 0.8;
    const time = frame / fps;

    for (const ep of escapeParticles) {
      const orbitAngle = time * 0.5 + ep.angleOffset;
      const orbitRadius = 300;
      const audioBoost = audio.onset ? 3.0 : 1.0;
      const glowSize = 15 + audio.rms * 50;

      let px: number, py: number;
      let trailStartX: number, trailStartY: number;

      if (variant === "chain_break") {
        const breakDelay = ep.angleOffset / (Math.PI * 2) * 0.5;
        const localProgress = Math.max(0, escapeProgress - breakDelay) / (1 - breakDelay + 0.01);
        const escapeR = orbitRadius + localProgress * ep.speed * 150;
        const drift = localProgress * 0.5;
        px = cx + Math.cos(orbitAngle + drift) * escapeR;
        py = cy + Math.sin(orbitAngle + drift) * escapeR;
        trailStartX = cx + Math.cos(orbitAngle) * orbitRadius;
        trailStartY = cy + Math.sin(orbitAngle) * orbitRadius;
      } else if (variant === "explosion") {
        const burstProgress = Math.min(escapeProgress * 2, 1);
        const escapeR = burstProgress * ep.speed * 120;
        px = cx + Math.cos(ep.angleOffset) * escapeR;
        py = cy + Math.sin(ep.angleOffset) * escapeR;
        trailStartX = cx;
        trailStartY = cy;
      } else {
        const escapeR = orbitRadius + escapeProgress * ep.speed * 200;
        px = cx + Math.cos(orbitAngle) * escapeR;
        py = cy + Math.sin(orbitAngle) * escapeR;
        trailStartX = cx + Math.cos(orbitAngle) * orbitRadius;
        trailStartY = cy + Math.sin(orbitAngle) * orbitRadius;
      }

      if (px < -50 || px > width + 50 || py < -50 || py > height + 50) continue;

      const particleSize = ep.size * audioBoost;

      ctx.beginPath();
      ctx.arc(px, py, particleSize, 0, Math.PI * 2);
      ctx.fillStyle = escape_color;
      ctx.globalAlpha = 1;
      ctx.fill();

      const gradient = ctx.createRadialGradient(px, py, 0, px, py, glowSize);
      gradient.addColorStop(0, escape_color + "AA");
      gradient.addColorStop(1, escape_color + "00");
      ctx.beginPath();
      ctx.arc(px, py, glowSize, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.globalAlpha = 0.8;
      ctx.fill();

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
