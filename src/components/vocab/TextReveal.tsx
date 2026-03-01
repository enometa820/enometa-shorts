import React from "react";
import { interpolate, spring } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * TextReveal — 타이포그래피 애니메이션
 *
 * 대본의 핵심 문구를 화면에 글자 단위로 등장시킨다.
 * 모드: typewriter | wave | glitch | scatter
 *
 * params:
 *   text: string           — 표시할 텍스트
 *   mode: string            — typewriter | wave | glitch | scatter (기본: typewriter)
 *   fontSize: number        — 폰트 크기 (기본: 64)
 *   color: string           — 텍스트 색상 (기본: #FFFFFF)
 *   position: string        — center | top | bottom (기본: center)
 *   staggerMs: number       — 글자 간 딜레이 ms (기본: 80)
 */
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
    position === "top" ? height * 0.2 :
    position === "bottom" ? height * 0.75 :
    height * 0.48;

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
            // 커서 깜빡임 (마지막 글자에만)
            const isLast = i === chars.length - 1;
            const cursorOpacity =
              isLast && localFrame > 0 && localFrame < fps * 2
                ? Math.sin(frame * 0.3) > 0 ? 1 : 0
                : 0;

            return (
              <span key={i} style={{ position: "relative", display: "inline-block" }}>
                <span
                  style={{
                    fontFamily: "Pretendard Variable, sans-serif",
                    fontSize,
                    fontWeight: 800,
                    color,
                    opacity,
                    transform: `scale(${scale})`,
                    display: "inline-block",
                    textShadow: opacity > 0.5
                      ? `0 0 ${8 + audio.rms * 20}px ${glowColor}`
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
                      backgroundColor: color,
                      opacity: cursorOpacity,
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
            // 웨이브: 각 글자가 위아래로 물결
            const waveY =
              Math.sin((frame * 0.08) + i * 0.5) * (12 + audio.bass * 15);
            const waveRotate =
              Math.sin((frame * 0.06) + i * 0.7) * 3;

            return (
              <span
                key={i}
                style={{
                  fontFamily: "Pretendard Variable, sans-serif",
                  fontSize,
                  fontWeight: 800,
                  color,
                  opacity,
                  transform: `translateY(${waveY}px) rotate(${waveRotate}deg)`,
                  display: "inline-block",
                  textShadow: `0 0 ${6 + audio.rms * 25}px ${glowColor}`,
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
            // 글리치: onset에 반응해서 위치/색상 떨림
            const isGlitching = audio.onset && Math.random() < 0.4;
            const glitchX = isGlitching ? (Math.random() - 0.5) * 10 : 0;
            const glitchY = isGlitching ? (Math.random() - 0.5) * 8 : 0;
            const glitchColor = isGlitching
              ? ["#FF0040", "#00FF80", "#4080FF"][Math.floor(Math.random() * 3)]
              : color;

            return (
              <span
                key={i}
                style={{
                  fontFamily: "'Courier New', monospace",
                  fontSize,
                  fontWeight: 700,
                  color: glitchColor,
                  opacity,
                  transform: `translate(${glitchX}px, ${glitchY}px)`,
                  display: "inline-block",
                  textShadow: isGlitching
                    ? `${glitchX * 2}px 0 #FF0040, ${-glitchX * 2}px 0 #00FF80`
                    : `0 0 ${4 + audio.rms * 15}px ${glowColor}`,
                }}
              >
                {char === " " ? "\u00A0" : char}
              </span>
            );
          }

          if (mode === "scatter") {
            // 흩어져있다가 모이는 효과
            const seed = i * 137.5;
            const scatterX = Math.sin(seed) * width * 0.4;
            const scatterY = Math.cos(seed * 0.7) * height * 0.4;
            const progress = interpolate(
              localFrame,
              [0, fps * 0.8],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            );
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            const x = scatterX * (1 - eased);
            const y = scatterY * (1 - eased);
            const rotation = (1 - eased) * (Math.sin(seed) * 360);
            const opacity = interpolate(progress, [0, 0.3], [0, 1], {
              extrapolateRight: "clamp",
            });

            return (
              <span
                key={i}
                style={{
                  fontFamily: "Pretendard Variable, sans-serif",
                  fontSize,
                  fontWeight: 900,
                  color,
                  opacity,
                  transform: `translate(${x}px, ${y}px) rotate(${rotation}deg)`,
                  display: "inline-block",
                  textShadow:
                    eased > 0.8
                      ? `0 0 ${10 + audio.rms * 30}px ${glowColor}`
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
