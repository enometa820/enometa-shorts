import React from "react";
import { interpolate, spring } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * SymbolMotion — 품사 기반 추상 도형 모션그래픽
 *
 * 대본 키워드의 품사(POS)에 따라 추상 기하학적 도형으로 시각화.
 * TextReveal의 텍스트 대신, 단어의 의미를 도형으로 상징.
 *
 * params:
 *   text: string        — 원본 키워드 (도형 아래 작게 표시)
 *   posType: string     — noun | verb | adjective | science | philosophy (품사 카테고리)
 *   shapeColor: string  — 도형 색상
 *   glowColor: string   — 글로우 색상
 *   position: string    — center | top | upper | bottom
 *   size: number        — 도형 기본 크기 (기본: 120)
 *   showLabel: boolean  — 키워드 텍스트 표시 여부 (기본: true)
 */

// 결정론적 해시 기반 랜덤
function seededRand(seed: number): number {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}

// ── 도형별 렌더러 ──────────────────────────────────────

// 명사: 육각형 — 개념의 존재감, breathing 팽창수축
const HexagonShape: React.FC<{
  size: number;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
}> = ({ size, color, glowColor, frame, fps, rms, bass, onset }) => {
  const breathe = 1 + Math.sin(frame * 0.06) * 0.08 + rms * 0.15;
  const rotate = frame * 0.3;
  const glowSize = 10 + rms * 30;
  const onsetFlash = onset ? 1.15 : 1;

  // 육각형 SVG path
  const r = (size / 2) * breathe * onsetFlash;
  const points = Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 2;
    return `${r * Math.cos(angle)},${r * Math.sin(angle)}`;
  }).join(" ");

  return (
    <svg
      width={size * 1.5}
      height={size * 1.5}
      viewBox={`${-size * 0.75} ${-size * 0.75} ${size * 1.5} ${size * 1.5}`}
      style={{
        transform: `rotate(${rotate}deg)`,
        filter: `drop-shadow(0 0 ${glowSize}px ${glowColor})`,
      }}
    >
      <polygon
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={2.5 + bass * 2}
        opacity={0.85}
      />
      {/* 내부 작은 육각형 — 이중 구조 */}
      <polygon
        points={Array.from({ length: 6 }, (_, i) => {
          const angle = (Math.PI / 3) * i - Math.PI / 2;
          const innerR = r * 0.5;
          return `${innerR * Math.cos(angle)},${innerR * Math.sin(angle)}`;
        }).join(" ")}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        opacity={0.4 + rms * 0.3}
      />
    </svg>
  );
};

// 동사: 화살표 — 행위의 흐름, 방향 이동
const ArrowShape: React.FC<{
  size: number;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
}> = ({ size, color, glowColor, frame, fps, rms, onset }) => {
  const moveX = Math.sin(frame * 0.04) * size * 0.6;
  const stretch = 1 + rms * 0.3;
  const glowSize = 8 + rms * 25;
  const onsetPush = onset ? size * 0.3 : 0;
  const trailOpacity = 0.15 + rms * 0.2;

  return (
    <svg
      width={size * 3}
      height={size}
      viewBox={`0 0 ${size * 3} ${size}`}
      style={{
        filter: `drop-shadow(0 0 ${glowSize}px ${glowColor})`,
      }}
    >
      {/* 이동 궤적 (잔상) */}
      <line
        x1={size * 0.3}
        y1={size / 2}
        x2={size * 1.5 + moveX + onsetPush - size * 0.2}
        y2={size / 2}
        stroke={color}
        strokeWidth={1.5}
        opacity={trailOpacity}
        strokeDasharray="6 4"
      />
      {/* 화살표 본체 */}
      <g
        transform={`translate(${size * 1.5 + moveX + onsetPush}, ${size / 2}) scale(${stretch}, 1)`}
      >
        <line
          x1={-size * 0.4}
          y1={0}
          x2={size * 0.2}
          y2={0}
          stroke={color}
          strokeWidth={3}
          strokeLinecap="round"
        />
        <polygon
          points={`${size * 0.2},0 ${size * 0.05},${-size * 0.12} ${size * 0.05},${size * 0.12}`}
          fill={color}
          opacity={0.9}
        />
      </g>
    </svg>
  );
};

