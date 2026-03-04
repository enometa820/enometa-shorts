import React, { useRef, useEffect } from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { Palette } from "../utils/palettes";

/**
 * ENOMETA 로고 엔드카드 v2
 * 파티클이 흩어졌다가 "ENOMETA" 텍스트로 수렴 + 다이나믹 웨이브/펄스/깜빡임.
 * palette prop으로 에피소드마다 다른 색상/분위기 적용.
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
  startFrame: number;
  durationFrames: number;
  palette?: Palette;
  tagline?: string;  // B-9: 에피소드별 태그라인 (기본: "존재와 사유, 그 경계를 초월하다")
}

export const LogoEndcard: React.FC<LogoEndcardProps> = ({
  startFrame,
  durationFrames,
  palette,
  tagline = "존재와 사유, 그 경계를 초월하다",
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

  // 팔레트 — prop이 없으면 phantom 기본값
  const p = palette || {
    name: "Phantom",
    bg: "#06060A",
    accent: "#8B5CF6",
    glow: "#7C3AED",
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
    ctx.fillStyle = p.bg;
    ctx.fillRect(0, 0, W, H);

    // ===== 타이밍 (v2: 빠른 시작) =====
    const scatterEnd = 0.03;
    const convergeDuration = 2.0;

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
      const isAccent = r5 < 0.12;
      const delay = r4 * 0.5;

      // 초기 위치 (v2: 화면 안에서 시작, 더 가까운 원형)
      const angle = r1 * Math.PI * 2;
      const radius = Math.max(W, H) * 0.2 + r2 * 200;
      const initX = W / 2 + Math.cos(angle) * radius;
      const initY = H / 2 + Math.sin(angle) * radius;

      // 목표 위치 (텍스트 픽셀)
      const target = pixels[i % pixels.length];

      // 개별 진행도 (딜레이 적용)
      const pp = Math.max(
        0,
        Math.min(1, (convergeProgress - delay) / (1 - delay)),
      );

      // 노이즈 (수렴 중 유기적 움직임)
      const noiseX = Math.sin(t * 1.5 + i * 3.7) * (1 - pp) * 20;
      const noiseY = Math.cos(t * 1.2 + i * 2.3) * (1 - pp) * 20;

      // 안착 후 호흡 (v2: 진폭 증가)
      const breatheX = pp > 0.85 ? Math.sin(t * 1.2 + i * 5) * 2.5 : 0;
      const breatheY = pp > 0.85 ? Math.cos(t * 0.9 + i * 4) * 2.0 : 0;

      // 안착 후 웨이브 (v2: 텍스트가 물결처럼 살아있는 느낌)
      let waveX = 0;
      let waveY = 0;
      if (pp > 0.9) {
        const wavePhase =
          t * 2.0 + target.x * 0.005 + target.y * 0.003;
        waveX = Math.sin(wavePhase) * 3.0;
        waveY = Math.cos(wavePhase * 0.7) * 2.0;
      }

      // 흩어짐 단계 떠돌기
      const wanderX = t < scatterEnd ? Math.sin(t * 2 + i) * 4 : 0;
      const wanderY = t < scatterEnd ? Math.cos(t * 1.5 + i * 2) * 4 : 0;

      // 최종 위치
      const x =
        initX +
        (target.x - initX) * pp +
        noiseX +
        breatheX +
        waveX +
        wanderX;
      const y =
        initY +
        (target.y - initY) * pp +
        noiseY +
        breatheY +
        waveY +
        wanderY;

      // 크기 & 투명도 (v2: 더 밝게 시작)
      const baseAlpha = 0.2 + r3 * 0.8;
      const alpha = baseAlpha * (0.35 + pp * 0.65);
      const settled = pp > 0.7 && Math.abs(x - target.x) < 15;

      // v2: 정착 파티클 크기 펄스 (±30%)
      const sizePulse = settled
        ? 1.0 + Math.sin(t * 3.0 + i * 0.5) * 0.3
        : 1.0;
      let size = isAccent
        ? (1 + r3 * 1.5) * (settled ? 1.0 : 0.8 + (1 - pp) * 0.8)
        : (0.5 + r3 * 1.5) * (0.8 + (1 - pp) * 0.8);
      size *= sizePulse;

      // v2: 정착 파티클 색상 깜빡임 (일반→accent 전환)
      let color: string;
      if (isAccent) {
        color = p.accent;
      } else if (pp > 0.85 && Math.sin(t * 4 + i * 7) > 0.85) {
        color = p.accent;
      } else {
        color =
          p.particles[
            Math.floor(r3 * p.particles.length) % p.particles.length
          ];
      }

      // 파티클 본체
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fillStyle = hexToRGBA(color, alpha);
      ctx.fill();

      // 액센트 글로우 (v2: 강화)
      if (isAccent && settled) {
        const glowPulse = 0.5 + Math.sin(t * 3 + i) * 0.3;
        ctx.beginPath();
        ctx.arc(x, y, size * 8, 0, Math.PI * 2);
        ctx.fillStyle = hexToRGBA(p.glow, 0.06 * glowPulse);
        ctx.fill();

        accentPositions.push({ x, y });
      }
    }

    // 액센트 파티클 연결선 (v2: 더 일찍, 더 강하게)
    if (convergeProgress > 0.8) {
      const lineAlpha = 0.08 * ((convergeProgress - 0.8) / 0.2);
      ctx.strokeStyle = hexToRGBA(p.accent, lineAlpha);
      ctx.lineWidth = 0.7;
      for (let i = 0; i < accentPositions.length; i++) {
        for (let j = i + 1; j < accentPositions.length; j++) {
          const dx = accentPositions[i].x - accentPositions[j].x;
          const dy = accentPositions[i].y - accentPositions[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 90) {
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

    // ===== 태그라인 파티클 (v3) =====
    const taglineY = H - 580; // bottom: 580 → top 기준
    const taglineStartSec = 2.0;
    if (t > taglineStartSec) {
      const TAG_PARTICLE_COUNT = 180;
      const tagProgress = Math.min((t - taglineStartSec) / 1.5, 1);
      const tagEased = easeInOutQuart(tagProgress);

      for (let i = 0; i < TAG_PARTICLE_COUNT; i++) {
        const r1 = seededRandom(i + 50000);
        const r2 = seededRandom(i + 60000);
        const r3 = seededRandom(i + 70000);
        const r4 = seededRandom(i + 80000);

        // 초기: 태그라인 주변 흩어짐
        const spreadX = (r1 - 0.5) * 800;
        const spreadY = (r2 - 0.5) * 200;
        // 목표: 태그라인 텍스트 근처
        const targetX = W / 2 + (r1 - 0.5) * 500;
        const targetY = taglineY + (r2 - 0.5) * 30;

        const startX = targetX + spreadX;
        const startY = targetY + spreadY;
        const delay = r4 * 0.4;
        const pp = Math.max(0, Math.min(1, (tagEased - delay) / (1 - delay)));

        const px = startX + (targetX - startX) * pp;
        const py = startY + (targetY - startY) * pp;

        // 안착 후 호흡
        const bx = pp > 0.8 ? Math.sin(t * 1.5 + i * 3) * 2.0 : 0;
        const by = pp > 0.8 ? Math.cos(t * 1.1 + i * 2) * 1.5 : 0;

        const alpha = 0.15 + pp * 0.5;
        const size = 0.4 + r3 * 0.8;

        // 글로우 펄스
        const isGlow = r3 > 0.85;
        const color = isGlow ? p.accent : p.particles[Math.floor(r3 * p.particles.length) % p.particles.length];

        ctx.beginPath();
        ctx.arc(px + bx, py + by, size, 0, Math.PI * 2);
        ctx.fillStyle = hexToRGBA(color, alpha);
        ctx.fill();

        if (isGlow && pp > 0.7) {
          ctx.beginPath();
          ctx.arc(px + bx, py + by, size * 6, 0, Math.PI * 2);
          ctx.fillStyle = hexToRGBA(p.glow, 0.04);
          ctx.fill();
        }
      }
    }
  }, [frame, localFrame, t]);

  // 엔드카드 영역 밖이면 렌더링하지 않음
  if (localFrame < 0 || localFrame >= durationFrames) return null;

  // 전체 페이드인/아웃 (v2: 빠른 fade-in)
  const fadeIn = interpolate(localFrame, [0, fps * 0.1], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    localFrame,
    [durationFrames - fps * 0.8, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp" },
  );
  const opacity = fadeIn * fadeOut;

  // 태그라인 등장 (v3: 더 크고 밝게)
  const taglineOpacity = interpolate(
    localFrame,
    [fps * 2.0, fps * 2.8],
    [0, 0.85],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
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
      {/* 배경 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: W,
          height: H,
          backgroundColor: p.bg,
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

      {/* 태그라인 v3 — 글자별 스태거 + 밑줄 + 글로우 */}
      <div
        style={{
          position: "absolute",
          bottom: 580,
          left: 0,
          width: W,
          textAlign: "center",
          pointerEvents: "none",
        }}
      >
        {/* 글자별 스태거 애니메이션 */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          {tagline.split("").map((char, i) => {
            const charDelay = i * 2;
            const charLocalFrame = localFrame - fps * 2.0 - charDelay;
            const charOpacity = interpolate(
              charLocalFrame,
              [0, fps * 0.3],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            const charY = interpolate(
              charLocalFrame,
              [0, fps * 0.4],
              [12, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            const breathe =
              charLocalFrame > fps * 0.5
                ? 1 + Math.sin(localFrame * 0.06 + i * 0.4) * 0.03
                : 1;

            return (
              <span
                key={i}
                style={{
                  fontFamily: "Pretendard Variable, sans-serif",
                  fontSize: 48,
                  fontWeight: 700,
                  letterSpacing: "0.25em",
                  color: p.accent,
                  opacity: charOpacity * taglineOpacity,
                  transform: `translateY(${charY}px) scale(${breathe})`,
                  display: "inline-block",
                  textShadow: `0 0 20px ${p.glow}60, 0 0 40px ${p.glow}30`,
                }}
              >
                {char === " " ? "\u00A0" : char}
              </span>
            );
          })}
        </div>

        {/* 애니메이션 밑줄 */}
        <svg
          width={600}
          height={4}
          style={{ margin: "16px auto 0", display: "block" }}
        >
          <line
            x1={0}
            y1={2}
            x2={600}
            y2={2}
            stroke={p.accent}
            strokeWidth={2}
            strokeDasharray={600}
            strokeDashoffset={interpolate(
              localFrame - fps * 2.5,
              [0, fps * 1.0],
              [600, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            )}
            opacity={taglineOpacity * 0.7}
          />
        </svg>
      </div>
    </div>
  );
};
