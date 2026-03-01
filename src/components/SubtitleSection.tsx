import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { AudioFrame } from "../hooks/useAudioData";
import { Scene, NarrationSegment } from "../types";

interface SubtitleSectionProps {
  scenes: Scene[];
  audio: AudioFrame;
  accentColor: string;
  narrationSegments?: NarrationSegment[];
}

/**
 * 한국어 자연 줄바꿈: 조사/어미 뒤에서 끊고 단어 중간 잘림 방지
 * 한 줄 최대 charLimit 글자, 2줄까지만
 */
function smartLineBreak(text: string, charLimit: number = 18): string {
  if (text.length <= charLimit) return text;

  // 조사/어미/쉼표/마침표 뒤가 자연스러운 줄바꿈 지점
  const breakAfter = /([은는이가을를에서도의로와과만까지부터라고처럼보다마다씩째]|[,.])\s*/g;
  const mid = Math.floor(text.length / 2);

  // 중간 근처에서 가장 가까운 자연 줄바꿈 지점 찾기
  let bestPos = -1;
  let bestDist = Infinity;

  let match;
  while ((match = breakAfter.exec(text)) !== null) {
    const pos = match.index + match[0].length;
    // 줄바꿈 후 양쪽 모두 3글자 이상이어야
    if (pos >= 3 && pos <= text.length - 3) {
      const dist = Math.abs(pos - mid);
      if (dist < bestDist) {
        bestDist = dist;
        bestPos = pos;
      }
    }
  }

  // 자연 줄바꿈 지점을 못 찾으면 공백 기준으로
  if (bestPos === -1) {
    const spaceIdx = text.indexOf(" ", Math.max(3, mid - 5));
    if (spaceIdx > 0 && spaceIdx < text.length - 3) {
      bestPos = spaceIdx + 1;
    }
  }

  // 그래도 못 찾으면 원문 그대로 (word-break: keep-all이 처리)
  if (bestPos === -1) return text;

  return text.slice(0, bestPos).trimEnd() + "\n" + text.slice(bestPos).trimStart();
}

export const SubtitleSection: React.FC<SubtitleSectionProps> = ({
  scenes,
  audio,
  accentColor,
  narrationSegments,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  // narration segments가 있으면 1문장씩, 없으면 씬 단위
  const activeSegment = narrationSegments?.find(
    (s) => currentTime >= s.start_sec && currentTime < s.end_sec,
  );

  // 현재 씬 정보 (감정 기반 스타일링용)
  const activeScene = scenes.find(
    (s) => currentTime >= s.start_sec && currentTime < s.end_sec,
  );

  const displayText = activeSegment?.text;
  if (!displayText) {
    return null;
  }

  // 세그먼트 내 진행도
  const segDuration = activeSegment.end_sec - activeSegment.start_sec;
  const segElapsed = currentTime - activeSegment.start_sec;

  // 페이드인/아웃
  const fadeIn = interpolate(segElapsed, [0, 0.2], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    segElapsed,
    [segDuration - 0.2, segDuration],
    [1, 0],
    { extrapolateLeft: "clamp" },
  );
  const opacity = Math.min(fadeIn, fadeOut);

  // 감정에 따른 스타일 (클라이맥스/각성 장면에서 강조)
  const emotion = activeScene?.emotion || "";
  const isEmphasis =
    emotion.includes("climax") || emotion.includes("awakening");
  const fontSize = isEmphasis ? 48 : 42;

  // 한국어 스마트 줄바꿈 적용
  const formattedText = smartLineBreak(displayText, 18);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 550,
        left: 0,
        width: 1080,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 100px 0 60px",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          fontFamily: "Pretendard Variable, sans-serif",
          fontWeight: isEmphasis ? 600 : 400,
          fontSize,
          color: "#FFFFFF",
          textAlign: "center",
          lineHeight: 1.5,
          opacity,
          textShadow: [
            "0 2px 8px rgba(0,0,0,0.95)",
            "0 0 20px rgba(0,0,0,0.7)",
            "0 0 40px rgba(0,0,0,0.4)",
          ].join(", "),
          backgroundColor: "rgba(0, 0, 0, 0.35)",
          padding: "12px 28px",
          borderRadius: 12,
          maxWidth: 900,
          wordBreak: "keep-all",
          overflowWrap: "break-word",
          whiteSpace: "pre-line",
        }}
      >
        {formattedText}
      </div>
    </div>
  );
};