// 형용사: 물결 — 감정의 파장, 진폭 진동
const WaveShape: React.FC<{
  size: number;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
}> = ({ size, color, glowColor, frame, fps, rms, bass, onset }) => {
  const amplitude = 15 + bass * 40 + (onset ? 20 : 0);
  const frequency = 0.03 + rms * 0.02;
  const glowSize = 8 + rms * 20;
  const waveCount = 3;

  return (
    <svg
      width={size * 2.5}
      height={size * 1.2}
      viewBox={`0 0 ${size * 2.5} ${size * 1.2}`}
      style={{
        filter: `drop-shadow(0 0 ${glowSize}px ${glowColor})`,
      }}
    >
      {Array.from({ length: waveCount }, (_, wi) => {
        const yBase = size * 0.3 + wi * size * 0.3;
        const phaseShift = wi * 1.2;
        const waveOpacity = 0.8 - wi * 0.2;
        const points = Array.from({ length: 50 }, (_, xi) => {
          const x = (xi / 49) * size * 2.5;
          const y =
            yBase +
            Math.sin(x * frequency + frame * 0.08 + phaseShift) *
              amplitude *
              (1 - wi * 0.25);
          return `${x},${y}`;
        }).join(" ");

        return (
          <polyline
            key={wi}
            points={points}
            fill="none"
            stroke={color}
            strokeWidth={2.5 - wi * 0.5}
            opacity={waveOpacity}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        );
      })}
    </svg>
  );
};

// science/data: 동심원 격자 — 데이터의 전파, 펄스 확산
const ConcentricShape: React.FC<{
  size: number;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
}> = ({ size, color, glowColor, frame, fps, rms, bass, onset }) => {
  const ringCount = 4;
  const glowSize = 8 + rms * 25;
  const pulsePhase = frame * 0.05;

  return (
    <svg
      width={size * 1.5}
      height={size * 1.5}
      viewBox={`${-size * 0.75} ${-size * 0.75} ${size * 1.5} ${size * 1.5}`}
      style={{
        filter: `drop-shadow(0 0 ${glowSize}px ${glowColor})`,
      }}
    >
      {Array.from({ length: ringCount }, (_, i) => {
        const baseR = ((i + 1) / ringCount) * size * 0.6;
        const pulse = Math.sin(pulsePhase - i * 0.8) * 0.15;
        const r = baseR * (1 + pulse) + (onset ? 8 : 0);
        const ringOpacity = 0.7 - i * 0.12 + rms * 0.2;
        const dashLen = 4 + i * 3;

        return (
          <circle
            key={i}
            cx={0}
            cy={0}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={2 - i * 0.3}
            opacity={Math.max(0.1, ringOpacity)}
            strokeDasharray={i % 2 === 0 ? "none" : `${dashLen} ${dashLen}`}
            strokeDashoffset={frame * (i % 2 === 0 ? 0.5 : -0.5)}
          />
        );
      })}
      {/* 중앙 점 — onset 시 확대 */}
      <circle
        cx={0}
        cy={0}
        r={4 + bass * 6 + (onset ? 8 : 0)}
        fill={color}
        opacity={0.6 + rms * 0.3}
      />
      {/* 십자 마커 */}
      <line x1={-8} y1={0} x2={8} y2={0} stroke={color} strokeWidth={1} opacity={0.4} />
      <line x1={0} y1={-8} x2={0} y2={8} stroke={color} strokeWidth={1} opacity={0.4} />
    </svg>
  );
};

