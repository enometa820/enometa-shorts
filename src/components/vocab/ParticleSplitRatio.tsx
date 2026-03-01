import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";
import { lerp, smoothstep } from "../../utils/easing";

interface SplitParticle {
  x: number;
  y: number;
  group: "a" | "b";
  angle: number;
  radius: number;
  speed: number;
  size: number;
}

export const ParticleSplitRatio: React.FC<VocabComponentProps> = ({
  count = 2000,
  ratio_a = 0.95,
  ratio_b = 0.05,
  transition_duration_sec = 2.0,
  group_a = { color: "#555577", orbit_radius: 300, orbit_speed: 0.5 },
  group_b = { color: "#8B5CF6", speed: 1.5 },
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
    const arr: SplitParticle[] = [];
    const countA = Math.floor(count * ratio_a);

    for (let i = 0; i < count; i++) {
      const isGroupA = i < countA;
      arr.push({
        x: Math.random() * width,
        y: Math.random() * height,
        group: isGroupA ? "a" : "b",
        angle: Math.random() * Math.PI * 2,
        radius: isGroupA
          ? (group_a.orbit_radius || 300) * (0.5 + Math.random() * 0.8)
          : 100 + Math.random() * 400,
        speed: isGroupA
          ? (group_a.orbit_speed || 0.5) * (0.6 + Math.random() * 0.8)
          : (group_b.speed || 1.5) * (0.5 + Math.random()),
        size: 1 + Math.random() * 1.5,
      });
    }
    return arr;
  }, [count, ratio_a, group_a.orbit_radius, group_a.orbit_speed, group_b.speed]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const time = frame / fps;
    // 분리 트랜지션 (씬 전체 duration 대비)
    const splitProgress = smoothstep(Math.min(sceneProgress * 3, 1));

    const radiusMod = audio.bass * 50;
    const shake = audio.onset ? 10 : 0;

    for (const p of particles) {
      let px: number, py: number;
      let color: string;
      let alpha: number;

      if (p.group === "a") {
        // 그룹 A: 궤도 회전 (반복되는 생각)
        const currentAngle = p.angle + time * p.speed;
        const r = lerp(
          Math.sqrt((p.x - cx) ** 2 + (p.y - cy) ** 2),
          p.radius + radiusMod,
          splitProgress,
        );
        px = cx + Math.cos(currentAngle) * r + (Math.random() - 0.5) * shake;
        py = cy + Math.sin(currentAngle) * r + (Math.random() - 0.5) * shake;
        color = group_a.color || "#555577";
        alpha = 0.3 + audio.rms * 0.3;
      } else {
        // 그룹 B: 자유 이동 (새로운 생각)
        const wanderAngle = p.angle + time * p.speed * 0.7;
        const wanderRadius = p.radius * 0.5;
        px = lerp(p.x, cx + Math.cos(wanderAngle) * wanderRadius, splitProgress);
        py = lerp(p.y, cy + Math.sin(wanderAngle) * wanderRadius, splitProgress);
        color = group_b.color || "#8B5CF6";
        alpha = 0.6 + audio.rms * 0.3;

        // 그룹 B 글로우
        if (splitProgress > 0.5) {
          const glowSize = p.size * 4 + audio.rms * 10;
          const gradient = ctx.createRadialGradient(px, py, 0, px, py, glowSize);
          gradient.addColorStop(0, color + "60");
          gradient.addColorStop(1, color + "00");
          ctx.beginPath();
          ctx.arc(px, py, glowSize, 0, Math.PI * 2);
          ctx.fillStyle = gradient;
          ctx.globalAlpha = alpha * 0.4;
          ctx.fill();
        }
      }

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
