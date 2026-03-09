import React from "react";
import { useCurrentFrame } from "remotion";
import { AudioFrame } from "../../hooks/useAudioData";

// 결정론적 해시 기반 랜덤
function seededRand(seed: number): number {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}

interface PostProcessProps {
  audio: AudioFrame;
  width: number;
  height: number;
}

/**
 * 포스트프로세싱 오버레이 레이어 — 백남준 미학
 * - 비네트 (항상)
 * - CRT 스캔라인 (강화)
 * - onset 플래시 (베이스 히트)
 * - 크로마틱 에버레이션 (high 반응, 강화)
 * - CRT 수평 티어링 (onset 시)
 * - 노이즈 그레인 (항상)
 * - 인터레이스 플리커
 * - RMS 글로우
 */
export const PostProcess: React.FC<PostProcessProps> = ({
  audio,
  width,
  height,
}) => {
  const frame = useCurrentFrame();

  // onset 플래시 강도 (강화: 0.25→0.3, 0.35→0.4)
  const flashOpacity = audio.onset ? 0.3 + audio.rms * 0.4 : 0;

  // rms 기반 글로우 강도
  const glowOpacity = 0.05 + audio.rms * 0.2;

  // bass 기반 비네트 강도 변화
  const vignetteIntensity = 0.55 + audio.bass * 0.3;

  // CRT 티어링 스트립: onset 시 수평 줄이 어긋남
  const tearStrips = audio.onset
    ? Array.from({ length: 5 }, (_, i) => ({
        y: seededRand(frame * 17 + i * 73) * height,
        h: 2 + seededRand(frame * 31 + i * 53) * 8,
        shiftX: (seededRand(frame * 7 + i * 41) - 0.5) * 60,
        opacity: 0.06 + audio.rms * 0.14,
      }))
    : [];

  // 노이즈 그레인 시드 (매 2프레임마다 갱신 — 필름 그레인 감성)
  const noiseSeed = Math.floor(frame / 2);

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width,
        height,
        zIndex: 10,
        pointerEvents: "none",
      }}
    >
      {/* 비네트 — 항상 적용, 가장자리를 어둡게 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          background: `radial-gradient(
            ellipse 70% 70% at 50% 50%,
            transparent 40%,
            rgba(0, 0, 0, ${vignetteIntensity}) 100%
          )`,
          pointerEvents: "none",
        }}
      />

      {/* CRT 스캔라인 — 강화: 3px 주기, 높은 opacity, rms 반응 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.12) 2px, rgba(0,0,0,0.12) 3px)",
          pointerEvents: "none",
          opacity: 0.75 + audio.rms * 0.15,
        }}
      />

      {/* onset 플래시 — 베이스 히트 시 흰색 플래시 */}
      {flashOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width,
            height,
            backgroundColor: `rgba(255, 255, 255, ${flashOpacity})`,
            pointerEvents: "none",
          }}
        />
      )}

      {/* CRT 수평 티어링 — onset 시 가로 줄이 어긋남 (백남준 스타일) */}
      {tearStrips.map((strip, i) => (
        <div
          key={`tear-${i}`}
          style={{
            position: "absolute",
            top: strip.y,
            left: strip.shiftX,
            width: width + Math.abs(strip.shiftX),
            height: strip.h,
            backgroundColor: `rgba(255, 255, 255, ${strip.opacity})`,
            mixBlendMode: "screen",
            pointerEvents: "none",
          }}
        />
      ))}

      {/* 노이즈 그레인 — 항상 적용, SVG feTurbulence 기반 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' seed='${noiseSeed}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E")`,
          backgroundSize: "256px 256px",
          opacity: 0.3 + audio.rms * 0.2,
          mixBlendMode: "overlay",
          pointerEvents: "none",
        }}
      />

      {/* 오디오 리액티브 글로우 — rms 기반 밝은 오버레이 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          background: `radial-gradient(
            ellipse 50% 50% at 50% 50%,
            rgba(255, 215, 0, ${glowOpacity}) 0%,
            transparent 70%
          )`,
          pointerEvents: "none",
          mixBlendMode: "screen",
        }}
      />

      {/* 크로마틱 에버레이션 — 강화: 12px+, 높은 opacity, 넓은 범위 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: 12 + audio.high * 8,
          height,
          background: `linear-gradient(180deg,
            transparent 0%,
            rgba(255, 0, 0, ${0.08 + audio.high * 0.18}) 20%,
            rgba(255, 0, 0, ${0.06 + audio.high * 0.12}) 80%,
            transparent 100%
          )`,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: 12 + audio.high * 8,
          height,
          background: `linear-gradient(180deg,
            transparent 0%,
            rgba(0, 100, 255, ${0.08 + audio.high * 0.18}) 20%,
            rgba(0, 100, 255, ${0.06 + audio.high * 0.12}) 80%,
            transparent 100%
          )`,
          pointerEvents: "none",
        }}
      />

      {/* 인터레이스 플리커 — 3프레임마다 미세 어두움 */}
      {frame % 3 === 0 && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width,
            height,
            backgroundColor: "rgba(0, 0, 0, 0.03)",
            pointerEvents: "none",
          }}
        />
      )}
    </div>
  );
};