// philosophy: 이중 원 — 개념의 이원성, 회전+분리+합체
const DualCircleShape: React.FC<{
  size: number;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
}> = ({ size, color, glowColor, frame, fps, rms, bass, onset }) => {
  // 두 원이 가까워졌다 멀어지는 호흡
  const separation = Math.sin(frame * 0.03) * size * 0.25;
  const r = size * 0.28 + bass * 10;
  const rotate = frame * 0.4;
  const glowSize = 8 + rms * 20;
  const overlapOpacity = interpolate(
    Math.abs(separation),
    [0, size * 0.2],
    [0.4, 0],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  return (
    <svg
      width={size * 2}
      height={size * 1.5}
      viewBox={`${-size} ${-size * 0.75} ${size * 2} ${size * 1.5}`}
      style={{
        transform: `rotate(${rotate}deg)`,
        filter: `drop-shadow(0 0 ${glowSize}px ${glowColor})`,
      }}
    >
      {/* 왼쪽 원 */}
      <circle
        cx={-separation}
        cy={0}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={2.5}
        opacity={0.75}
      />
      {/* 오른쪽 원 */}
      <circle
        cx={separation}
        cy={0}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={2.5}
        opacity={0.75}
      />
      {/* 교차 영역 강조 */}
      {overlapOpacity > 0.05 && (
        <circle
          cx={0}
          cy={0}
          r={r * 0.3}
          fill={color}
          opacity={overlapOpacity}
        />
      )}
      {/* 연결선 */}
      <line
        x1={-separation - r}
        y1={0}
        x2={separation + r}
        y2={0}
        stroke={color}
        strokeWidth={1}
        opacity={0.2 + rms * 0.2}
        strokeDasharray="3 3"
      />
    </svg>
  );
};

// ── 메인 컴포넌트 ──────────────────────────────────────

const POS_TO_SHAPE: Record<string, string> = {
  noun: "hexagon",
  verb: "arrow",
  adjective: "wave",
  science: "concentric",
  data: "concentric",
  philosophy: "dual",
  chemical: "concentric",
  adverb: "wave",
};

export const SymbolMotion: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const text: string = params.text || "";
  const posType: string = params.posType || "noun";
  const shapeColor: string = params.shapeColor || "#FFFFFF";
  const glowColor: string = params.glowColor || params.shapeColor || "#8B5CF6";
  const position: string = params.position || "center";
  const size: number = params.size || 120;
  const showLabel: boolean = params.showLabel !== false;

  const posY =
    position === "top" ? height * 0.15 :
    position === "upper" ? height * 0.32 :
    position === "bottom" ? height * 0.72 :
    height * 0.45;

  // 입장 애니메이션
  const enterProgress = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 120 },
  });
  const enterScale = interpolate(enterProgress, [0, 1], [0.2, 1]);
  const enterOpacity = interpolate(enterProgress, [0, 1], [0, 1]);

  // 퇴장 (씬 마지막 15%)
  const exitOpacity = interpolate(
    sceneProgress,
    [0.85, 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const opacity = enterOpacity * exitOpacity;

  // 라벨 fade-in (도형 등장 후)
  const labelOpacity = interpolate(frame, [fps * 0.5, fps * 0.8], [0, 0.7], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }) * exitOpacity;

  const shapeType = POS_TO_SHAPE[posType] || "hexagon";

  const shapeProps = {
    size,
    color: shapeColor,
    glowColor,
    frame,
    fps,
    rms: audio.rms,
    bass: audio.bass,
    onset: audio.onset,
  };

  const renderShape = () => {
    switch (shapeType) {
      case "hexagon": return <HexagonShape {...shapeProps} />;
      case "arrow": return <ArrowShape {...shapeProps} />;
      case "wave": return <WaveShape {...shapeProps} />;
      case "concentric": return <ConcentricShape {...shapeProps} />;
      case "dual": return <DualCircleShape {...shapeProps} />;
      default: return <HexagonShape {...shapeProps} />;
    }
  };

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
          position: "absolute",
          top: posY,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
          transform: `scale(${enterScale})`,
          opacity,
        }}
      >
        {renderShape()}
        {showLabel && text && (
          <span
            style={{
              fontFamily: "Pretendard Variable, sans-serif",
              fontSize: 28,
              fontWeight: 600,
              color: shapeColor,
              opacity: labelOpacity,
              letterSpacing: "0.15em",
              textShadow: `0 0 12px ${glowColor}80`,
            }}
          >
            {text}
          </span>
        )}
      </div>
    </div>
  );
};
