import React from "react";
import { interpolate } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * DataBar — 데이터 시각화 (바 차트 + 인포그래픽)
 *
 * 숫자/통계가 등장하는 대본에서 바 차트를 애니메이션으로 보여준다.
 * 오디오 리액티브: bass로 바가 떨리고, onset에 새 바가 등장
 *
 * params:
 *   bars: Array<{label: string, value: number, color?: string}>
 *   maxValue: number        — 바 스케일 기준 (기본: 100)
 *   orientation: string     — horizontal | vertical (기본: horizontal)
 *   style: string           — bar | ring | radial (기본: bar)
 *   showLabels: boolean     — 라벨 표시 (기본: true)
 *   showValues: boolean     — 값 표시 (기본: true)
 *   color: string           — 기본 색상 (기본: #8B5CF6)
 *   animDuration: number    — 애니메이션 시간 초 (기본: 1.5)
 */
export const DataBar: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const bars: Array<{ label: string; value: number; color?: string }> =
    params.bars || [
      { label: "A", value: 95 },
      { label: "B", value: 60 },
      { label: "C", value: 35 },
      { label: "D", value: 5 },
    ];
  const maxValue: number = params.maxValue || 100;
  const orientation: string = params.orientation || "horizontal";
  const style: string = params.style || "bar";
  const showLabels: boolean = params.showLabels !== false;
  const showValues: boolean = params.showValues !== false;
  const defaultColor: string = params.color || "#8B5CF6";
  const animDuration: number = params.animDuration || 1.5;

  const animFrames = animDuration * fps;

  if (style === "ring") {
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
        }}
      >
        {bars.map((bar, i) => {
          const delay = i * fps * 0.3;
          const progress = interpolate(
            frame - delay,
            [0, animFrames],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          const eased = 1 - Math.pow(1 - progress, 3);
          const ratio = (bar.value / maxValue) * eased;
          const radius = 120 + i * 70;
          const circumference = 2 * Math.PI * radius;
          const strokeDash = circumference * ratio;
          const color = bar.color || defaultColor;
          const pulseRadius = radius + audio.bass * 5;

          // 값 표시 위치
          const valueAngle = ratio * Math.PI * 2 - Math.PI / 2;
          const valueX = width / 2 + Math.cos(valueAngle) * pulseRadius;
          const valueY = height / 2 + Math.sin(valueAngle) * pulseRadius;

          return (
            <React.Fragment key={i}>
              {/* 배경 링 */}
              <svg
                style={{ position: "absolute", top: 0, left: 0 }}
                width={width}
                height={height}
              >
                <circle
                  cx={width / 2}
                  cy={height / 2}
                  r={pulseRadius}
                  fill="none"
                  stroke="rgba(255,255,255,0.06)"
                  strokeWidth={18}
                />
                <circle
                  cx={width / 2}
                  cy={height / 2}
                  r={pulseRadius}
                  fill="none"
                  stroke={color}
                  strokeWidth={18}
                  strokeDasharray={`${strokeDash} ${circumference}`}
                  strokeDashoffset={0}
                  strokeLinecap="round"
                  transform={`rotate(-90 ${width / 2} ${height / 2})`}
                  style={{
                    filter: `drop-shadow(0 0 ${6 + audio.rms * 15}px ${color})`,
                  }}
                />
              </svg>
              {/* 값/라벨 */}
              {showValues && eased > 0.5 && (
                <div
                  style={{
                    position: "absolute",
                    left: valueX - 30,
                    top: valueY - 12,
                    fontSize: 20,
                    fontWeight: 700,
                    color,
                    fontFamily: "'Courier New', monospace",
                    opacity: interpolate(eased, [0.5, 0.8], [0, 1], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                    }),
                    textShadow: `0 0 8px ${color}`,
                  }}
                >
                  {Math.round(bar.value * eased)}
                  {showLabels && (
                    <span style={{ fontSize: 14, opacity: 0.6, marginLeft: 4 }}>
                      {bar.label}
                    </span>
                  )}
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  }

  // === 기본 바 차트 (horizontal / vertical) ===
  const barGap = 20;
  const barAreaWidth = width * 0.7;
  const barAreaHeight = height * 0.5;
  const barThickness =
    orientation === "horizontal"
      ? (barAreaHeight - barGap * (bars.length - 1)) / bars.length
      : (barAreaWidth - barGap * (bars.length - 1)) / bars.length;

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
      }}
    >
      <div
        style={{
          width: barAreaWidth,
          height: barAreaHeight,
          position: "relative",
        }}
      >
        {bars.map((bar, i) => {
          const delay = i * fps * 0.2;
          const progress = interpolate(
            frame - delay,
            [0, animFrames],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
          const ratio = (bar.value / maxValue) * eased;
          const color = bar.color || defaultColor;

          // 오디오 리액티브 떨림
          const audioShake = audio.bass * 3;

          if (orientation === "horizontal") {
            const y = i * (barThickness + barGap);
            const barWidth = ratio * barAreaWidth + audioShake;

            return (
              <div key={i} style={{ position: "absolute", top: y, left: 0 }}>
                {/* 배경 트랙 */}
                <div
                  style={{
                    width: barAreaWidth,
                    height: barThickness,
                    backgroundColor: "rgba(255,255,255,0.04)",
                    borderRadius: barThickness / 2,
                  }}
                />
                {/* 값 바 */}
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: Math.max(barWidth, 0),
                    height: barThickness,
                    backgroundColor: color,
                    borderRadius: barThickness / 2,
                    boxShadow: `0 0 ${10 + audio.rms * 20}px ${color}60`,
                  }}
                />
                {/* 라벨 */}
                {showLabels && (
                  <div
                    style={{
                      position: "absolute",
                      top: barThickness / 2 - 10,
                      left: 12,
                      fontSize: 18,
                      fontWeight: 600,
                      color: "rgba(255,255,255,0.9)",
                      fontFamily: "Pretendard Variable, sans-serif",
                      opacity: eased,
                    }}
                  >
                    {bar.label}
                  </div>
                )}
                {/* 값 */}
                {showValues && eased > 0.3 && (
                  <div
                    style={{
                      position: "absolute",
                      top: barThickness / 2 - 12,
                      left: Math.max(barWidth + 10, 80),
                      fontSize: 22,
                      fontWeight: 800,
                      color,
                      fontFamily: "'Courier New', monospace",
                      opacity: interpolate(eased, [0.3, 0.6], [0, 1], {
                        extrapolateLeft: "clamp",
                        extrapolateRight: "clamp",
                      }),
                      textShadow: `0 0 6px ${color}`,
                    }}
                  >
                    {Math.round(bar.value * eased)}
                  </div>
                )}
              </div>
            );
          }

          // vertical
          const x = i * (barThickness + barGap);
          const barHeight = ratio * barAreaHeight + audioShake;

          return (
            <div key={i} style={{ position: "absolute", bottom: 0, left: x }}>
              {/* 배경 */}
              <div
                style={{
                  width: barThickness,
                  height: barAreaHeight,
                  backgroundColor: "rgba(255,255,255,0.04)",
                  borderRadius: barThickness / 2,
                }}
              />
              {/* 바 */}
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  left: 0,
                  width: barThickness,
                  height: Math.max(barHeight, 0),
                  backgroundColor: color,
                  borderRadius: barThickness / 2,
                  boxShadow: `0 0 ${10 + audio.rms * 20}px ${color}60`,
                }}
              />
              {/* 값 */}
              {showValues && eased > 0.3 && (
                <div
                  style={{
                    position: "absolute",
                    bottom: Math.max(barHeight + 8, 30),
                    left: barThickness / 2,
                    transform: "translateX(-50%)",
                    fontSize: 20,
                    fontWeight: 800,
                    color,
                    fontFamily: "'Courier New', monospace",
                    textShadow: `0 0 6px ${color}`,
                  }}
                >
                  {Math.round(bar.value * eased)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
