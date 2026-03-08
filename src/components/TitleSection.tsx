import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { fitText } from "@remotion/layout-utils";
import { AudioFrame } from "../hooks/useAudioData";

interface TitleSectionProps {
  title: string;
  audio: AudioFrame;
  accentColor: string;
  glowColor: string;
  highlightWords?: string[];
  endcardStartFrame?: number;
}

export const TitleSection: React.FC<TitleSectionProps> = ({
  title,
  audio,
  accentColor,
  glowColor,
  highlightWords = [],
  endcardStartFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 인트로 페이드인 (0~1초)
  const fadeIn = interpolate(frame, [0, fps], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 엔드카드 시작 1초 전부터 fade-out
  let fadeOut = 1;
  if (endcardStartFrame) {
    fadeOut = interpolate(
      frame,
      [endcardStartFrame - fps, endcardStartFrame],
      [1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );
  }
  const opacity = fadeIn * fadeOut;

  // 오디오 리액티브 글로우
  const glowIntensity = 8 + audio.rms * 20;

  // 마침표 뒤 공백에서 문장 단위 줄바꿈 (2줄 처리)
  // text-wrap: balance가 자동 균등 분배하므로 \n 강제 삽입은 마침표 케이스만
  const titleFormatted = title.includes(". ")
    ? title.replace(/\.\s+/g, ".\n")
    : title;

  // fitText: 제목 길이에 따라 fontSize 자동 조절 (최대 72px)
  const { fontSize } = fitText({
    text: titleFormatted,
    withinWidth: 920,
    fontFamily: "Pretendard Variable, sans-serif",
    fontWeight: "900",
  });
  const titleFontSize = Math.min(fontSize, 72);

  // 핵심 키워드를 붉은색으로 렌더링
  const renderTitle = () => {
    if (highlightWords.length === 0) return titleFormatted;

    // 키워드 매칭을 위한 정규식
    const pattern = highlightWords
      .map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("|");
    const regex = new RegExp(`(${pattern})`, "g");
    const parts = titleFormatted.split(regex);

    return parts.map((part, i) => {
      const isHighlight = highlightWords.includes(part);
      if (isHighlight) {
        return (
          <span
            key={i}
            style={{
              color: "#FF4444",
              WebkitTextStroke: "2px #5A0000",
              textShadow: [
                `0 0 ${glowIntensity + 4}px rgba(255, 68, 68, 0.7)`,
                "0 2px 4px rgba(0, 0, 0, 0.8)",
              ].join(", "),
            }}
          >
            {part}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  // 비주얼 영역(y=370) 바로 위에 배치
  return (
    <div
      style={{
        position: "absolute",
        top: 180,
        left: 0,
        width: 1080,
        height: 190,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        opacity,
      }}
    >
      <div
        style={{
          fontFamily: "Pretendard Variable, sans-serif",
          fontWeight: 900,
          fontSize: titleFontSize,
          letterSpacing: "0.08em",
          color: "#FFD700",
          textAlign: "center",
          WebkitTextStroke: "2px #1A1A2E",
          paintOrder: "stroke fill",
          textShadow: [
            `0 0 ${glowIntensity}px rgba(255, 215, 0, 0.6)`,
            "0 2px 6px rgba(0, 0, 0, 0.9)",
            "0 0 30px rgba(0, 0, 0, 0.6)",
          ].join(", "),
          padding: "0 80px",
          lineHeight: 1.25,
          wordBreak: "keep-all" as const,
          overflowWrap: "normal" as const,
          whiteSpace: "pre-line" as const,
          textWrap: "balance" as const,
        }}
      >
        {renderTitle()}
      </div>
    </div>
  );
};
