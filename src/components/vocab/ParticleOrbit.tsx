import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface OrbitParticle {
  angle: number;      // 시작 각도
  radius: number;     // 궤도 반지름
  speed: number;      // 각속도
  size: number;
  orbitOffset: number; // 궤도 중심 오프셋
}

export const ParticleOrbit: React.FC<VocabComponentProps> = ({
  count = 1900,
  color = "#555577",
  orbit_radius = 300,
  orbit_speed = 0.5,
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
      arr.push({
        angle: Math.random() * Math.PI * 2,
        radius: orbit_radius * (0.5 + Math.random() * 0.8),
        speed: orbit_speed * (0.6 + Math.random() * 0.8),
        size: 1 + Math.random() * 1.5,
        orbitOffset: (Math.random() - 0.5) * 30,
      });
    }
    return arr;
  }, [count, orbit_radius, orbit_speed]);

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
      const currentRadius = p.radius + radiusMod + p.orbitOffset;

      const px = cx + Math.cos(currentAngle) * currentRadius + (Math.random() - 0.5) * shake;
      const py = cy + Math.sin(currentAngle) * currentRadius + (Math.random() - 0.5) * shake;

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
