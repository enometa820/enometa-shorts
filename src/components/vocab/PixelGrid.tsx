import React from "react";
import { interpolate } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * PixelGrid — 8bit 스타일 격자 비주얼
 *
 * NES/Game Boy 느낌의 저해상도 격자. 셀이 오디오에 반응하여 점등/소등.
 * 모든 움직임이 그리드에 스냅되어 레트로 게임 미학을 재현.
 *
 * params:
 *   cols: number         — 열 수 (기본: 32, 낮을수록 더 픽셀)
 *   rows: number         — 행 수 (기본: 32)
 *   mode: string         — fill | outline | life | rain (기본: fill)
 *   colors: string[]     — 제한 팔레트 (기본: Game Boy 4색)
 *   pixelGap: number     — 셀 간격 (기본: 1)
 *   reactivity: number   — 오디오 반응 강도 (기본: 1.0)
 */
export const PixelGrid: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const cols: number = params.cols || 32;
  const rows: number = params.rows || 32;
  const mode: string = params.mode || "fill";
  const colors: string[] = params.colors || ["#0f380f", "#306230", "#8bac0f", "#9bbc0f"];
  const pixelGap: number = params.pixelGap ?? 1;
  const reactivity: number = params.reactivity || 1.0;

  const t = frame / fps;
  const cellW = (width - pixelGap) / cols;
  const cellH = (height - pixelGap) / rows;

  // 등장 애니메이션
  const reveal = interpolate(sceneProgress, [0, 0.12], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 의사 난수 (시드 기반, 결정적)
  const hash = (x: number, y: number, seed: number) => {
    const n = Math.sin(x * 12.9898 + y * 78.233 + seed * 43758.5453) * 43758.5453;
    return n - Math.floor(n);
  };

  const cells: React.ReactNode[] = [];

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const x = col * cellW + pixelGap;
      const y = row * cellH + pixelGap;
      const w = cellW - pixelGap;
      const h = cellH - pixelGap;

      // 중심 거리
      const nx = col / cols - 0.5;
      const ny = row / rows - 0.5;
      const dist = Math.sqrt(nx * nx + ny * ny) * 2;

      // 셀 활성화 판단
      let active = false;
      let colorIdx = 0;

      if (mode === "fill") {
        // 오디오 기반: bass가 높으면 중앙부터 활성화 확장
        const threshold = 1.0 - (audio.bass * 0.6 + audio.rms * 0.4) * reactivity;
        active = dist < threshold ? false : true;
        // onset 충격파
        const waveDist = Math.abs(dist - ((t * 2) % 2));
        if (audio.onset && waveDist < 0.15) active = true;
        // 시간 기반 패턴
        const pattern = hash(col, row, Math.floor(t * 4));
        if (pattern < audio.rms * reactivity * 0.5) active = true;
        colorIdx = Math.floor(dist * (colors.length - 1));
      } else if (mode === "outline") {
        // 가장자리만 활성화 + 오디오 두께 변화
        const edgeDist = Math.min(col, row, cols - 1 - col, rows - 1 - row);
        const thickness = Math.floor(1 + audio.bass * 3 * reactivity);
        active = edgeDist < thickness;
        colorIdx = edgeDist;
      } else if (mode === "life") {
        // Game of Life 스타일: 매 프레임 패턴 변화
        const gen = Math.floor(t * 3);
        const alive = hash(col, row, gen) < (0.3 + audio.rms * 0.3 * reactivity);
        const neighbors = [
          hash(col - 1, row, gen), hash(col + 1, row, gen),
          hash(col, row - 1, gen), hash(col, row + 1, gen),
        ].filter((v) => v < 0.4).length;
        active = alive && neighbors >= 1 && neighbors <= 3;
        colorIdx = neighbors;
      } else if (mode === "rain") {
        // 디지털 비: 세로 줄이 위에서 아래로 떨어짐
        const speed = 8 + hash(col, 0, 0) * 12;
        const offset = hash(col, 0, 1) * rows;
        const rainPos = ((t * speed + offset) % (rows * 1.5));
        const diff = row - rainPos;
        active = diff >= 0 && diff < 4 + audio.bass * 6 * reactivity;
        colorIdx = Math.min(Math.floor(diff), colors.length - 1);
        if (audio.onset && hash(col, row, Math.floor(t * 10)) < 0.3) active = true;
      }

      if (!active) continue;

      // 등장 딜레이
      const cellReveal = interpolate(
        reveal,
        [dist * 0.5, dist * 0.5 + 0.3],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );
      if (cellReveal <= 0) continue;

      const safeIdx = Math.max(0, Math.min(colorIdx, colors.length - 1));
      const opacity = (0.5 + audio.rms * 0.5) * cellReveal;

      cells.push(
        <rect
          key={`${col}-${row}`}
          x={x}
          y={y}
          width={w}
          height={h}
          fill={colors[safeIdx]}
          opacity={opacity}
        />
      );
    }
  }

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
        {cells}
      </svg>
    </div>
  );
};
