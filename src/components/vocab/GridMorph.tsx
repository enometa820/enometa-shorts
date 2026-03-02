import React from "react";
import { interpolate } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * GridMorph — Max Cooper 스타일 격자 변형
 * variants: default (표준 웨이브), wave_propagation (파문 전파), pixel_dissolve (픽셀 분해)
 */
export const GridMorph: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  variant = "default",
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

  const points: Array<{
    x: number; y: number; ox: number; oy: number;
    distFromCenter: number; intensity: number;
  }> = [];

  const cx = width / 2;
  const cy = height / 2;
  const maxDist = Math.sqrt(cx * cx + cy * cy);

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const ox = (col + 1) * cellW;
      const oy = (row + 1) * cellH;

      const dx = ox - cx;
      const dy = oy - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const normalizedDist = dist / maxDist;
      const angle = Math.atan2(dy, dx);

      let displaceX = 0;
      let displaceY = 0;

      if (variant === "wave_propagation") {
        // 파문 전파: 중심에서 동심원 파문이 퍼져나감
        const ripplePhase = dist * 0.04 - t * 4;
        const rippleAmp = 25 * morphIntensity * Math.max(0, 1 - normalizedDist * 0.8);
        const ripple = Math.sin(ripplePhase) * rippleAmp;
        const bassWave = audio.bass * 30 * Math.sin(dist * 0.02 - t * 3) * (1 - normalizedDist);
        const onsetRipple = audio.onset
          ? Math.sin(dist * 0.06 - t * 10) * 40 * (1 - normalizedDist)
          : 0;

        displaceX = Math.cos(angle) * (ripple + bassWave + onsetRipple);
        displaceY = Math.sin(angle) * (ripple + bassWave + onsetRipple);

      } else if (variant === "pixel_dissolve") {
        // 픽셀 분해: 시간에 따라 격자가 흩어짐
        const dissolveT = sceneProgress;
        const dissolveThreshold = normalizedDist * 0.7 + 0.3;
        const isDissolving = dissolveT > dissolveThreshold * 0.5;

        if (isDissolving) {
          const localDissolve = Math.min((dissolveT - dissolveThreshold * 0.5) * 3, 1);
          const jitter = localDissolve * 40 * morphIntensity;
          const fallSpeed = localDissolve * localDissolve * 60;
          displaceX = (Math.sin(col * 7.3 + row * 13.1 + t * 2) * jitter) + audio.bass * 15;
          displaceY = fallSpeed + Math.cos(col * 5.7 + row * 11.3 + t * 3) * jitter * 0.5;
        } else {
          displaceX = audio.rms * 5 * Math.sin(t + col * 0.3);
          displaceY = audio.rms * 5 * Math.cos(t + row * 0.3);
        }

      } else {
        // default: 표준 웨이브 왜곡
        const wave1 = Math.sin(dist * 0.02 - t * 2.5) * 20 * morphIntensity;
        const wave2 = Math.cos(dist * 0.015 + t * 1.8) * 15 * morphIntensity;
        const bassDisplace = audio.bass * 40 * morphIntensity * (1 - normalizedDist * 0.5);
        const midRotate = audio.mid * 0.3 * morphIntensity;
        const breathe = audio.rms * 20 * morphIntensity;
        const onsetWave = audio.onset
          ? Math.sin(dist * 0.05 - t * 8) * 30 * (1 - normalizedDist)
          : 0;

        displaceX =
          Math.cos(angle + midRotate) * (wave1 + bassDisplace + onsetWave) +
          Math.sin(t * 0.5 + col * 0.3) * breathe * 0.3;
        displaceY =
          Math.sin(angle + midRotate) * (wave2 + bassDisplace + onsetWave) +
          Math.cos(t * 0.4 + row * 0.3) * breathe * 0.3;
      }

      // 씬 진행에 따른 등장
      const revealProgress = interpolate(sceneProgress, [0, 0.15], [0, 1], { extrapolateRight: "clamp" });
      const revealDelay = normalizedDist * 0.8;
      const pointReveal = interpolate(revealProgress, [revealDelay, revealDelay + 0.2], [0, 1], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });

      points.push({
        x: ox + displaceX * pointReveal,
        y: oy + displaceY * pointReveal,
        ox, oy, distFromCenter: normalizedDist, intensity: pointReveal,
      });
    }
  }

  if (mode === "dots" || mode === "wave") {
    return (
      <div style={{ position: "absolute", top: 0, left: 0, width, height, pointerEvents: "none" }}>
        <svg width={width} height={height}>
          {showConnections &&
            points.map((p, i) => {
              const col = i % cols;
              const row = Math.floor(i / cols);
              const lines: React.ReactNode[] = [];
              if (col < cols - 1) {
                const right = points[i + 1];
                lines.push(
                  <line key={`h-${i}`} x1={p.x} y1={p.y} x2={right.x} y2={right.y}
                    stroke={color} strokeWidth={0.5} opacity={0.1 * p.intensity} />
                );
              }
              if (row < rows - 1) {
                const below = points[i + cols];
                lines.push(
                  <line key={`v-${i}`} x1={p.x} y1={p.y} x2={below.x} y2={below.y}
                    stroke={color} strokeWidth={0.5} opacity={0.1 * p.intensity} />
                );
              }
              return lines;
            })}

          {points.map((p, i) => {
            const baseSize = 1.5 + audio.rms * 3;
            const isAccent = p.distFromCenter < 0.2 && Math.sin(i * 0.7 + t) > 0.7;
            const dotColor = isAccent ? accentColor : color;
            const size = isAccent ? baseSize * 2 : baseSize;
            const opacity = (0.2 + (1 - p.distFromCenter) * 0.6) * p.intensity;

            return (
              <React.Fragment key={i}>
                <circle cx={p.x} cy={p.y} r={size} fill={dotColor} opacity={opacity} />
                {isAccent && (
                  <circle cx={p.x} cy={p.y} r={size * 4} fill={accentColor} opacity={0.04 * p.intensity} />
                )}
              </React.Fragment>
            );
          })}
        </svg>
      </div>
    );
  }

  if (mode === "mesh") {
    return (
      <div style={{ position: "absolute", top: 0, left: 0, width, height, pointerEvents: "none" }}>
        <svg width={width} height={height}>
          {points.map((p, i) => {
            const col = i % cols;
            const row = Math.floor(i / cols);
            if (col >= cols - 1 || row >= rows - 1) return null;

            const topRight = points[i + 1];
            const bottomLeft = points[i + cols];
            const bottomRight = points[i + cols + 1];

            const cellDist = (p.distFromCenter + topRight.distFromCenter +
              bottomLeft.distFromCenter + bottomRight.distFromCenter) / 4;
            const opacity = (0.03 + (1 - cellDist) * 0.08 + audio.rms * 0.04) * p.intensity;

            return (
              <polygon key={i}
                points={`${p.x},${p.y} ${topRight.x},${topRight.y} ${bottomRight.x},${bottomRight.y} ${bottomLeft.x},${bottomLeft.y}`}
                fill={cellDist < 0.3 ? accentColor : color}
                opacity={opacity} stroke={color} strokeWidth={0.3} strokeOpacity={0.1 * p.intensity} />
            );
          })}
        </svg>
      </div>
    );
  }

  return null;
};
