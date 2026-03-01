import React from "react";
import { interpolate } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * PixelWaveform — 8bit 스타일 파형 시각화
 *
 * 저해상도 계단식 바로 오디오를 시각화. WaveformVisualizer의 lo-fi 버전.
 * 양자화된 높이, 제한 색상, 날카로운 픽셀 에지.
 *
 * params:
 *   bars: number         — 바 개수 (기본: 16, 낮을수록 더 8bit)
 *   colors: string[]     — 제한 팔레트 (기본: Game Boy 4색)
 *   mode: string         — bars | steps | cascade (기본: bars)
 *   quantize: number     — 높이 양자화 단계 (기본: 8)
 *   mirror: boolean      — 상하 대칭 (기본: true)
 *   position: string     — center | bottom (기본: center)
 */
export const PixelWaveform: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const barCount: number = params.bars || 16;
  const colors: string[] = params.colors || ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"];
  const mode: string = params.mode || "bars";
  const quantize: number = params.quantize || 8;
  const mirror: boolean = params.mirror ?? true;
  const position: string = params.position || "center";

  const t = frame / fps;

  // 등장
  const reveal = interpolate(sceneProgress, [0, 0.08], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 오디오 바 데이터 생성
  const generateBars = (): number[] => {
    const result: number[] = [];
    for (let i = 0; i < barCount; i++) {
      const n = i / barCount;
      const bassInf = Math.max(0, 1 - n * 3) * audio.bass;
      const midInf = Math.exp(-Math.pow((n - 0.4) * 4, 2)) * audio.mid;
      const highInf = Math.max(0, n - 0.6) * 2.5 * audio.high;
      const base = (bassInf * 0.6 + midInf * 0.3 + highInf * 0.1) * (0.5 + audio.rms * 0.5);
      const timeNoise = Math.sin(t * 3 + i * 0.5) * 0.08;
      const raw = Math.max(0, Math.min(1, base + timeNoise + 0.05));
      // 양자화: 계단식 높이
      const quantized = Math.round(raw * quantize) / quantize;
      result.push(quantized);
    }
    return result;
  };

  const barData = generateBars();
  const centerY = position === "bottom" ? height * 0.75 : height / 2;
  const maxH = height * 0.35;
  const barW = (width * 0.85) / barCount;
  const startX = width * 0.075;
  const gap = 2;

  const elements: React.ReactNode[] = [];

  if (mode === "bars" || mode === "steps") {
    barData.forEach((value, i) => {
      const x = startX + i * barW;
      const barH = value * maxH + 4;
      // 양자화된 높이를 셀 단위로 분할
      const cellSize = maxH / quantize;
      const activeCells = Math.round(value * quantize);

      if (mode === "steps") {
        // 셀 단위 렌더링 (진짜 8bit 느낌)
        for (let c = 0; c < activeCells; c++) {
          const cellY = centerY - (c + 1) * cellSize;
          const colorIdx = Math.min(Math.floor((c / quantize) * colors.length), colors.length - 1);
          const opacity = (0.6 + value * 0.4) * reveal;
          elements.push(
            <rect
              key={`u-${i}-${c}`}
              x={x + gap / 2}
              y={cellY}
              width={barW - gap}
              height={cellSize - 1}
              fill={colors[colorIdx]}
              opacity={opacity}
            />
          );
          // 미러 (아래)
          if (mirror) {
            elements.push(
              <rect
                key={`d-${i}-${c}`}
                x={x + gap / 2}
                y={centerY + c * cellSize + 1}
                width={barW - gap}
                height={cellSize - 1}
                fill={colors[colorIdx]}
                opacity={opacity * 0.4}
              />
            );
          }
        }
      } else {
        // 단순 바
        const colorIdx = Math.min(
          Math.floor(value * colors.length),
          colors.length - 1
        );
        const y = centerY - barH;
        elements.push(
          <rect
            key={`bar-${i}`}
            x={x + gap / 2}
            y={y}
            width={barW - gap}
            height={barH}
            fill={colors[colorIdx]}
            opacity={(0.6 + value * 0.4) * reveal}
          />
        );
        if (mirror) {
          elements.push(
            <rect
              key={`mir-${i}`}
              x={x + gap / 2}
              y={centerY}
              width={barW - gap}
              height={barH * 0.5}
              fill={colors[colorIdx]}
              opacity={(0.6 + value * 0.4) * reveal * 0.3}
            />
          );
        }
      }
    });
  } else if (mode === "cascade") {
    // 폭포형: 시간축이 아래로 흐름 (스펙트로그램 느낌)
    const historyRows = quantize * 2;
    for (let row = 0; row < historyRows; row++) {
      const timeOffset = row * 0.1;
      barData.forEach((value, i) => {
        const delayedValue = value * Math.max(0, 1 - row * 0.08);
        if (delayedValue < 0.05) return;
        const x = startX + i * barW;
        const y = centerY - maxH * 0.5 + row * (maxH / historyRows);
        const colorIdx = Math.min(
          Math.floor(delayedValue * colors.length),
          colors.length - 1
        );
        elements.push(
          <rect
            key={`cas-${row}-${i}`}
            x={x + gap / 2}
            y={y}
            width={barW - gap}
            height={maxH / historyRows - 1}
            fill={colors[colorIdx]}
            opacity={delayedValue * 0.8 * reveal}
          />
        );
      });
    }
  }

  // onset 플래시 프레임
  const flashBorder = audio.onset ? (
    <rect
      x={startX - 4}
      y={centerY - maxH - 8}
      width={width * 0.85 + 8}
      height={maxH * 2 + 16}
      fill="none"
      stroke={colors[colors.length - 1]}
      strokeWidth={3}
      opacity={0.6}
    />
  ) : null;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width,
        height,
        opacity: reveal,
        pointerEvents: "none",
        imageRendering: "pixelated",
      }}
    >
      <svg
        width={width}
        height={height}
        style={{ imageRendering: "pixelated" } as React.CSSProperties}
        shapeRendering="crispEdges"
      >
        {/* 중앙선 */}
        <line
          x1={startX}
          y1={centerY}
          x2={width - startX}
          y2={centerY}
          stroke={colors[0]}
          strokeWidth={1}
          opacity={0.3}
        />
        {elements}
        {flashBorder}
      </svg>
    </div>
  );
};
