import React from "react";
import { interpolate } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * WaveformVisualizer — 오디오 파형 시각화
 *
 * 오디오 데이터를 파형/스펙트럼/원형 형태로 시각화한다.
 * 음악과 나레이션이 살아 움직이는 것을 보여준다.
 *
 * params:
 *   mode: string       — waveform | spectrum | circular | mirror (기본: waveform)
 *   color: string      — 파형 색상 (기본: #8B5CF6)
 *   lineWidth: number  — 선 두께 (기본: 2)
 *   bars: number       — 바/포인트 수 (기본: 64)
 *   mirror: boolean    — 상하 대칭 (기본: false)
 *   filled: boolean    — 채움 (기본: false)
 *   position: string   — center | bottom | full (기본: center)
 */
export const WaveformVisualizer: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const mode: string = params.mode || "waveform";
  const color: string = params.color || "#8B5CF6";
  const lineWidth: number = params.lineWidth || 2;
  const barCount: number = params.bars || 64;
  const mirror: boolean = params.mirror || false;
  const filled: boolean = params.filled || false;
  const position: string = params.position || "center";
  const accentColor: string = params.accentColor || "#FF4444";

  const t = frame / fps;

  // 시뮬레이션된 주파수 데이터 생성 (실제 FFT 데이터 대용)
  const generateBars = (): number[] => {
    const result: number[] = [];
    for (let i = 0; i < barCount; i++) {
      const normalized = i / barCount;
      // 저주파 (bass 영향), 중주파 (mid 영향), 고주파 (high 영향) 혼합
      const bassInfluence = Math.max(0, 1 - normalized * 3) * audio.bass;
      const midInfluence =
        Math.exp(-Math.pow((normalized - 0.4) * 4, 2)) * audio.mid;
      const highInfluence = Math.max(0, normalized - 0.6) * 2.5 * audio.high;

      const base =
        (bassInfluence * 0.6 + midInfluence * 0.3 + highInfluence * 0.1) *
        (0.5 + audio.rms * 0.5);

      // 시간 변화 추가
      const timeNoise =
        Math.sin(t * 3 + i * 0.3) * 0.1 +
        Math.sin(t * 5.7 + i * 0.7) * 0.05;

      result.push(Math.max(0, Math.min(1, base + timeNoise + 0.02)));
    }
    return result;
  };

  const barData = generateBars();

  // 등장 애니메이션
  const revealOpacity = interpolate(sceneProgress, [0, 0.1], [0, 1], {
    extrapolateRight: "clamp",
  });

  const centerY = position === "bottom" ? height * 0.75 : height / 2;
  const maxBarHeight =
    position === "full" ? height * 0.4 : height * 0.25;

  if (mode === "circular") {
    const radius = Math.min(width, height) * 0.25;
    const angleStep = (Math.PI * 2) / barCount;

    return (
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          opacity: revealOpacity,
          pointerEvents: "none",
        }}
      >
        <svg width={width} height={height}>
          {barData.map((value, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const barLen = value * maxBarHeight + 5;
            const x1 = width / 2 + Math.cos(angle) * radius;
            const y1 = height / 2 + Math.sin(angle) * radius;
            const x2 = width / 2 + Math.cos(angle) * (radius + barLen);
            const y2 = height / 2 + Math.sin(angle) * (radius + barLen);

            const intensity = value;
            const barColor =
              intensity > 0.6 ? accentColor : color;
            const opacity = 0.3 + intensity * 0.7;

            return (
              <React.Fragment key={i}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={barColor}
                  strokeWidth={lineWidth + intensity * 2}
                  strokeLinecap="round"
                  opacity={opacity}
                />
                {/* 미러 (안쪽) */}
                {mirror && (
                  <line
                    x1={x1}
                    y1={y1}
                    x2={
                      width / 2 +
                      Math.cos(angle) * (radius - barLen * 0.4)
                    }
                    y2={
                      height / 2 +
                      Math.sin(angle) * (radius - barLen * 0.4)
                    }
                    stroke={barColor}
                    strokeWidth={lineWidth}
                    strokeLinecap="round"
                    opacity={opacity * 0.4}
                  />
                )}
              </React.Fragment>
            );
          })}

          {/* 중앙 원 */}
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius - 5}
            fill="none"
            stroke={color}
            strokeWidth={1}
            opacity={0.15}
          />
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius + audio.rms * 10}
            fill="none"
            stroke={color}
            strokeWidth={0.5}
            opacity={0.08}
          />
        </svg>
      </div>
    );
  }

  // === spectrum / waveform / mirror ===
  const barWidth = (width * 0.85) / barCount;
  const startX = width * 0.075;

  if (mode === "spectrum") {
    return (
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          opacity: revealOpacity,
          pointerEvents: "none",
        }}
      >
        <svg width={width} height={height}>
          {barData.map((value, i) => {
            const x = startX + i * barWidth;
            const barH = value * maxBarHeight * 2 + 2;
            const y = mirror ? centerY - barH : centerY - barH;
            const intensity = value;
            const barColor = intensity > 0.6 ? accentColor : color;

            return (
              <React.Fragment key={i}>
                {/* 메인 바 */}
                <rect
                  x={x}
                  y={y}
                  width={Math.max(barWidth - 2, 1)}
                  height={barH}
                  rx={1}
                  fill={barColor}
                  opacity={0.4 + intensity * 0.6}
                />
                {/* 글로우 */}
                {intensity > 0.4 && (
                  <rect
                    x={x - 1}
                    y={y - 2}
                    width={Math.max(barWidth, 2)}
                    height={barH + 4}
                    rx={2}
                    fill={barColor}
                    opacity={0.08}
                    filter="url(#glow)"
                  />
                )}
                {/* 미러 (아래 반사) */}
                {mirror && (
                  <rect
                    x={x}
                    y={centerY}
                    width={Math.max(barWidth - 2, 1)}
                    height={barH * 0.6}
                    rx={1}
                    fill={barColor}
                    opacity={(0.4 + intensity * 0.6) * 0.3}
                  />
                )}
              </React.Fragment>
            );
          })}

          {/* 중앙 라인 */}
          <line
            x1={startX}
            y1={centerY}
            x2={width - startX}
            y2={centerY}
            stroke={color}
            strokeWidth={0.5}
            opacity={0.15}
          />

          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
        </svg>
      </div>
    );
  }

  // waveform: 부드러운 곡선
  const wavePoints = barData
    .map((value, i) => {
      const x = startX + i * barWidth + barWidth / 2;
      const y = centerY - (value - 0.5) * maxBarHeight * 2;
      return `${x},${y}`;
    })
    .join(" ");

  const mirrorPoints = mirror
    ? barData
        .map((value, i) => {
          const x = startX + i * barWidth + barWidth / 2;
          const y = centerY + (value - 0.5) * maxBarHeight * 1.2;
          return `${x},${y}`;
        })
        .join(" ")
    : "";

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width,
        height,
        opacity: revealOpacity,
        pointerEvents: "none",
      }}
    >
      <svg width={width} height={height}>
        {/* 메인 파형 */}
        <polyline
          points={wavePoints}
          fill={filled ? `${color}20` : "none"}
          stroke={color}
          strokeWidth={lineWidth}
          strokeLinejoin="round"
          strokeLinecap="round"
          opacity={0.8}
        />
        {/* 글로우 파형 */}
        <polyline
          points={wavePoints}
          fill="none"
          stroke={color}
          strokeWidth={lineWidth + 4}
          strokeLinejoin="round"
          opacity={0.1 + audio.rms * 0.15}
        />
        {/* 미러 */}
        {mirror && (
          <polyline
            points={mirrorPoints}
            fill={filled ? `${color}10` : "none"}
            stroke={color}
            strokeWidth={lineWidth * 0.7}
            strokeLinejoin="round"
            opacity={0.25}
          />
        )}
        {/* 중앙선 */}
        <line
          x1={startX}
          y1={centerY}
          x2={width - startX}
          y2={centerY}
          stroke={color}
          strokeWidth={0.5}
          opacity={0.1}
        />
      </svg>
    </div>
  );
};
