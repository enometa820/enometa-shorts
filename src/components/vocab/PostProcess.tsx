import React from "react";
import { useCurrentFrame } from "remotion";
import { AudioFrame } from "../../hooks/useAudioData";

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
 * PostProcess v2 — 강화된 CRT/글리치 효과
 *
 * 개선 사항:
 * - 전체화면 RGB 채널 분리 (좌우 스트립 → 전체 오버레이 x오프셋)
 * - 2중 스캔라인 (기본 + 고주파 인터페런스)
 * - 강화된 글리치 바 (onset 시 넓고 불투명하게)
 * - 데이터 블록 부패 (high SI 시 직사각형 글리치 블록)
 * - CRT 포스포 잔광 (persistence — 이전 프레임 에코)
 * - SVG 변위 맵 노이즈 (더 큰/더 불투명)
 */
export const PostProcess: React.FC<PostProcessProps> = ({
  audio,
  width,
  height,
}) => {
  const frame = useCurrentFrame();

  // 핵심 오디오 강도값
  const onsetStrength = audio.onset ? 1.0 : 0;
  const bassEnergy = audio.bass;
  const rmsEnergy = audio.rms;
  const highEnergy = audio.high;

  // ── 비네트 ──────────────────────────────────────────────────
  const vignetteIntensity = 0.60 + bassEnergy * 0.35;

  // ── onset 플래시 ─────────────────────────────────────────────
  const flashOpacity = onsetStrength * (0.28 + rmsEnergy * 0.35);

  // ── RGB 채널 분리 (전체화면) ─────────────────────────────────
  // 채널별 X 오프셋: bass가 높을수록 더 벌어짐
  const rgbShift = 3 + bassEnergy * 12 + onsetStrength * 20;
  const rgbOpacity = 0.07 + highEnergy * 0.12 + onsetStrength * 0.15;

  // ── 글리치 바: onset 시 넓고 강렬하게 ─────────────────────────
  const glitchBars = audio.onset
    ? Array.from({ length: 8 }, (_, i) => {
        const r = seededRand(frame * 23 + i * 89);
        const r2 = seededRand(frame * 37 + i * 61);
        const r3 = seededRand(frame * 11 + i * 43);
        const isColor = r3 > 0.6;
        return {
          y: r * height,
          h: 3 + r2 * 18,
          shiftX: (seededRand(frame * 7 + i * 41) - 0.5) * 80,
          opacity: 0.12 + rmsEnergy * 0.25,
          color: isColor
            ? `rgba(${Math.floor(r * 255)}, 0, 255, ${0.08 + rmsEnergy * 0.15})`
            : `rgba(255, 255, 255, ${0.10 + rmsEnergy * 0.20})`,
        };
      })
    : [];

  // ── 데이터 블록 부패 (high+onset 시) ──────────────────────────
  const corruptBlocks =
    audio.onset && highEnergy > 0.5
      ? Array.from({ length: 3 }, (_, i) => ({
          x: seededRand(frame * 19 + i * 67) * width * 0.8,
          y: seededRand(frame * 29 + i * 53) * height,
          w: 30 + seededRand(frame * 41 + i * 31) * 120,
          h: 4 + seededRand(frame * 13 + i * 79) * 20,
          hue: Math.floor(seededRand(frame * 7 + i) * 360),
          opacity: 0.15 + highEnergy * 0.25,
        }))
      : [];

  // ── 노이즈 그레인 ─────────────────────────────────────────────
  const noiseSeed = Math.floor(frame / 2);
  const noiseOpacity = 0.40 + rmsEnergy * 0.25;
  const noiseFreq = 0.70 + bassEnergy * 0.20;

  // ── RMS 글로우 ─────────────────────────────────────────────────
  const glowOpacity = 0.04 + rmsEnergy * 0.18;

  // ── 인터레이스 플리커 ─────────────────────────────────────────
  const flicker = frame % 4 === 0 ? 0.04 : frame % 7 === 0 ? 0.025 : 0;

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
        overflow: "hidden",
      }}
    >
      {/* 1. 비네트 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse 72% 72% at 50% 50%, transparent 38%, rgba(0,0,0,${vignetteIntensity}) 100%)`,
        }}
      />

      {/* 2. CRT 스캔라인 — 기본 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.14) 2px, rgba(0,0,0,0.14) 3px)",
          opacity: 0.80 + rmsEnergy * 0.12,
        }}
      />

      {/* 3. 고주파 스캔라인 인터페런스 (7px 주기) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 5px, rgba(0,0,0,0.04) 5px, rgba(0,0,0,0.04) 7px)",
          opacity: 0.6,
        }}
      />

      {/* 4. RGB 채널 분리 — Red (좌 오프셋) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: -rgbShift,
          width,
          height,
          backgroundColor: `rgba(255, 0, 0, ${rgbOpacity})`,
          mixBlendMode: "screen",
        }}
      />

      {/* 4. RGB 채널 분리 — Blue (우 오프셋) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: rgbShift,
          width,
          height,
          backgroundColor: `rgba(0, 80, 255, ${rgbOpacity})`,
          mixBlendMode: "screen",
        }}
      />

      {/* 4. RGB 채널 분리 — Green (상 오프셋) */}
      <div
        style={{
          position: "absolute",
          top: -Math.floor(rgbShift * 0.3),
          left: 0,
          width,
          height,
          backgroundColor: `rgba(0, 255, 80, ${rgbOpacity * 0.5})`,
          mixBlendMode: "screen",
        }}
      />

      {/* 5. onset 플래시 */}
      {flashOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: `rgba(255, 255, 255, ${flashOpacity})`,
          }}
        />
      )}

      {/* 6. CRT 글리치 바 */}
      {glitchBars.map((bar, i) => (
        <div
          key={`gb-${i}`}
          style={{
            position: "absolute",
            top: bar.y,
            left: bar.shiftX,
            width: width + Math.abs(bar.shiftX),
            height: bar.h,
            backgroundColor: bar.color,
            mixBlendMode: "screen",
          }}
        />
      ))}

      {/* 7. 데이터 블록 부패 */}
      {corruptBlocks.map((block, i) => (
        <div
          key={`cb-${i}`}
          style={{
            position: "absolute",
            top: block.y,
            left: block.x,
            width: block.w,
            height: block.h,
            backgroundColor: `hsla(${block.hue}, 100%, 60%, ${block.opacity})`,
            mixBlendMode: "exclusion",
          }}
        />
      ))}

      {/* 8. 노이즈 그레인 (SVG feTurbulence) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='${noiseFreq.toFixed(2)}' numOctaves='4' seed='${noiseSeed}' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E")`,
          backgroundSize: "256px 256px",
          opacity: noiseOpacity,
          mixBlendMode: "overlay",
        }}
      />

      {/* 9. RMS 글로우 — 중앙 에너지 펄스 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse 55% 55% at 50% 50%, rgba(255,200,80,${glowOpacity}) 0%, transparent 70%)`,
          mixBlendMode: "screen",
        }}
      />

      {/* 10. 인터레이스 플리커 */}
      {flicker > 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: `rgba(0, 0, 0, ${flicker})`,
          }}
        />
      )}

      {/* 11. 수평 포스포 잔광 — bass 히트 후 수평 브라이트 라인 */}
      {bassEnergy > 0.6 && (
        <div
          style={{
            position: "absolute",
            top: height * (0.3 + seededRand(frame * 3) * 0.4),
            left: 0,
            width,
            height: 1 + bassEnergy * 2,
            backgroundColor: `rgba(255, 255, 200, ${0.04 + bassEnergy * 0.08})`,
            mixBlendMode: "screen",
          }}
        />
      )}
    </div>
  );
};
