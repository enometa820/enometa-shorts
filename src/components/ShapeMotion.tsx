import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { Scene, ShapeParams } from "../types";

interface ShapeMotionProps {
  scenes: Scene[];
}

interface ShapeBaseProps {
  speed: number;
  scale: number;
  count: number;
}

/**
 * 비주얼 영역(y=370~1450) 내 배치를 위한 top 값.
 * ShapeMotion은 EnometaShorts의 1080×1920 컨테이너에 absolute로 배치됨.
 * 비주얼 영역 중앙~하단에 위치하도록 top: 850~1150 범위 사용.
 */

// 패턴: tension — 사각형 테두리 (지속 회전 + 크기 맥동)
const TensionShape: React.FC<ShapeBaseProps> = ({ speed, scale }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterSpring = spring({ frame, fps, config: { damping: 20, stiffness: 200 } });
  const enterScale = interpolate(enterSpring, [0, 1], [0.3, 1]);

  const rotate = (frame / fps) * 45 * speed;
  const pulse = 1 + Math.sin((frame / fps) * 3 * speed) * 0.08;
  const opacity = interpolate(frame, [0, 12], [0, 0.6], {
    extrapolateRight: "clamp",
  });
  const size = 200 * scale;

  return (
    <div
      style={{
        position: "absolute",
        top: 950,
        left: "50%",
        width: size,
        height: size,
        marginLeft: -size / 2,
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
const ClimaxShape: React.FC<ShapeBaseProps> = ({ speed, scale }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const t = frame / fps;

  const cycle1 = (t * 0.8 * speed) % 1;
  const scale1 = interpolate(cycle1, [0, 1], [0.6, 1.8]);
  const opacity1 = interpolate(cycle1, [0, 0.3, 1], [0.7, 0.5, 0]);

  const cycle2 = ((t * 0.8 * speed) + 0.5) % 1;
  const scale2 = interpolate(cycle2, [0, 1], [0.6, 1.8]);
  const opacity2 = interpolate(cycle2, [0, 0.3, 1], [0.7, 0.5, 0]);

  const size = 160 * scale;
  const baseStyle: React.CSSProperties = {
    position: "absolute",
    top: 880,
    left: "50%",
    width: size,
    height: size,
    marginLeft: -size / 2,
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
const AwakeningShape: React.FC<ShapeBaseProps> = ({ speed, scale }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });
  const t = frame / fps;

  const scanProgress1 = (t * 0.5 * speed) % 1;
  const translateX1 = interpolate(scanProgress1, [0, 1], [-540, 540]);
  const lineOpacity1 = interpolate(scanProgress1, [0, 0.1, 0.9, 1], [0, 0.8, 0.8, 0]);

  const scanProgress2 = (t * 0.35 * speed + 0.4) % 1;
  const translateX2 = interpolate(scanProgress2, [0, 1], [-540, 540]);
  const lineOpacity2 = interpolate(scanProgress2, [0, 0.1, 0.9, 1], [0, 0.5, 0.5, 0]);

  const width1 = 320 * scale;
  const width2 = 200 * scale;

  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 1020,
          left: "50%",
          width: width1,
          height: 2,
          marginLeft: -width1 / 2,
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
          width: width2,
          height: 1.5,
          marginLeft: -width2 / 2,
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
const IntroShape: React.FC<ShapeBaseProps> = ({ speed, scale, count }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const STAGGER = 6;
  const dotCount = Math.max(2, Math.min(6, Math.round(3 * count)));
  const dotSize = 8 * scale;

  return (
    <div
      style={{
        position: "absolute",
        top: 1050,
        left: "50%",
        display: "flex",
        gap: 14,
        marginLeft: -(dotCount * (dotSize + 14)) / 2,
        pointerEvents: "none",
      }}
    >
      {Array.from({ length: dotCount }, (_, i) => {
        const delayedFrame = Math.max(0, frame - i * STAGGER);
        const opacity = interpolate(delayedFrame, [0, 10], [0, 0.65], {
          extrapolateRight: "clamp",
        });
        const floatY = Math.sin(t * 2 * speed + i * 2.1) * 12;
        const floatX = Math.cos(t * 1.5 * speed + i * 1.7) * 5;

        return (
          <div
            key={i}
            style={{
              width: dotSize,
              height: dotSize,
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
const BuildupShape: React.FC<ShapeBaseProps> = ({ speed, scale }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });
  const flashPeriod = Math.max(2, Math.round(8 / speed));
  const flash = interpolate(frame % flashPeriod, [0, flashPeriod * 0.25, flashPeriod * 0.5, flashPeriod * 0.75, flashPeriod], [1, 0.3, 1, 0.4, 1]);
  const scalePulse = 0.9 + Math.sin(t * 5 * speed) * 0.15;
  const triBase = 60 * scale;
  const triHeight = 104 * scale;

  return (
    <div
      style={{
        position: "absolute",
        top: 960,
        left: "50%",
        marginLeft: -triBase,
        width: 0,
        height: 0,
        borderLeft: `${triBase}px solid transparent`,
        borderRight: `${triBase}px solid transparent`,
        borderBottom: `${triHeight}px solid rgba(255, 179, 71, 0.6)`,
        transform: `scale(${scalePulse})`,
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
  const sp = activeScene?.shape_params ?? {};
  const shapeProps: ShapeBaseProps = {
    speed: sp.speed ?? 1.0,
    scale: sp.scale ?? 1.0,
    count: sp.count ?? 1,
  };

  if (emotion.includes("tension")) return <TensionShape {...shapeProps} />;
  if (emotion.includes("climax")) return <ClimaxShape {...shapeProps} />;
  if (emotion.includes("awakening")) return <AwakeningShape {...shapeProps} />;
  if (emotion.includes("buildup")) return <BuildupShape {...shapeProps} />;
  if (emotion.includes("intro")) return <IntroShape {...shapeProps} />;

  return null;
};
