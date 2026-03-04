import React from "react";
import { interpolate, spring } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * TextReveal — 타이포그래피 모션그래픽
 *
 * 대본의 핵심 단어/구절/문장을 비주얼 영역에 글자 단위로 등장시킨다.
 * 모드: typewriter | wave | glitch | scatter
 *
 * params:
 *   text: string           — 표시할 텍스트 (단어, 구절, 짧은 문장)
 *   mode: string            — typewriter | wave | glitch | scatter (기본: typewriter)
 *   fontSize: number        — 폰트 크기 (기본: 64)
 *   color: string           — 텍스트 색상 (기본: #FFFFFF)
 *   position: string        — center | top | upper | bottom (기본: center). 자막 영역(y≥1230 전체 캔버스) 침범 금지
 *   staggerMs: number       — 글자 간 딜레이 ms (기본: 80)
 *   glowColor: string       — 글로우 색상 (기본: #8B5CF6)
 */

// 결정론적 해시 기반 랜덤 (프레임 렌더링에 안전)
function seededRand(seed: number): number {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}

export const TextReveal: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const text: string = params.text || "ENOMETA";
  const mode: string = params.mode || "typewriter";
  const fontSize: number = params.fontSize || 64;
  const color: string = params.color || "#FFFFFF";
  const position: string = params.position || "center";
  const staggerMs: number = params.staggerMs || 80;
  const glowColor: string = params.glowColor || params.color || "#8B5CF6";

  const chars = text.split("");
  const staggerFrames = (staggerMs / 1000) * fps;

  const posY =
    position === "top" ? height * 0.15 :
    position === "upper" ? height * 0.32 :
    position === "bottom" ? height * 0.72 :  // 자막 영역(y≥1230) 상단, 비주얼 하단 배치
    height * 0.48;  // center

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width,
        height,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: posY,
          left: 0,
          width,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flexWrap: "wrap",
          padding: "0 60px",
          gap: fontSize < 48 ? "2px" : "0px",
        }}
      >
        {chars.map((char, i) => {
          const charDelay = i * staggerFrames;
          const localFrame = frame - charDelay;

          if (mode === "typewriter") {
            const opacity = interpolate(localFrame, [0, 3], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const scale = interpolate(localFrame, [0, 5], [1.3, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const isLast = i === chars.length - 1;
            const cursorOpacity =
              isLast && localFrame > 0 && localFrame < fps * 2
                ? Math.sin(frame * 0.3) > 0 ? 1 : 0
                : 0;

            // 오디오 리액티브 글로우 + 색상 펄스
            const glowSize = 8 + audio.rms * 25;
            const colorPulse = audio.rms > 0.3 ? glowColor : color;

            return (
              <span key={i} style={{ position: "relative", display: "inline-block" }}>
                <span
                  style={{
                    fontFamily: "Pretendard Variable, sans-serif",
                    fontSize,
                    fontWeight: 800,
                    color: colorPulse,
                    opacity,
                    transform: `scale(${scale})`,
                    display: "inline-block",
                    textShadow: opacity > 0.5
                      ? `0 0 ${glowSize}px ${glowColor}, 0 0 ${glowSize * 2}px ${glowColor}40`
                      : "none",
                  }}
                >
                  {char === " " ? "\u00A0" : char}
                </span>
                {cursorOpacity > 0 && (
                  <span
                    style={{
                      position: "absolute",
                      right: -2,
                      top: "10%",
                      width: 3,
                      height: "80%",
                      backgroundColor: glowColor,
                      opacity: cursorOpacity,
                      boxShadow: `0 0 8px ${glowColor}`,
                    }}
                  />
                )}
              </span>
            );
          }

          if (mode === "wave") {
            const opacity = interpolate(localFrame, [0, 5], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            // 강화된 웨이브: 더 큰 진폭 + 스케일 펄스
            const waveY =
              Math.sin((frame * 0.1) + i * 0.6) * (20 + audio.bass * 40);
            const waveRotate =
              Math.sin((frame * 0.07) + i * 0.8) * 5;
            const waveScale = 1 + Math.sin((frame * 0.05) + i * 0.4) * 0.1;
            const glowSize = 12 + audio.rms * 50;

            return (
              <span
                key={i}
                style={{
                  fontFamily: "Pretendard Variable, sans-serif",
                  fontSize,
                  fontWeight: 800,
                  color,
                  opacity,
                  transform: `translateY(${waveY}px) rotate(${waveRotate}deg) scale(${waveScale})`,
                  display: "inline-block",
                  textShadow: `0 0 ${glowSize}px ${glowColor}, 0 0 ${glowSize * 1.5}px ${glowColor}60`,
                }}
              >
                {char === " " ? "\u00A0" : char}
              </span>
            );
          }

          if (mode === "glitch") {
            const opacity = interpolate(localFrame, [0, 2], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            // 결정론적 글리치: frame 기반 시드로 렌더링 안전
            const glitchSeed = frame * 137 + i * 31;
            const glitchIntensity = audio.onset ? 0.8 : (audio.rms > 0.2 ? 0.3 : 0);
            const isGlitching = seededRand(glitchSeed) < glitchIntensity;
            const glitchX = isGlitching ? (seededRand(glitchSeed + 1) - 0.5) * 16 : 0;
            const glitchY = isGlitching ? (seededRand(glitchSeed + 2) - 0.5) * 12 : 0;
            const glitchColors = ["#FF0040", "#00FF80", "#4080FF", "#FFD700", "#00FFFF"];
            const glitchColor2 = isGlitching
              ? glitchColors[Math.floor(seededRand(glitchSeed + 3) * glitchColors.length)]
              : color;
            // 스케일 글리치
            const glitchScale = isGlitching ? 1 + (seededRand(glitchSeed + 4) - 0.5) * 0.3 : 1;

            return (
              <span
                key={i}
                style={{
                  fontFamily: "'Courier New', monospace",
                  fontSize,
                  fontWeight: 700,
                  color: glitchColor2,
                  opacity,
                  transform: `translate(${glitchX}px, ${glitchY}px) scale(${glitchScale})`,
                  display: "inline-block",
                  textShadow: isGlitching
                    ? `${glitchX * 2}px 0 #FF0040, ${-glitchX * 2}px 0 #00FF80, 0 0 15px ${glowColor}`
                    : `0 0 ${6 + audio.rms * 20}px ${glowColor}`,
                }}
              >
                {char === " " ? "\u00A0" : char}
              </span>
            );
          }

          if (mode === "scatter") {
            const seed = i * 137.5;
            const scatterX = Math.sin(seed) * width * 0.4;
            const scatterY = Math.cos(seed * 0.7) * height * 0.4;
            const progress = interpolate(
              localFrame,
              [0, fps * 0.8],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            const eased = 1 - Math.pow(1 - progress, 3);
            const x = scatterX * (1 - eased);
            const y = scatterY * (1 - eased);
            const rotation = (1 - eased) * (Math.sin(seed) * 360);
            const opacity = interpolate(progress, [0, 0.3], [0, 1], {
              extrapolateRight: "clamp",
            });
            // 수렴 후 호흡 효과
            const breathe = eased > 0.9
              ? 1 + Math.sin(frame * 0.08 + i * 0.5) * 0.05
              : 1;
            const glowSize = eased > 0.8 ? 12 + audio.rms * 35 : 0;

            return (
              <span
                key={i}
                style={{
                  fontFamily: "Pretendard Variable, sans-serif",
                  fontSize,
                  fontWeight: 900,
                  color,
                  opacity,
                  transform: `translate(${x}px, ${y}px) rotate(${rotation}deg) scale(${breathe})`,
                  display: "inline-block",
                  textShadow:
                    glowSize > 0
                      ? `0 0 ${glowSize}px ${glowColor}, 0 0 ${glowSize * 2}px ${glowColor}40`
                      : "none",
                }}
              >
                {char === " " ? "\u00A0" : char}
              </span>
            );
          }

          // fallback
          return (
            <span key={i} style={{ fontSize, color }}>
              {char}
            </span>
          );
        })}
      </div>
    </div>
  );
};
