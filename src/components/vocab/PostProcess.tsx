import React from "react";
import { AudioFrame } from "../../hooks/useAudioData";

interface PostProcessProps {
  audio: AudioFrame;
  width: number;
  height: number;
}

/**
 * 포스트프로세싱 오버레이 레이어
 * - 비네트 (항상)
 * - 스캔라인 (미세)
 * - onset 플래시 (베이스 히트)
 * - 크로마틱 에버레이션 효과 (rms 기반)
 */
export const PostProcess: React.FC<PostProcessProps> = ({
  audio,
  width,
  height,
}) => {
  // onset 플래시 강도
  const flashOpacity = audio.onset ? 0.15 + audio.rms * 0.2 : 0;

  // rms 기반 글로우 강도
  const glowOpacity = 0.03 + audio.rms * 0.08;

  // bass 기반 비네트 강도 변화
  const vignetteIntensity = 0.55 + audio.bass * 0.15;

  return (
    <>
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

      {/* 스캔라인 — 미세한 수평 라인 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,0,0,0.04) 3px, rgba(0,0,0,0.04) 4px)",
          pointerEvents: "none",
          opacity: 0.6,
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

      {/* 크로마틱 에버레이션 힌트 — 좌우 미세 컬러 쉬프트 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: 3,
          height,
          background: `linear-gradient(180deg,
            transparent 0%,
            rgba(255, 0, 0, ${0.03 + audio.high * 0.05}) 30%,
            rgba(255, 0, 0, ${0.02 + audio.high * 0.03}) 70%,
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
          width: 3,
          height,
          background: `linear-gradient(180deg,
            transparent 0%,
            rgba(0, 100, 255, ${0.03 + audio.high * 0.05}) 30%,
            rgba(0, 100, 255, ${0.02 + audio.high * 0.03}) 70%,
            transparent 100%
          )`,
          pointerEvents: "none",
        }}
      />
    </>
  );
};
