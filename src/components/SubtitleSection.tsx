import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from "remotion";
import { AudioFrame } from "../hooks/useAudioData";
import { Scene, NarrationSegment } from "../types";

interface SubtitleSectionProps {
  scenes: Scene[];
  audio: AudioFrame;
  accentColor: string;
  narrationSegments?: NarrationSegment[];
}

// emotion별 색상 매핑
const EMOTION_COLORS: Record<string, { base: string; highlight: string }> = {
  awakening: { base: "#FFFFFF", highlight: "#FFD700" },
  tension:   { base: "#FFCCAA", highlight: "#FF4500" },
  climax:    { base: "#E0E0FF", highlight: "#00FFFF" },
  buildup:   { base: "#FFEECC", highlight: "#FFB347" },
  intro:     { base: "#CCCCCC", highlight: "#FFFFFF" },
};

const getColors = (emotion: string) =>
  Object.entries(EMOTION_COLORS).find(([k]) => emotion.includes(k))?.[1] ??
  { base: "#FFFFFF", highlight: "#FFD700" };

const getBottom = (emotion: string) => {
  if (emotion.includes("awakening")) return 400;
  if (emotion.includes("climax")) return 320;
  return 520;
};

const getFontSize = (emotion: string) => {
  if (emotion.includes("climax")) return 72;
  if (emotion.includes("awakening")) return 66;
  if (emotion.includes("tension")) return 58;
  return 54;
};

// 세그먼트 단위 자막 렌더러 — emotion별 4종 모션 패턴
// createTikTokStyleCaptions 완전 제거: 문장 합침 버그 방지
const SegmentSubtitle: React.FC<{ text: string; emotion: string }> = ({
  text,
  emotion,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const colors = getColors(emotion);
  const fontSize = getFontSize(emotion);
  const bottom = getBottom(emotion);
  const isHeavy = emotion.includes("climax") || emotion.includes("awakening");

  // 공통 페이드인 (8프레임 = 약 0.27초)
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 패턴 A: 슬라이드업 — intro, resolution, default
  const slideSpring = spring({ frame, fps, config: { damping: 200 } });
  const slideY = interpolate(slideSpring, [0, 1], [28, 0]);

  // 패턴 B: 스케일인 — tension, climax
  const scaleSpring = spring({ frame, fps, config: { damping: 200 } });

  // 패턴 C: 타이프라이터 — awakening (string slice, CSS animation 금지)
  const totalChars = text.length;
  const visibleChars = Math.floor(
    interpolate(frame, [0, Math.max(1, fps * 0.9)], [0, totalChars], {
      extrapolateRight: "clamp",
    }),
  );

  // 패턴 D: 플래시컷 — buildup
  const flashOpacity = interpolate(frame % 6, [0, 2, 4, 6], [1, 0.45, 1, 0.45]);
  const flashX = interpolate(frame % 8, [0, 2, 4, 6, 8], [0, -3, 3, -2, 0]);

  let transform = "none";
  let opacity = fadeIn;

  if (emotion.includes("awakening")) {
    opacity = fadeIn;
  } else if (emotion.includes("buildup")) {
    opacity = fadeIn * flashOpacity;
    transform = `translateX(${flashX}px)`;
  } else if (emotion.includes("tension") || emotion.includes("climax")) {
    transform = `scale(${scaleSpring})`;
  } else {
    transform = `translateY(${slideY}px)`;
  }

  const displayText = emotion.includes("awakening")
    ? text.slice(0, visibleChars)
    : text;

  return (
    <div
      style={{
        position: "absolute",
        bottom,
        left: 0,
        width: 1080,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 80px",
        pointerEvents: "none",
        opacity,
        transform,
      }}
    >
      <div
        style={{
          fontFamily: "Pretendard Variable, sans-serif",
          fontWeight: isHeavy ? 700 : 500,
          fontSize,
          color: colors.base,
          textAlign: "center",
          lineHeight: 1.5,
          textShadow: [
            "0 2px 8px rgba(0,0,0,0.95)",
            "0 0 20px rgba(0,0,0,0.7)",
            "0 0 40px rgba(0,0,0,0.4)",
          ].join(", "),
          backgroundColor: "rgba(0, 0, 0, 0.35)",
          padding: "16px 36px",
          borderRadius: 12,
          maxWidth: 920,
          wordBreak: "keep-all",
          overflowWrap: "normal",
          whiteSpace: "pre-wrap",
        }}
      >
        {displayText}
      </div>
    </div>
  );
};

export const SubtitleSection: React.FC<SubtitleSectionProps> = ({
  scenes,
  audio,
  accentColor,
  narrationSegments,
}) => {
  const { fps, durationInFrames: totalFrames } = useVideoConfig();

  if (!narrationSegments || narrationSegments.length === 0) return null;

  return (
    <>
      {narrationSegments.map((seg, index) => {
        const startFrame = Math.floor(seg.start_sec * fps);
        const nextSeg = narrationSegments[index + 1] ?? null;
        // 다음 세그먼트 시작까지 또는 영상 끝까지 (최대 8초)
        const maxDuration = Math.ceil(fps * 8);
        const endFrame = Math.min(
          nextSeg ? Math.floor(nextSeg.start_sec * fps) : totalFrames,
          startFrame + maxDuration,
          totalFrames,
        );
        const durationInFrames = Math.max(1, endFrame - startFrame);

        const activeScene = scenes.find(
          (s) => seg.start_sec >= s.start_sec && seg.start_sec < s.end_sec,
        );
        const emotion = activeScene?.emotion ?? "";

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={durationInFrames}
            premountFor={fps}
          >
            <SegmentSubtitle text={seg.text} emotion={emotion} />
          </Sequence>
        );
      })}
    </>
  );
};
