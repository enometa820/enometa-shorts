import React, { useRef, useEffect } from "react";
import { VocabComponentProps } from "../../types";

export const BrightnessPulse: React.FC<VocabComponentProps> = ({
  rhythm = "heartbeat",
  intensity = 0.5,
  speed = 1.0,
  color = "#FFFFFF",
  audio,
  sceneProgress,
  frame,
  fps,
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

    const time = frame / fps;
    let pulseValue: number;

    if (rhythm === "heartbeat") {
      // 심장 박동 리듬: 빠른 2연타 + 긴 휴식
      const beatPhase = (time * speed) % 1;
      if (beatPhase < 0.1) {
        pulseValue = Math.sin((beatPhase / 0.1) * Math.PI);
      } else if (beatPhase < 0.15) {
        pulseValue = 0;
      } else if (beatPhase < 0.25) {
        pulseValue = Math.sin(((beatPhase - 0.15) / 0.1) * Math.PI) * 0.7;
      } else {
        pulseValue = 0;
      }
    } else if (rhythm === "tension") {
      // 긴장감: 점점 빨라지는 펄스
      const accel = 1 + sceneProgress * 3;
      pulseValue = Math.pow(Math.sin(time * speed * accel * Math.PI) * 0.5 + 0.5, 3);
    } else {
      // 기본: 부드러운 사인파
      pulseValue = Math.sin(time * speed * Math.PI * 2) * 0.5 + 0.5;
    }

    // 오디오 리액티브: bass가 펄스를 증폭
    pulseValue = pulseValue * (1 + audio.bass * 0.5);

    const alpha = pulseValue * intensity * 0.15;

    // 중앙에서 퍼지는 밝기 펄스
    const gradient = ctx.createRadialGradient(
      width / 2, height / 2, 0,
      width / 2, height / 2, width * 0.6,
    );
    gradient.addColorStop(0, color);
    gradient.addColorStop(0.5, color + "40");
    gradient.addColorStop(1, "transparent");

    ctx.fillStyle = gradient;
    ctx.globalAlpha = alpha;
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
