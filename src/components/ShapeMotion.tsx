import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { Scene } from "../types";

interface ShapeMotionProps {
  scenes: Scene[];
}

/**
 * 비주얼 영역(y=370~1450) 내 배치를 위한 top 값.
 * ShapeMotion은 EnometaShorts의 1080×1920 컨테이너에 absolute로 배치됨.
 * 비주얼 영역 중앙~하단에 위치하도록 top: 850~1150 범위 사용.
 */

// 패턴: tension — 사각형 테두리 (지속 회전 + 크기 맥동)
const TensionShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterSpring = spring({ frame, fps, config: { damping: 20, stiffness: 200 } });
  const enterScale = interpolate(enterSpring, [0, 1], [0.3, 1]);

  // 지속 회전 (멈추지 않음)
  const rotate = (frame / fps) * 45; // 초당 45도
  // 크기 맥동 (sine wave)
  const pulse = 1 + Math.sin((frame / fps) * 3) * 0.08;
  // 페이드인
  const opacity = interpolate(frame, [0, 12], [0, 0.6], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 950,
        left: "50%",
        width: 200,
        height: 200,
        marginLeft: -100,
        border: "2px solid rgba(255, 68, 0, 0.7)",
        borderRadius: 4,
        transform: `scale(${enterScale * pulse}) rotate(${rotate}deg)`,
        opacity,
        pointerEvents: "none",
      }}
    />
  );
};

// 패턴: climax — 동심원 확산 (2개 원, 위상차 펄스)
const ClimaxShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const t = frame / fps;

  // 원 1: 확산하며 페이드아웃 반복
  const cycle1 = (t * 0.8) % 1; // 1.25초 주기
  const scale1 = interpolate(cycle1, [0, 1], [0.6, 1.8]);
  const opacity1 = interpolate(cycle1, [0, 0.3, 1], [0.7, 0.5, 0]);

  // 원 2: 위상 0.5 차이
  const cycle2 = ((t * 0.8) + 0.5) % 1;
  const scale2 = interpolate(cycle2, [0, 1], [0.6, 1.8]);
  const opacity2 = interpolate(cycle2, [0, 0.3, 1], [0.7, 0.5, 0]);

  const baseStyle: React.CSSProperties = {
    position: "absolute",
    top: 880,
    left: "50%",
    width: 160,
    height: 160,
    marginLeft: -80,
    border: "1.5px solid rgba(0, 255, 255, 0.8)",
    borderRadius: "50%",
    pointerEvents: "none",
  };

  return (
    <>
      <div style={{ ...baseStyle, transform: `scale(${scale1})`, opacity: opacity1 * fadeIn }} />
      <div style={{ ...baseStyle, transform: `scale(${scale2})`, opacity: opacity2 * fadeIn }} />
    </>
  );
};

// 패턴: awakening — 수평 스캔라인 (좌→우 반복 슬라이드)
const AwakeningShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const t = frame / fps;

  // 선 1: 2초 주기로 좌→우 스캔
  const scanProgress1 = (t * 0.5) % 1; // 2초 주기
  const translateX1 = interpolate(scanProgress1, [0, 1], [-540, 540]);
  const lineOpacity1 = interpolate(scanProgress1, [0, 0.1, 0.9, 1], [0, 0.8, 0.8, 0]);

  // 선 2: 위상 차이 + 다른 속도
  const scanProgress2 = (t * 0.35 + 0.4) % 1; // 2.85초 주기
  const translateX2 = interpolate(scanProgress2, [0, 1], [-540, 540]);
  const lineOpacity2 = interpolate(scanProgress2, [0, 0.1, 0.9, 1], [0, 0.5, 0.5, 0]);

  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 1020,
          left: "50%",
          width: 320,
          height: 2,
          marginLeft: -160,
          backgroundColor: "rgba(255, 215, 0, 0.85)",
          transform: `translateX(${translateX1}px)`,
          opacity: lineOpacity1 * fadeIn,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 1035,
          left: "50%",
          width: 200,
          height: 1.5,
          marginLeft: -100,
          backgroundColor: "rgba(255, 215, 0, 0.5)",
          transform: `translateX(${translateX2}px)`,
          opacity: lineOpacity2 * fadeIn,
          pointerEvents: "none",
        }}
      />
    </>
  );
};

// 패턴: intro — 점 3개 부유 (sine wave Y offset + stagger)
const IntroShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const STAGGER = 6;

  return (
    <div
      style={{
        position: "absolute",
        top: 1050,
        left: "50%",
        display: "flex",
        gap: 14,
        marginLeft: -30,
        pointerEvents: "none",
      }}
    >
      {[0, 1, 2].map((i) => {
        const delayedFrame = Math.max(0, frame - i * STAGGER);
        const opacity = interpolate(delayedFrame, [0, 10], [0, 0.65], {
          extrapolateRight: "clamp",
        });
        // 각 점이 다른 위상으로 부유
        const floatY = Math.sin(t * 2 + i * 2.1) * 12;
        const floatX = Math.cos(t * 1.5 + i * 1.7) * 5;

        return (
          <div
            key={i}
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: "rgba(204, 204, 204, 0.9)",
              opacity,
              transform: `translate(${floatX}px, ${floatY}px)`,
            }}
          />
        );
      })}
    </div>
  );
};

// 패턴: buildup — 삼각형 펄스 (점멸 + 스케일)
const BuildupShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  // 빠른 점멸
  const flash = interpolate(frame % 8, [0, 2, 4, 6, 8], [1, 0.3, 1, 0.4, 1]);
  const scale = 0.9 + Math.sin(t * 5) * 0.15;

  return (
    <div
      style={{
        position: "absolute",
        top: 960,
        left: "50%",
        marginLeft: -60,
        width: 0,
        height: 0,
        borderLeft: "60px solid transparent",
        borderRight: "60px solid transparent",
        borderBottom: "104px solid rgba(255, 179, 71, 0.6)",
        transform: `scale(${scale})`,
        opacity: flash * fadeIn * 0.7,
        pointerEvents: "none",
      }}
    />
  );
};

export const ShapeMotion: React.FC<ShapeMotionProps> = ({ scenes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentSec = frame / fps;
  const activeScene = scenes.find(
    (s) => currentSec >= s.start_sec && currentSec < s.end_sec,
  );
  const emotion = activeScene?.emotion ?? "";

  if (emotion.includes("tension")) return <TensionShape />;
  if (emotion.includes("climax")) return <ClimaxShape />;
  if (emotion.includes("awakening")) return <AwakeningShape />;
  if (emotion.includes("buildup")) return <BuildupShape />;
  if (emotion.includes("intro")) return <IntroShape />;

  return null;
};
