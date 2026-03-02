import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface OrbitParticle {
  angle: number;
  radius: number;
  speed: number;
  size: number;
  orbitOffset: number;
  radiusY?: number;
}

export const ParticleOrbit: React.FC<VocabComponentProps> = ({
  count = 1900,
  color = "#555577",
  orbit_radius = 300,
  orbit_speed = 0.5,
  variant = "default",
  audio,
  audioReactive,
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
    const arr: OrbitParticle[] = [];
    for (let i = 0; i < count; i++) {
      const rY = variant === "ellipse_drift"
        ? orbit_radius * (0.3 + Math.random() * 0.5)
        : undefined;
      arr.push({
        angle: Math.random() * Math.PI * 2,
        radius: orbit_radius * (0.5 + Math.random() * 0.8),
        speed: orbit_speed * (0.6 + Math.random() * 0.8),
        size: 1 + Math.random() * 1.5,
        orbitOffset: (Math.random() - 0.5) * 30,
        radiusY: rY,
      });
    }
    return arr;
  }, [count, orbit_radius, orbit_speed, variant]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const time = frame / fps;
    const radiusMod = audio.bass * 100;
    const shake = audio.onset ? 30 : 0;
    const alpha = 0.3 + audio.rms * 0.7;

    for (const p of particles) {
      const currentAngle = p.angle + time * p.speed;
      let px: number, py: number;

      if (variant === "ellipse_drift") {
        const rX = p.radius + radiusMod + p.orbitOffset;
        const rY = (p.radiusY || p.radius * 0.6) + radiusMod * 0.5;
        const drift = time * 0.15;
        const ex = Math.cos(currentAngle) * rX;
        const ey = Math.sin(currentAngle) * rY;
        px = cx + ex * Math.cos(drift) - ey * Math.sin(drift);
        py = cy + ex * Math.sin(drift) + ey * Math.cos(drift);
      } else if (variant === "figure_eight") {
        const r = p.radius + radiusMod + p.orbitOffset;
        const a = currentAngle;
        const denom = 1 + Math.sin(a) * Math.sin(a);
        px = cx + (r * Math.cos(a)) / denom;
        py = cy + (r * Math.sin(a) * Math.cos(a)) / denom;
      } else {
        const currentRadius = p.radius + radiusMod + p.orbitOffset;
        px = cx + Math.cos(currentAngle) * currentRadius;
        py = cy + Math.sin(currentAngle) * currentRadius;
      }

      px += (Math.random() - 0.5) * shake;
      py += (Math.random() - 0.5) * shake;

      ctx.beginPath();
      ctx.arc(px, py, p.size, 0, Math.PI * 2);
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
