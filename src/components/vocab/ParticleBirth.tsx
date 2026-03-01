import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  birthProgress: number; // 0~1, 이 파티클이 태어나는 시점
}

export const ParticleBirth: React.FC<VocabComponentProps> = ({
  count = 2000,
  spawn_duration_sec = 4.0,
  initial_color = "#8B5CF6",
  initial_opacity = 0.6,
  size_range = [1, 3],
  audio,
  sceneProgress,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // 파티클 시드 데이터 (한 번만 생성)
  const particles = useMemo(() => {
    const arr: Particle[] = [];
    for (let i = 0; i < count; i++) {
      arr.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: size_range[0] + Math.random() * (size_range[1] - size_range[0]),
        birthProgress: i / count,
      });
    }
    return arr;
  }, [count, width, height, size_range[0], size_range[1]]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    // spawn_duration 내에서 얼마나 진행되었는지
    const spawnProgress = Math.min(sceneProgress * (1 / (spawn_duration_sec / 6)), 1);

    // 오디오 리액티브
    const sizeBoost = 1 + audio.bass * 4;
    const brightnessBoost = 0.2 + audio.rms * 0.9;

    for (const p of particles) {
      // 아직 태어나지 않은 파티클은 건너뜀
      if (p.birthProgress > spawnProgress) continue;

      // 태어난 후 얼마나 지났는지
      const lifeProgress = (spawnProgress - p.birthProgress) / (1 - p.birthProgress + 0.01);
      const alpha = Math.min(lifeProgress * 3, 1) * initial_opacity * brightnessBoost;

      // 위치 업데이트 (미세한 드리프트)
      const px = p.x + p.vx * sceneProgress * 60;
      const py = p.y + p.vy * sceneProgress * 60;

      // 파티클 그리기
      ctx.beginPath();
      ctx.arc(px % width, py % height, p.size * sizeBoost, 0, Math.PI * 2);
      ctx.fillStyle = initial_color;
      ctx.globalAlpha = alpha;
      ctx.fill();

      // 비트에 글로우 추가
      if (audio.onset && Math.random() < 0.3) {
        ctx.beginPath();
        ctx.arc(px % width, py % height, p.size * sizeBoost * 6, 0, Math.PI * 2);
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
