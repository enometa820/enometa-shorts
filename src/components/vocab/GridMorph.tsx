import React from "react";
import { interpolate } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * GridMorph — Max Cooper 스타일 격자 변형
 *
 * 도트/라인 격자가 오디오에 반응하여 물결/왜곡/팽창/수축한다.
 * TouchDesigner / Max Cooper의 시각화 스타일 재현.
 *
 * params:
 *   cols: number        — 열 수 (기본: 24)
 *   rows: number        — 행 수 (기본: 24)
 *   mode: string        — dots | lines | mesh | wave (기본: dots)
 *   color: string       — 점/선 색상 (기본: #FFFFFF)
 *   morphIntensity: number — 왜곡 강도 (기본: 1.0)
 *   showConnections: boolean — 점 사이 연결선 (기본: false)
 */
export const GridMorph: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const cols: number = params.cols || 24;
  const rows: number = params.rows || 24;
  const mode: string = params.mode || "dots";
  const color: string = params.color || "#FFFFFF";
  const morphIntensity: number = params.morphIntensity || 1.0;
  const showConnections: boolean = params.showConnections || false;
  const accentColor: string = params.accentColor || "#8B5CF6";

  const t = frame / fps;
  const cellW = width / (cols + 1);
  const cellH = height / (rows + 1);

  // 격자 포인트 계산 (왜곡 적용)
  const points: Array<{
    x: number;
    y: number;
    ox: number;
    oy: number;
    distFromCenter: number;
    intensity: number;
  }> = [];

  const cx = width / 2;
  const cy = height / 2;
  const maxDist = Math.sqrt(cx * cx + cy * cy);

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const ox = (col + 1) * cellW;
      const oy = (row + 1) * cellH;

      // 중심으로부터 거리
      const dx = ox - cx;
      const dy = oy - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const normalizedDist = dist / maxDist;

      // 왜곡 계산
      const angle = Math.atan2(dy, dx);

      // 웨이브 왜곡 (시간 + 거리 기반)
      const wave1 = Math.sin(dist * 0.02 - t * 2.5) * 20 * morphIntensity;
      const wave2 = Math.cos(dist * 0.015 + t * 1.8) * 15 * morphIntensity;

      // 오디오 리액티브 왜곡
      const bassDisplace = audio.bass * 40 * morphIntensity * (1 - normalizedDist * 0.5);
      const midRotate = audio.mid * 0.3 * morphIntensity;

      // 호흡 효과 (rms)
      const breathe = audio.rms * 20 * morphIntensity;

      // onset 충격파
      const onsetWave = audio.onset
        ? Math.sin(dist * 0.05 - t * 8) * 30 * (1 - normalizedDist)
        : 0;

      // 최종 위치
      const displaceX =
        Math.cos(angle + midRotate) * (wave1 + bassDisplace + onsetWave) +
        Math.sin(t * 0.5 + col * 0.3) * breathe * 0.3;
      const displaceY =
        Math.sin(angle + midRotate) * (wave2 + bassDisplace + onsetWave) +
        Math.cos(t * 0.4 + row * 0.3) * breathe * 0.3;

      // 씬 진행에 따른 등장
      const revealProgress = interpolate(
        sceneProgress,
        [0, 0.15],
        [0, 1],
        { extrapolateRight: "clamp" }
      );
      const revealDelay = normalizedDist * 0.8;
      const pointReveal = interpolate(
        revealProgress,
        [revealDelay, revealDelay + 0.2],
        [0, 1],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      );

      points.push({
        x: ox + displaceX * pointReveal,
        y: oy + displaceY * pointReveal,
        ox,
        oy,
        distFromCenter: normalizedDist,
        intensity: pointReveal,
      });
    }
  }

  if (mode === "dots" || mode === "wave") {
    return (
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          pointerEvents: "none",
        }}
      >
        <svg width={width} height={height}>
          {/* 연결선 (옵션) */}
          {showConnections &&
            points.map((p, i) => {
              const col = i % cols;
              const row = Math.floor(i / cols);
              const lines: React.ReactNode[] = [];

              // 오른쪽 이웃
              if (col < cols - 1) {
                const right = points[i + 1];
                lines.push(
                  <line
                    key={`h-${i}`}
                    x1={p.x}
                    y1={p.y}
                    x2={right.x}
                    y2={right.y}
                    stroke={color}
                    strokeWidth={0.5}
                    opacity={0.1 * p.intensity}
                  />
                );
              }
              // 아래 이웃
              if (row < rows - 1) {
                const below = points[i + cols];
                lines.push(
                  <line
                    key={`v-${i}`}
                    x1={p.x}
                    y1={p.y}
                    x2={below.x}
                    y2={below.y}
                    stroke={color}
                    strokeWidth={0.5}
                    opacity={0.1 * p.intensity}
                  />
                );
              }
              return lines;
            })}

          {/* 도트 */}
          {points.map((p, i) => {
            const baseSize = 1.5 + audio.rms * 3;
            const isAccent = p.distFromCenter < 0.2 && Math.sin(i * 0.7 + t) > 0.7;
            const dotColor = isAccent ? accentColor : color;
            const size = isAccent ? baseSize * 2 : baseSize;
            const opacity = (0.2 + (1 - p.distFromCenter) * 0.6) * p.intensity;

            return (
              <React.Fragment key={i}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={size}
                  fill={dotColor}
                  opacity={opacity}
                />
                {isAccent && (
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={size * 4}
                    fill={accentColor}
                    opacity={0.04 * p.intensity}
                  />
                )}
              </React.Fragment>
            );
          })}
        </svg>
      </div>
    );
  }

  // mesh 모드: 격자 면을 채움
  if (mode === "mesh") {
    return (
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          pointerEvents: "none",
        }}
      >
        <svg width={width} height={height}>
          {points.map((p, i) => {
            const col = i % cols;
            const row = Math.floor(i / cols);
            if (col >= cols - 1 || row >= rows - 1) return null;

            const topLeft = p;
            const topRight = points[i + 1];
            const bottomLeft = points[i + cols];
            const bottomRight = points[i + cols + 1];

            const cellDist = (topLeft.distFromCenter + topRight.distFromCenter +
              bottomLeft.distFromCenter + bottomRight.distFromCenter) / 4;
            const opacity =
              (0.03 + (1 - cellDist) * 0.08 + audio.rms * 0.04) *
              topLeft.intensity;

            return (
              <polygon
                key={i}
                points={`${topLeft.x},${topLeft.y} ${topRight.x},${topRight.y} ${bottomRight.x},${bottomRight.y} ${bottomLeft.x},${bottomLeft.y}`}
                fill={cellDist < 0.3 ? accentColor : color}
                opacity={opacity}
                stroke={color}
                strokeWidth={0.3}
                strokeOpacity={0.1 * topLeft.intensity}
              />
            );
          })}
        </svg>
      </div>
    );
  }

  return null;
};
