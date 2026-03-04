import React, { useRef, useEffect } from "react";
import { VocabComponentProps } from "../../types";

/**
 * Lissajous — 두 사인파의 위상차로 기하학적 패턴 생성
 * x = sin(a·t + δ), y = cos(b·t)
 * 데이터아트 정체성: 수학적 우아함 + 오디오 리액티브
 */

function hexToRGBA(hex: string, alpha: number): string {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export const Lissajous: React.FC<VocabComponentProps> = ({
  ratioA = 3,
  ratioB = 2,
  phaseOffset = 0,
  color = "#8B5CF6",
  glowColor = "#7C3AED",
  lineWidth = 2,
  trailLength = 800,
  audio,
  sceneProgress,
  frame = 0,
  fps = 30,
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

    const cx = width / 2;
    const cy = height / 2;
    const t = frame / fps;

    // 스케일: 화면 크기에 맞추기
    const scale = Math.min(width, height) * 0.35;

    // 오디오 리액티브 변조
    const rmsBoost = 1 + audio.rms * 0.4;
    const bassPhase = audio.bass * 0.5;
    const dynamicLineWidth = (lineWidth + audio.rms * 3) * rmsBoost;

    // 위상: 시간에 따라 천천히 변화 + 오디오 반응
    const phase = phaseOffset + t * 0.3 + bassPhase;

    // 씬 진행에 따른 점진적 복잡도 증가
    const complexity = 0.3 + sceneProgress * 0.7;
    const points = Math.floor(trailLength * complexity);

    // 글로우 레이어 (넓은 선)
    ctx.beginPath();
    for (let i = 0; i < points; i++) {
      const progress = i / points;
      const angle = progress * Math.PI * 2 * 4; // 4바퀴

      const x = cx + Math.sin(ratioA * angle + phase) * scale;
      const y = cy + Math.cos(ratioB * angle) * scale;

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = hexToRGBA(glowColor, 0.08 + audio.rms * 0.12);
    ctx.lineWidth = dynamicLineWidth * 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();

    // 메인 곡선 (세그먼트별 알파 그라데이션)
    const segmentSize = Math.max(1, Math.floor(points / 60));
    for (let seg = 0; seg < points - segmentSize; seg += segmentSize) {
      ctx.beginPath();
      for (let i = seg; i <= Math.min(seg + segmentSize, points - 1); i++) {
        const progress = i / points;
        const angle = progress * Math.PI * 2 * 4;

        const x = cx + Math.sin(ratioA * angle + phase) * scale;
        const y = cy + Math.cos(ratioB * angle) * scale;

        if (i === seg) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }

      // 트레일 알파: 끝으로 갈수록 투명
      const segProgress = seg / points;
      const alpha = 0.2 + (1 - segProgress) * 0.6 + audio.rms * 0.2;
      ctx.strokeStyle = hexToRGBA(color, Math.min(alpha, 0.9));
      ctx.lineWidth = dynamicLineWidth;
      ctx.lineCap = "round";
      ctx.stroke();
    }

    // 선도점 (현재 위치 글로우)
    const headAngle = (points / points) * Math.PI * 2 * 4;
    const headX = cx + Math.sin(ratioA * headAngle + phase) * scale;
    const headY = cy + Math.cos(ratioB * headAngle) * scale;

    const headGlow = ctx.createRadialGradient(
      headX, headY, 0,
      headX, headY, 15 + audio.rms * 20,
    );
    headGlow.addColorStop(0, hexToRGBA(color, 0.8));
    headGlow.addColorStop(0.5, hexToRGBA(glowColor, 0.3));
    headGlow.addColorStop(1, hexToRGBA(glowColor, 0));
    ctx.beginPath();
    ctx.arc(headX, headY, 15 + audio.rms * 20, 0, Math.PI * 2);
    ctx.fillStyle = headGlow;
    ctx.fill();

    // 교차점 강조 (곡선이 자체 교차하는 지점에 글로우)
    if (sceneProgress > 0.4 && audio.onset) {
      const numHighlights = 3 + Math.floor(audio.bass * 5);
      for (let h = 0; h < numHighlights; h++) {
        const hAngle = (h / numHighlights) * Math.PI * 2 * 4;
        const hx = cx + Math.sin(ratioA * hAngle + phase) * scale;
        const hy = cy + Math.cos(ratioB * hAngle) * scale;
        const hGlow = ctx.createRadialGradient(hx, hy, 0, hx, hy, 8);
        hGlow.addColorStop(0, hexToRGBA("#FFFFFF", 0.6));
        hGlow.addColorStop(1, hexToRGBA(color, 0));
        ctx.beginPath();
        ctx.arc(hx, hy, 8, 0, Math.PI * 2);
        ctx.fillStyle = hGlow;
        ctx.fill();
      }
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
