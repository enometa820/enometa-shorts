import React, { useRef, useEffect } from "react";
import { VocabComponentProps } from "../../types";
import { lerp } from "../../utils/easing";

// hex → RGB
const hexToRgb = (hex: string): [number, number, number] => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return [0, 0, 0];
  return [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16),
  ];
};

const rgbToHex = (r: number, g: number, b: number): string => {
  return "#" + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
};

export const ColorShift: React.FC<VocabComponentProps> = ({
  vocab = "color_shift",
  from_color = "#8B5CF6",
  to_color = "#555577",
  target,
  duration_sec = 2.0,
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

    // 색상 전환 진행도
    const t = Math.min(sceneProgress * 2, 1);

    const fromRgb = hexToRgb(from_color);
    const toRgb = hexToRgb(to_color);

    const r = lerp(fromRgb[0], toRgb[0], t);
    const g = lerp(fromRgb[1], toRgb[1], t);
    const b = lerp(fromRgb[2], toRgb[2], t);

    // 반투명 오버레이로 색상 변환 표현
    const currentColor = rgbToHex(r, g, b);
    const alpha = 0.05 + audio.rms * 0.05;

    ctx.fillStyle = currentColor;
    ctx.globalAlpha = alpha;
    ctx.fillRect(0, 0, width, height);

    // 비네트 효과
    const gradient = ctx.createRadialGradient(
      width / 2, height / 2, 0,
      width / 2, height / 2, width * 0.7,
    );
    gradient.addColorStop(0, "transparent");
    gradient.addColorStop(1, currentColor + "40");
    ctx.fillStyle = gradient;
    ctx.globalAlpha = 0.3;
    ctx.fillRect(0, 0, width, height);

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
