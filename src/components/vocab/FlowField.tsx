import React, { useRef, useEffect } from "react";
import { VocabComponentProps } from "../../types";

// 간단한 Perlin-like noise (2D simplex 대용)
const hash = (x: number, y: number): number => {
  const n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return n - Math.floor(n);
};

const smoothNoise = (x: number, y: number): number => {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;

  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);

  const a = hash(ix, iy);
  const b = hash(ix + 1, iy);
  const c = hash(ix, iy + 1);
  const d = hash(ix + 1, iy + 1);

  return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
};

const fbm = (x: number, y: number, octaves: number = 3): number => {
  let value = 0;
  let amplitude = 0.5;
  let frequency = 1;
  for (let i = 0; i < octaves; i++) {
    value += amplitude * smoothNoise(x * frequency, y * frequency);
    amplitude *= 0.5;
    frequency *= 2;
  }
  return value;
};

export const FlowField: React.FC<VocabComponentProps> = ({
  vocab = "flow_field_calm",
  noise_scale = 0.003,
  speed = 0.1,
  line_opacity = 0.15,
  line_color = "#8B5CF6",
  audio,
  sceneProgress,
  frame,
  fps,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const isTurbulent = vocab === "flow_field_turbulent";

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // 페이드 효과: 완전히 지우지 않고 반투명 배경으로 잔상
    ctx.fillStyle = "rgba(0,0,0,0.05)";
    ctx.fillRect(0, 0, width, height);

    const time = frame / fps;
    const turbulence = isTurbulent ? 2.5 : 1.0;
    const currentSpeed = speed * (1 + audio.mid * 4) * turbulence;
    const currentScale = noise_scale * turbulence;

    // flow field 라인 그리기
    const step = 20;
    const lineLen = 15 + audio.bass * 40;

    ctx.strokeStyle = line_color;
    ctx.lineWidth = 0.8;
    ctx.globalAlpha = line_opacity * (0.3 + audio.rms * 0.8);

    for (let x = 0; x < width; x += step) {
      for (let y = 0; y < height; y += step) {
        const noiseVal = fbm(
          x * currentScale + time * currentSpeed,
          y * currentScale + time * currentSpeed * 0.7,
          isTurbulent ? 4 : 3,
        );
        const angle = noiseVal * Math.PI * 4;

        const endX = x + Math.cos(angle) * lineLen;
        const endY = y + Math.sin(angle) * lineLen;

        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(endX, endY);
        ctx.stroke();
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
