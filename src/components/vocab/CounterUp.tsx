import React from "react";
import { interpolate } from "remotion";
import { VocabComponentProps } from "../../types";
import { easeOutCubic } from "../../utils/easing";

export const CounterUp: React.FC<VocabComponentProps> = ({
  target = 60000,
  position = "center",
  font_size = 120,
  color = "#FFFFFF",
  fade_out_at_end = true,
  audio,
  sceneProgress,
  width = 1080,
  height = 1080,
}) => {
  // 카운팅 애니메이션
  const countProgress = easeOutCubic(Math.min(sceneProgress * 1.5, 1));
  const currentValue = Math.floor(target * countProgress);

  // 포맷팅 (천 단위 구분)
  const formatted = currentValue.toLocaleString();

  // 페이드인/아웃
  let opacity = Math.min(sceneProgress * 5, 1);
  if (fade_out_at_end && sceneProgress > 0.8) {
    opacity *= (1 - sceneProgress) / 0.2;
  }

  // 오디오 리액티브: 비트에 맞춰 크기 살짝 변동
  const sizeBoost = audio.onset ? 0.05 : 0;
  const glowIntensity = 5 + audio.rms * 20;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width,
        height,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          fontFamily: "Pretendard Variable, monospace",
          fontWeight: 200,
          fontSize: font_size * (1 + sizeBoost),
          color,
          opacity,
          letterSpacing: "0.05em",
          textShadow: `0 0 ${glowIntensity}px ${color}66`,
        }}
      >
        {formatted}
      </div>
    </div>
  );
};
