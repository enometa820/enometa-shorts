import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

/**
 * FractalCrack — 균열/각성/깨어남 표현
 * 재귀 균열 패턴 + 빛 방출
 * variants: default (중심), edge_shatter (가장자리), web_crack (거미줄)
 */

interface CrackBranch {
  x1: number;
  y1: number;
  angle: number;
  length: number;
  depth: number;
  birthProgress: number;
}

export const FractalCrack: React.FC<VocabComponentProps> = ({
  maxDepth = 5,
  color = "#FF4444",
  variant = "default",
  audio,
  sceneProgress,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const branches = useMemo(() => {
    const arr: CrackBranch[] = [];
    const cx = width / 2;
    const cy = height / 2;

    function generate(x: number, y: number, angle: number, len: number, depth: number, progress: number) {
      if (depth > maxDepth || len < 8) return;

      arr.push({ x1: x, y1: y, angle, length: len, depth, birthProgress: progress });

      const numBranches = 2 + Math.floor(Math.random() * 2);
      for (let i = 0; i < numBranches; i++) {
        const x2 = x + Math.cos(angle) * len;
        const y2 = y + Math.sin(angle) * len;
        const newAngle = angle + (Math.random() - 0.5) * 1.2;
        const newLen = len * (0.6 + Math.random() * 0.2);
        const newProgress = progress + (1 / maxDepth) * 0.8;
        generate(x2, y2, newAngle, newLen, depth + 1, newProgress);
      }
    }

    if (variant === "edge_shatter") {
      // 가장자리/코너에서 안쪽으로 균열
      const edgePoints = [
        { x: 0, y: 0, a: Math.PI * 0.25 },
        { x: width, y: 0, a: Math.PI * 0.75 },
        { x: width, y: height, a: -Math.PI * 0.75 },
        { x: 0, y: height, a: -Math.PI * 0.25 },
        { x: width / 2, y: 0, a: Math.PI * 0.5 },
        { x: width / 2, y: height, a: -Math.PI * 0.5 },
      ];
      for (const ep of edgePoints) {
        generate(ep.x, ep.y, ep.a, 100 + Math.random() * 50, 0, 0);
      }
    } else if (variant === "web_crack") {
      // 거미줄 패턴: 방사형 + 동심원적 균열
      const numRadial = 12;
      for (let i = 0; i < numRadial; i++) {
        const angle = (i / numRadial) * Math.PI * 2;
        generate(cx, cy, angle, 60 + Math.random() * 30, 0, 0);
      }
      // 동심원 연결용 짧은 가지
      for (let r = 80; r < 350; r += 80) {
        for (let i = 0; i < 8; i++) {
          const angle = (i / 8) * Math.PI * 2 + Math.random() * 0.3;
          const sx = cx + Math.cos(angle) * r;
          const sy = cy + Math.sin(angle) * r;
          const tangent = angle + Math.PI * 0.5 + (Math.random() - 0.5) * 0.4;
          arr.push({
            x1: sx, y1: sy, angle: tangent,
            length: 30 + Math.random() * 30, depth: 2,
            birthProgress: r / 400,
          });
        }
      }
    } else {
      // default: 중심에서 여러 방향으로 균열
      const startAngles = [
        -Math.PI * 0.3, -Math.PI * 0.1, Math.PI * 0.15,
        Math.PI * 0.5, Math.PI * 0.8, -Math.PI * 0.7,
      ];
      for (const angle of startAngles) {
        generate(cx, cy, angle, 80 + Math.random() * 40, 0, 0);
      }
    }

    return arr;
  }, [maxDepth, width, height, variant]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const growProgress = Math.min(sceneProgress * 1.5, 1);

    for (const branch of branches) {
      if (branch.birthProgress > growProgress) continue;

      const localProgress = Math.min((growProgress - branch.birthProgress) * 3, 1);
      const x2 = branch.x1 + Math.cos(branch.angle) * branch.length * localProgress;
      const y2 = branch.y1 + Math.sin(branch.angle) * branch.length * localProgress;

      const lineWidth = Math.max(0.5, 3 - branch.depth * 0.5) + audio.bass * 3;

      // 빛 방출 효과
      const glowAlpha = 0.2 + audio.rms * 0.4;
      ctx.beginPath();
      ctx.moveTo(branch.x1, branch.y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = `rgba(255, 200, 100, ${glowAlpha})`;
      ctx.lineWidth = lineWidth + 6;
      ctx.stroke();

      // 균열 라인
      ctx.beginPath();
      ctx.moveTo(branch.x1, branch.y1);
      ctx.lineTo(x2, y2);
      const crackAlpha = 0.4 + localProgress * 0.4 + audio.rms * 0.4;
      ctx.strokeStyle = `rgba(255, 68, 68, ${crackAlpha})`;
      ctx.lineWidth = lineWidth;
      ctx.stroke();

      // 균열 끝 빛 파티클
      if (localProgress > 0.8 && branch.depth >= maxDepth - 1) {
        const sparkSize = 6 + (audio.onset ? 14 : 0);
        const sparkGlow = ctx.createRadialGradient(x2, y2, 0, x2, y2, sparkSize * 3);
        sparkGlow.addColorStop(0, `rgba(255, 255, 200, ${0.4 + audio.rms * 0.4})`);
        sparkGlow.addColorStop(1, "rgba(255, 100, 50, 0)");
        ctx.beginPath();
        ctx.arc(x2, y2, sparkSize * 3, 0, Math.PI * 2);
        ctx.fillStyle = sparkGlow;
        ctx.fill();
      }
    }

    // 중심 폭발 글로우 (edge_shatter에서는 생략)
    if (variant !== "edge_shatter") {
      const coreCx = width / 2;
      const coreCy = height / 2;
      const coreSize = 25 + growProgress * 40 + audio.bass * 45;
      const coreGlow = ctx.createRadialGradient(coreCx, coreCy, 0, coreCx, coreCy, coreSize);
      coreGlow.addColorStop(0, `rgba(255, 255, 255, ${0.3 + audio.rms * 0.4})`);
      coreGlow.addColorStop(0.3, `rgba(255, 100, 50, ${0.2 + audio.rms * 0.3})`);
      coreGlow.addColorStop(1, "rgba(255, 68, 68, 0)");
      ctx.beginPath();
      ctx.arc(coreCx, coreCy, coreSize, 0, Math.PI * 2);
      ctx.fillStyle = coreGlow;
      ctx.fill();
    }
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
