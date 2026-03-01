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
 * 한국어 자연 줄바꿈: 공백(띄어쓰기) 기준으로만 끊어서 단어 잘림 방지
 * 텍스트 중간 지점에 가장 가까운 공백에서 2줄로 분할
 */
function smartLineBreak(text: string, charLimit: number = 18): string {
  if (text.length <= charLimit) return text;

  const words = text.split(" ");
  if (words.length <= 1) return text;

  // 텍스트 중간에 가장 가까운 공백 위치에서 2줄 분할
  const mid = text.length / 2;
  let bestSplitIdx = 0;
  let bestDist = Infinity;
  let pos = 0;

  for (let i = 0; i < words.length - 1; i++) {
    pos += words[i].length;
    const splitPos = pos + 1;
    const dist = Math.abs(splitPos - mid);
    if (dist < bestDist && splitPos >= 2 && splitPos <= text.length - 2) {
      bestDist = dist;
      bestSplitIdx = i + 1;
    }
    pos += 1;
  }

  if (bestSplitIdx === 0) return text;

  const line1 = words.slice(0, bestSplitIdx).join(" ");
  const line2 = words.slice(bestSplitIdx).join(" ");
  return line1 + "\n" + line2;
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
