import React, { useMemo } from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from "remotion";
import { createTikTokStyleCaptions } from "@remotion/captions";
import type { Caption, TikTokPage } from "@remotion/captions";
import { AudioFrame } from "../hooks/useAudioData";
import { Scene, NarrationSegment } from "../types";

interface SubtitleSectionProps {
  scenes: Scene[];
  audio: AudioFrame;
  accentColor: string;
  narrationSegments?: NarrationSegment[];
}

// NarrationSegment → Caption 변환 (문장 단위 1:1 매핑)
// 기존 단어별 선형 분할 방식 제거 → segment 타이밍 직접 사용으로 붕괴 방지
function segmentsToCaptions(segments: NarrationSegment[]): Caption[] {
  return segments.map((seg) => ({
    text: seg.text,
    startMs: seg.start_sec * 1000,
    endMs: seg.end_sec * 1000,
    timestampMs: seg.start_sec * 1000,
    confidence: null,
  }));
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

// TikTok 스타일 캡션 페이지 렌더러 — emotion별 4종 모션 패턴
const CaptionPage: React.FC<{ page: TikTokPage; emotion: string }> = ({
  page,
  emotion,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentTimeMs = (frame / fps) * 1000;
  const absoluteTimeMs = page.startMs + currentTimeMs;

  const colors = getColors(emotion);
  const fontSize = getFontSize(emotion);
  const bottom = getBottom(emotion);
  const isHeavy = emotion.includes("climax") || emotion.includes("awakening");

  // 공통 페이드인/아웃
  const pageMs = Math.max(page.durationMs ?? 200, 200);
  const fadeIn = interpolate(currentTimeMs, [0, 150], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(currentTimeMs, [pageMs - 150, pageMs], [1, 0], {
    extrapolateLeft: "clamp",
  });
  const baseOpacity = Math.min(fadeIn, fadeOut);

  // 패턴 A: 슬라이드 업 — intro, resolution, default
  const slideSpring = spring({ frame, fps, config: { damping: 200 } });
  const slideY = interpolate(slideSpring, [0, 1], [28, 0]);

  // 패턴 B: 스케일 인 — tension, climax
  const scaleSpring = spring({ frame, fps, config: { damping: 200 } });

  // 패턴 C: 타이프라이터 — awakening (string slice, CSS animation 금지)
  const totalChars = page.tokens.reduce((sum, t) => sum + t.text.length, 0);
  const visibleChars = Math.floor(
    interpolate(frame, [0, Math.max(1, fps * 0.9)], [0, totalChars], {
      extrapolateRight: "clamp",
    }),
  );

  // 패턴 D: 플래시 컷 — buildup (frame 기반, CSS animation 금지)
  const flashOpacity = interpolate(
    frame % 6,
    [0, 2, 4, 6],
    [1, 0.45, 1, 0.45],
  );
  const flashX = interpolate(
    frame % 8,
    [0, 2, 4, 6, 8],
    [0, -3, 3, -2, 0],
  );

  // 패턴 분기
  let opacity = baseOpacity;
  let transform = "none";

  if (emotion.includes("awakening")) {
    opacity = fadeIn;
  } else if (emotion.includes("buildup")) {
    opacity = baseOpacity * flashOpacity;
    transform = `translateX(${flashX}px)`;
  } else if (emotion.includes("tension") || emotion.includes("climax")) {
    transform = `scale(${scaleSpring})`;
  } else {
    transform = `translateY(${slideY}px)`;
  }

  // 토큰 렌더
  let charCount = 0;
  const renderTokens = () => {
    if (emotion.includes("awakening")) {
      // 타이프라이터: 문자 수 기반 슬라이싱
      return page.tokens.map((token) => {
        const tokenLen = token.text.length;
        const prev = charCount;
        charCount += tokenLen;
        const slice = token.text.slice(0, Math.max(0, visibleChars - prev));
        return (
          <span key={token.fromMs} style={{ color: colors.base }}>
            {slice}
          </span>
        );
      });
    }
    return page.tokens.map((token) => {
      const isActive =
        token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;
      return (
        <span
          key={token.fromMs}
          style={{
            color: isActive ? colors.highlight : colors.base,
            fontWeight: isActive ? 700 : isHeavy ? 700 : 500,
          }}
        >
          {token.text}
        </span>
      );
    });
  };

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
        {renderTokens()}
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

  const SWITCH_CAPTIONS_EVERY_MS = 4000;

  const captions = useMemo(
    () => (narrationSegments ? segmentsToCaptions(narrationSegments) : []),
    [narrationSegments],
  );

  const { pages } = useMemo(
    () =>
      createTikTokStyleCaptions({
        captions,
        combineTokensWithinMilliseconds: SWITCH_CAPTIONS_EVERY_MS,
      }),
    [captions],
  );

  if (pages.length === 0) return null;

  return (
    <>
      {pages.map((page, index) => {
        const nextPage = pages[index + 1] ?? null;
        const startFrame = Math.floor((page.startMs / 1000) * fps);
        const endFrame = Math.min(
          nextPage ? Math.floor((nextPage.startMs / 1000) * fps) : totalFrames,
          startFrame + Math.ceil((SWITCH_CAPTIONS_EVERY_MS / 1000) * fps),
          totalFrames,
        );
        const durationInFrames = endFrame - startFrame;

        if (durationInFrames <= 0) return null;

        const pageSec = page.startMs / 1000;
        const activeScene = scenes.find(
          (s) => pageSec >= s.start_sec && pageSec < s.end_sec,
        );
        const emotion = activeScene?.emotion ?? "";

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={durationInFrames}
            premountFor={fps}
          >
            <CaptionPage page={page} emotion={emotion} />
          </Sequence>
        );
      })}
    </>
  );
};
