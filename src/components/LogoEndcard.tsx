import React, { useRef, useEffect } from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";

/**
 * ENOMETA 로고 엔드카드
 * 파티클이 흩어졌다가 "ENOMETA" 텍스트로 수렴하는 애니메이션.
 * 원본: EnometaLogoV2.jsx → Remotion 프레임 기반으로 변환.
 */

const PARTICLE_COUNT = 3000;

// 결정론적 랜덤 (프레임 기반 렌더링을 위해)
function seededRandom(seed: number): number {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}

function easeInOutQuart(t: number): number {
  return t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2;
}

function hexToRGBA(hex: string, alpha: number): string {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

interface LogoEndcardProps {
  startFrame: number; // 엔드카드 시작 프레임
  durationFrames: number; // 엔드카드 길이 (프레임)
}

export const LogoEndcard: React.FC<LogoEndcardProps> = ({
  startFrame,
  durationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const textPixelsRef = useRef<{ x: number; y: number }[]>([]);
  const initRef = useRef(false);

  const W = 1080;
  const H = 1920;
  const localFrame = frame - startFrame;
  const t = localFrame / fps;

  // 팔레트 — phantom (원본과 동일)
  const palette = {
    bg: "#06060A",
    accent: "#8B5CF6",
    glow: "#7C3AED",
    sub: "#4C1D95",
    particles: ["#FFFFFF", "#C8C8D0", "#8888AA", "#555577", "#AAAACC"],
  };

  // 텍스트 픽셀 추출 (1회)
  useEffect(() => {
    if (initRef.current) return;
    const offscreen = document.createElement("canvas");
    offscreen.width = W;
    offscreen.height = H;
    const ctx = offscreen.getContext("2d")!;

    ctx.fillStyle = "#FFFFFF";
    ctx.font = `200 110px "Pretendard Variable", "Segoe UI", sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    // letterSpacing은 fillText 전에 설정
    (ctx as any).letterSpacing = "35px";
    ctx.fillText("ENOMETA", W / 2 + 18, H / 2 - 60);

    const imageData = ctx.getImageData(0, 0, W, H);
    const pixels: { x: number; y: number }[] = [];
    const step = 3;
    for (let y = 0; y < H; y += step) {
      for (let x = 0; x < W; x += step) {
        const i = (y * W + x) * 4;
        if (imageData.data[i + 3] > 100) {
          pixels.push({ x, y });
        }
      }
    }
    textPixelsRef.current = pixels;
    initRef.current = true;
  }, []);

  // 매 프레임 캔버스 렌더링
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !initRef.current || localFrame < 0) return;
    const ctx = canvas.getContext("2d")!;
    const pixels = textPixelsRef.current;
    if (pixels.length === 0) return;

    // 캔버스 클리어
    ctx.fillStyle = palette.bg;
    ctx.fillRect(0, 0, W, H);

    // 타이밍
    const scatterEnd = 0.8; // 0.8초까지 흩어짐
    const convergeDuration = 3.2; // 3.2초에 걸쳐 수렴

    let convergeProgress = 0;
    if (t > scatterEnd) {
      convergeProgress = Math.min((t - scatterEnd) / convergeDuration, 1);
      convergeProgress = easeInOutQuart(convergeProgress);
    }

    // 액센트 파티클 위치 저장 (연결선용)
    const accentPositions: { x: number; y: number }[] = [];

    // 파티클 그리기
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const r1 = seededRandom(i);
      const r2 = seededRandom(i + 10000);
      const r3 = seededRandom(i + 20000);
      const r4 = seededRandom(i + 30000);
      const r5 = seededRandom(i + 40000);
      const isAccent = r5 < 0.08;
      const delay = r4 * 0.5;

      // 초기 위치 (원형으로 흩어진 상태)
      const angle = r1 * Math.PI * 2;
      const radius = Math.max(W, H) * 0.35 + r2 * 400;
      const initX = W / 2 + Math.cos(angle) * radius;
      const initY = H / 2 + Math.sin(angle) * radius;

      // 목표 위치 (텍스트 픽셀)
      const target = pixels[i % pixels.length];

      // 개별 진행도 (딜레이 적용)
      const pp = Math.max(
        0,
        Math.min(1, (convergeProgress - delay) / (1 - delay))
      );

      // 노이즈 (수렴 중 유기적 움직임)
      const noiseX = Math.sin(t * 1.5 + i * 3.7) * (1 - pp) * 20;
      const noiseY = Math.cos(t * 1.2 + i * 2.3) * (1 - pp) * 20;

      // 안착 후 호흡 (미세한 떨림)
      const breatheX = pp > 0.85 ? Math.sin(t * 0.8 + i * 5) * 0.6 : 0;
      const breatheY = pp > 0.85 ? Math.cos(t * 0.6 + i * 4) * 0.6 : 0;

      // 흩어짐 단계 떠돌기
      const wanderX = t < scatterEnd ? Math.sin(t * 2 + i) * 4 : 0;
      const wanderY = t < scatterEnd ? Math.cos(t * 1.5 + i * 2) * 4 : 0;

      // 최종 위치 = lerp(초기, 목표, 진행도) + 노이즈
      const x =
        initX + (target.x - initX) * pp + noiseX + breatheX + wanderX;
      const y =
        initY + (target.y - initY) * pp + noiseY + breatheY + wanderY;

      // 크기 & 투명도
      const baseAlpha = 0.2 + r3 * 0.8;
      const alpha = baseAlpha * (0.15 + pp * 0.85);
      const settled = pp > 0.7 && Math.abs(x - target.x) < 15;
      const size = isAccent
        ? (1 + r3 * 1.5) * (settled ? 1.0 : 0.8 + (1 - pp) * 0.8)
        : (0.5 + r3 * 1.5) * (0.8 + (1 - pp) * 0.8);
      const color = isAccent
        ? palette.accent
        : palette.particles[
            Math.floor(r3 * palette.particles.length) %
              palette.particles.length
          ];

      // 파티클 본체
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fillStyle = hexToRGBA(color, alpha);
      ctx.fill();

      // 액센트 글로우
      if (isAccent && settled) {
        const glowPulse = 0.5 + Math.sin(t * 3 + i) * 0.3;
        ctx.beginPath();
        ctx.arc(x, y, size * 6, 0, Math.PI * 2);
        ctx.fillStyle = hexToRGBA(palette.glow, 0.035 * glowPulse);
        ctx.fill();

        accentPositions.push({ x, y });
      }
    }

    // 액센트 파티클 연결선 (수렴 후)
    if (convergeProgress > 0.85) {
      const lineAlpha = 0.05 * ((convergeProgress - 0.85) / 0.15);
      ctx.strokeStyle = hexToRGBA(palette.accent, lineAlpha);
      ctx.lineWidth = 0.5;
      for (let i = 0; i < accentPositions.length; i++) {
        for (let j = i + 1; j < accentPositions.length; j++) {
          const dx = accentPositions[i].x - accentPositions[j].x;
          const dy = accentPositions[i].y - accentPositions[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 70) {
            ctx.beginPath();
            ctx.moveTo(accentPositions[i].x, accentPositions[i].y);
            ctx.lineTo(accentPositions[j].x, accentPositions[j].y);
            ctx.stroke();
          }
        }
      }
    }

    // 스캔라인 효과 (수렴 후)
    if (convergeProgress > 0.9) {
      const scanY = ((t * 50) % (H + 100)) - 50;
      const grad = ctx.createLinearGradient(0, scanY - 40, 0, scanY + 40);
      grad.addColorStop(0, "rgba(255,255,255,0)");
      grad.addColorStop(0.5, "rgba(255,255,255,0.01)");
      grad.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, scanY - 40, W, 80);
    }
  }, [frame, localFrame, t]);

  // 엔드카드 영역 밖이면 렌더링하지 않음
  if (localFrame < 0 || localFrame >= durationFrames) return null;

  // 전체 페이드인/아웃
  const fadeIn = interpolate(localFrame, [0, fps * 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    localFrame,
    [durationFrames - fps * 0.8, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );
  const opacity = fadeIn * fadeOut;

  // 태그라인 등장 (수렴 완료 후)
  const taglineOpacity = interpolate(
    localFrame,
    [fps * 4.2, fps * 5.0],
    [0, 0.35],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: W,
        height: H,
        opacity,
        zIndex: 100,
      }}
    >
      {/* 배경 (캔버스 아래) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: W,
          height: H,
          backgroundColor: "#06060A",
        }}
      />

      {/* 파티클 캔버스 */}
      <canvas
        ref={canvasRef}
        width={W}
        height={H}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: W,
          height: H,
        }}
      />

      {/* 태그라인 */}
      <div
        style={{
          position: "absolute",
          bottom: 580,
          left: 0,
          width: W,
          textAlign: "center",
          opacity: taglineOpacity,
          fontFamily: "Pretendard Variable, sans-serif",
          fontSize: 18,
          letterSpacing: "0.4em",
          color: palette.accent,
          fontWeight: 300,
        }}
      >
        존재와 사유, 그 경계를 초월하다
      </div>
    </div>
  );
};
