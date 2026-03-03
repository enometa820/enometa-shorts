import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { Scene } from "../types";

interface ShapeMotionProps {
  scenes: Scene[];
}

// 패턴: tension — 사각형 테두리 (spring scale + 회전)
const TensionShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scaleSpring = spring({ frame, fps, config: { damping: 20, stiffness: 200 } });
  const scale = interpolate(scaleSpring, [0, 1], [0.5, 1]);
  const rotate = interpolate(frame, [0, fps * 2], [0, 12], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, 12], [0, 0.55], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 290,
        left: "50%",
        width: 180,
        height: 180,
        marginLeft: -90,
        border: "2px solid rgba(255, 68, 0, 0.75)",
        borderRadius: 4,
        transform: `scale(${scale}) rotate(${rotate}deg)`,
        opacity,
        pointerEvents: "none",
      }}
    />
  );
};

// 패턴: climax — 원형 펄스 (opacity 파동 + scale)
const ClimaxShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cycleLen = fps * 1.2;
  const cycleFrame = frame % cycleLen;

  const pulse = interpolate(
    cycleFrame,
    [0, cycleLen * 0.5, cycleLen],
    [1, 1.1, 1],
  );
  const opacity = interpolate(
    cycleFrame,
    [0, cycleLen * 0.25, cycleLen * 0.5, cycleLen * 0.75, cycleLen],
    [0.5, 0.85, 0.5, 0.8, 0.5],
  );
  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 180,
        left: "50%",
        width: 150,
        height: 150,
        marginLeft: -75,
        border: "1.5px solid rgba(0, 255, 255, 0.85)",
        borderRadius: "50%",
        transform: `scale(${pulse})`,
        opacity: opacity * fadeIn,
        pointerEvents: "none",
      }}
    />
  );
};

// 패턴: awakening — 수평선 2개 (좌→우 spring 슬라이드)
const AwakeningShape: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slideSpring = spring({ frame, fps, config: { damping: 200 } });
  const scaleX = interpolate(slideSpring, [0, 1], [0, 1]);
  const opacity = interpolate(frame, [0, 10], [0, 0.75], {
    extrapolateRight: "clamp",
  });

  return (
    <>
      <div
        style={{
          position: "absolute",
          bottom: 262,
          left: "50%",
          width: 280,
          height: 1.5,
          marginLeft: -140,
          backgroundColor: "rgba(255, 215, 0, 0.85)",
          transform: `scaleX(${scaleX})`,
          transformOrigin: "left center",
          opacity,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 252,
          left: "50%",
          width: 180,
          height: 1.5,
          marginLeft: -90,
          backgroundColor: "rgba(255, 215, 0, 0.5)",
          transform: `scaleX(${scaleX})`,
          transformOrigin: "left center",
          opacity,
          pointerEvents: "none",
        }}
      />
    </>
  );
};

// 패턴: intro — 점 3개 stagger 페이드인
const IntroShape: React.FC = () => {
  const frame = useCurrentFrame();
  const STAGGER = 6;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 242,
        left: "50%",
        display: "flex",
        gap: 10,
        marginLeft: -27,
        pointerEvents: "none",
      }}
    >
      {[0, 1, 2].map((i) => {
        const delayedFrame = Math.max(0, frame - i * STAGGER);
        const opacity = interpolate(delayedFrame, [0, 10], [0, 0.65], {
          extrapolateRight: "clamp",
        });
        return (
          <div
            key={i}
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: "rgba(204, 204, 204, 0.9)",
              opacity,
            }}
          />
        );
      })}
    </div>
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
  if (emotion.includes("intro")) return <IntroShape />;

  return null;
};
