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

/**
 * 긴 세그먼트를 문장(마침표) 단위로 분할하여 서브 타이밍을 생성.
 * EP007처럼 한 세그먼트에 4문장(70자)이 합쳐진 경우,
 * 세그먼트 시간을 문장 수로 균등 분배하여 순차 표시.
 */
function splitSegmentToSentences(
  text: string,
  startSec: number,
  endSec: number,
): { text: string; startSec: number; endSec: number }[] {
  // 마침표 뒤에서 분할 (마침표 유지)
  const sentences = text
    .split(/(?<=\.)\s*/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  if (sentences.length <= 1) {
    return [{ text, startSec, endSec }];
  }

  const totalDur = endSec - startSec;
  // 글자 수 비례로 시간 분배
  const totalChars = sentences.reduce((sum, s) => sum + s.length, 0);

  const result: { text: string; startSec: number; endSec: number }[] = [];
  let t = startSec;

  for (let i = 0; i < sentences.length; i++) {
    const ratio = sentences[i].length / totalChars;
    const dur = totalDur * ratio;
    result.push({
      text: sentences[i],
      startSec: t,
      endSec: t + dur,
    });
    t += dur;
  }

  return result;
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

  if (!narrationSegments || narrationSegments.length === 0) return null;

  // 현재 활성 세그먼트 찾기
  const activeSegment = narrationSegments.find(
    (s) => currentTime >= s.start_sec && currentTime < s.end_sec,
  );

  if (!activeSegment?.text) return null;

  // 긴 세그먼트(35자 초과)는 문장 단위로 분할
  const subParts =
    activeSegment.text.length > 35
      ? splitSegmentToSentences(
          activeSegment.text,
          activeSegment.start_sec,
          activeSegment.end_sec,
        )
      : [
          {
            text: activeSegment.text,
            startSec: activeSegment.start_sec,
            endSec: activeSegment.end_sec,
          },
        ];

  // 현재 시간에 맞는 서브파트 찾기
  const activePart = subParts.find(
    (p) => currentTime >= p.startSec && currentTime < p.endSec,
  );

  if (!activePart) return null;

  const displayText = activePart.text;

  // 현재 씬 정보 (감정 기반 스타일링용)
  const activeScene = scenes.find(
    (s) => currentTime >= s.start_sec && currentTime < s.end_sec,
  );

  // 서브파트 내 진행도
  const partDuration = activePart.endSec - activePart.startSec;
  const partElapsed = currentTime - activePart.startSec;

  // 페이드인/아웃
  const fadeIn = interpolate(partElapsed, [0, 0.15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    partElapsed,
    [partDuration - 0.15, partDuration],
    [1, 0],
    { extrapolateLeft: "clamp" },
  );
  const opacity = Math.min(fadeIn, fadeOut);

  // 감정에 따른 스타일
  const emotion = activeScene?.emotion || "";
  const isEmphasis =
    emotion.includes("climax") || emotion.includes("awakening");
  const fontSize = isEmphasis ? 62 : 54;

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
          fontWeight: isEmphasis ? 700 : 500,
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
          padding: "16px 36px",
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
