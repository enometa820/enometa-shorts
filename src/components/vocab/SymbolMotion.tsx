import React from "react";
import { interpolate, spring } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * SymbolMotion — 품사 기반 ASCII 아트 그리드 (v2: 백남준 미학)
 *
 * SVG 추상 도형 → 대형 ASCII 캐릭터 그리드로 전면 교체.
 * 각 POS 타입마다 고유한 문자셋+패턴으로 화면을 채운다.
 * 오디오 리액티브: onset→글리치, rms→밀도, bass→스케일
 *
 * params:
 *   text: string        — 원본 키워드 (그리드 중앙에 강조 삽입)
 *   posType: string     — noun | verb | adjective | science | philosophy
 *   shapeColor: string  — 기본 색상
 *   glowColor: string   — 글로우/강조 색상
 *   position: string    — center | top | upper | bottom
 */

// 결정론적 해시 기반 랜덤
function seededRand(seed: number): number {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}

// POS별 문자 집합
const POS_CHARSETS: Record<string, { fill: string; accent: string }> = {
  noun: { fill: "█▓▒░◆◇■□●○", accent: "◆●█" },
  verb: { fill: "►▶→═──»>⟩⟫", accent: "►▶═" },
  adjective: { fill: "～∿≈≋⌇∾~≈～∿", accent: "～∿≈" },
  science: { fill: "┼─│├┤┬┴╬═║", accent: "╬╋┼" },
  philosophy: { fill: "○●◐◑◒◓◔◕⊕⊖", accent: "●○◐" },
  data: { fill: "01{}<>[]():;", accent: "{}01" },
  chemical: { fill: "⬡⬢△▽◇◆⊿∆∇⊕", accent: "⬡⬢⊕" },
  adverb: { fill: "～∿→⟩»›>⇒⟶⟹", accent: "→⟩»" },
};

const GLITCH_CHARS = "█▓▒░╬╋┼@#$%&!?■◆";
const GLITCH_COLORS = ["#FF0040", "#00FF80", "#FFD700", "#00BFFF"];

// ── 그리드 셀 타입 ──────────────────────────────────────

interface GridCell {
  char: string;
  intensity: number;
  isAccent: boolean;
  isKeyword: boolean;
}

// ── POS별 패턴 생성기 ──────────────────────────────────

function genNoun(
  r: number, c: number, rows: number, cols: number,
  frame: number, rms: number, charset: { fill: string; accent: string },
): GridCell {
  // 밀도 기반 블록: 중앙이 밀집, 외곽은 희박
  const distR = Math.abs(r - rows / 2) / (rows / 2);
  const distC = Math.abs(c - cols / 2) / (cols / 2);
  const dist = Math.sqrt(distR * distR + distC * distC);
  const threshold = 0.45 + rms * 0.2;
  const timeSeed = r * cols + c + Math.floor(frame * 0.2);

  if (dist < threshold) {
    const idx = Math.floor(seededRand(timeSeed) * charset.fill.length);
    return {
      char: charset.fill[idx],
      intensity: 1.0 - dist * 0.6,
      isAccent: seededRand(r * 31 + c * 17) < 0.12,
      isKeyword: false,
    };
  }
  return {
    char: seededRand(timeSeed) < 0.06 ? "·" : " ",
    intensity: 0.15,
    isAccent: false,
    isKeyword: false,
  };
}

function genVerb(
  r: number, c: number, rows: number, cols: number,
  frame: number, rms: number, charset: { fill: string; accent: string },
): GridCell {
  // 왼→오 흐름 + 속도감
  const flowPhase = ((c / cols) + frame * 0.025) % 1;
  const rowDist = Math.abs(r - rows / 2) / (rows / 2);
  const flowIntensity = Math.sin(flowPhase * Math.PI) * (0.6 + rms * 0.4) * (1 - rowDist * 0.7);
  const timeSeed = r * cols + c + Math.floor(frame * 0.15);

  if (flowIntensity > 0.25) {
    const idx = Math.floor(seededRand(timeSeed) * charset.fill.length);
    return {
      char: charset.fill[idx],
      intensity: flowIntensity,
      isAccent: c % 5 === Math.floor(frame * 0.2) % 5,
      isKeyword: false,
    };
  }
  return { char: " ", intensity: 0, isAccent: false, isKeyword: false };
}

function genAdjective(
  r: number, c: number, rows: number, cols: number,
  frame: number, rms: number, bass: number, charset: { fill: string; accent: string },
): GridCell {
  // 사인파 물결: 여러 겹
  const waveY = Math.sin(c * 0.25 + frame * 0.06) * (2.5 + bass * 3);
  const wave2 = Math.sin(c * 0.15 + frame * 0.04 + 2) * (1.5 + rms * 2);
  const dist1 = Math.abs(r - rows / 2 - waveY);
  const dist2 = Math.abs(r - rows / 2 - wave2);
  const minDist = Math.min(dist1, dist2);
  const timeSeed = r * cols + c + Math.floor(frame * 0.2);

  if (minDist < 1.8) {
    const idx = Math.floor(seededRand(timeSeed) * charset.fill.length);
    return {
      char: charset.fill[idx],
      intensity: 1.0 - minDist * 0.35,
      isAccent: minDist < 0.5,
      isKeyword: false,
    };
  }
  return { char: " ", intensity: 0, isAccent: false, isKeyword: false };
}

function genScience(
  r: number, c: number, rows: number, cols: number,
  frame: number, rms: number, charset: { fill: string; accent: string },
): GridCell {
  // 데이터 격자: 줄/칸 교차점 강조
  const isGridRow = r % 3 === 0;
  const isGridCol = c % 5 === 0;
  const isNode = isGridRow && isGridCol;
  const timeSeed = r * cols + c + Math.floor(frame * 0.15);

  if (isNode) {
    return {
      char: charset.accent[Math.floor(seededRand(r * 7 + c) * charset.accent.length)],
      intensity: 0.9 + rms * 0.1,
      isAccent: true,
      isKeyword: false,
    };
  }
  if (isGridRow) {
    return { char: "─", intensity: 0.5 + rms * 0.2, isAccent: false, isKeyword: false };
  }
  if (isGridCol) {
    return { char: "│", intensity: 0.5 + rms * 0.2, isAccent: false, isKeyword: false };
  }
  // 빈 공간: rms에 따라 일부 채움
  if (seededRand(timeSeed) < 0.1 + rms * 0.2) {
    const idx = Math.floor(seededRand(timeSeed + 1) * charset.fill.length);
    return { char: charset.fill[idx], intensity: 0.35, isAccent: false, isKeyword: false };
  }
  return { char: " ", intensity: 0, isAccent: false, isKeyword: false };
}

function genPhilosophy(
  r: number, c: number, rows: number, cols: number,
  frame: number, rms: number, bass: number, onset: boolean, charset: { fill: string; accent: string },
): GridCell {
  // 이원성: 좌우 대비
  const mid = cols / 2;
  const boundary = Math.abs(c - mid);
  const timeSeed = r * cols + c + Math.floor(frame * 0.2);

  if (boundary < 1.5) {
    // 경계: 혼합 기호
    return {
      char: onset ? "◐" : (frame % 10 < 5 ? "◑" : "◐"),
      intensity: 0.9,
      isAccent: true,
      isKeyword: false,
    };
  }
  const isLeft = c < mid;
  const pool = isLeft ? "○◌◦·" : "●◉◎•";
  const fillChance = 0.25 + bass * 0.3;

  if (seededRand(timeSeed) < fillChance) {
    return {
      char: pool[Math.floor(seededRand(timeSeed + 1) * pool.length)],
      intensity: 0.55 + rms * 0.35,
      isAccent: false,
      isKeyword: false,
    };
  }
  return { char: " ", intensity: 0, isAccent: false, isKeyword: false };
}

// ── 그리드 생성 ──────────────────────────────────────

function generateGrid(
  posType: string,
  cols: number,
  rows: number,
  frame: number,
  rms: number,
  bass: number,
  onset: boolean,
  keyword: string,
): GridCell[][] {
  const charset = POS_CHARSETS[posType] || POS_CHARSETS.noun;
  const grid: GridCell[][] = [];

  // 키워드 삽입 위치
  const kwRow = Math.floor(rows / 2);
  const kwStart = Math.max(0, Math.floor((cols - keyword.length) / 2));

  for (let r = 0; r < rows; r++) {
    const row: GridCell[] = [];
    for (let c = 0; c < cols; c++) {
      // 키워드 행: 중앙에 키워드 강조
      if (r === kwRow && c >= kwStart && c < kwStart + keyword.length) {
        row.push({
          char: keyword[c - kwStart],
          intensity: 1.0,
          isAccent: false,
          isKeyword: true,
        });
        continue;
      }

      // POS별 패턴 생성
      let cell: GridCell;
      switch (posType) {
        case "noun":
          cell = genNoun(r, c, rows, cols, frame, rms, charset);
          break;
        case "verb":
          cell = genVerb(r, c, rows, cols, frame, rms, charset);
          break;
        case "adjective":
        case "adverb":
          cell = genAdjective(r, c, rows, cols, frame, rms, bass, charset);
          break;
        case "science":
        case "data":
        case "chemical":
          cell = genScience(r, c, rows, cols, frame, rms, charset);
          break;
        case "philosophy":
          cell = genPhilosophy(r, c, rows, cols, frame, rms, bass, onset, charset);
          break;
        default:
          cell = genNoun(r, c, rows, cols, frame, rms, charset);
      }

      // onset 글리치: 40% 확률로 랜덤 문자 교체
      const seed = r * cols + c;
      if (onset && seededRand(frame * 23 + seed) < 0.4 && cell.intensity > 0.2) {
        cell.char = GLITCH_CHARS[Math.floor(seededRand(frame * 11 + seed) * GLITCH_CHARS.length)];
        cell.isAccent = true;
      }

      row.push(cell);
    }
    grid.push(row);
  }

  return grid;
}

// ── 메인 컴포넌트 ──────────────────────────────────────

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

  // 그리드 크기: 큰 텍스트 영역 (기존 120px SVG → 28col×14row 텍스트)
  const fontSize = 32;
  const cols = Math.min(28, Math.floor((width * 0.85) / (fontSize * 0.62)));
  const rows = 14;

  const posY =
    position === "top" ? height * 0.12 :
    position === "upper" ? height * 0.28 :
    position === "bottom" ? height * 0.52 :
    height * 0.32;

  // 입장 애니메이션
  const enterProgress = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 120 },
  });
  const enterScale = interpolate(enterProgress, [0, 1], [0.7, 1]);
  const enterOpacity = interpolate(enterProgress, [0, 1], [0, 1]);

  // 퇴장 (씬 마지막 15%)
  const exitOpacity = interpolate(
    sceneProgress,
    [0.85, 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const opacity = enterOpacity * exitOpacity;

  // 호흡: rms 연동 스케일
  const breathe = 1 + Math.sin(frame * 0.05) * 0.04 + audio.rms * 0.06;

  // 그리드 생성
  const keyword = text.toUpperCase().slice(0, 10);
  const grid = generateGrid(posType, cols, rows, frame, audio.rms, audio.bass, audio.onset, keyword);

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
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: posY,
          transform: `scale(${enterScale * breathe})`,
          opacity,
          fontFamily: "'Courier New', monospace",
          fontSize,
          lineHeight: 1.25,
        }}
      >
        {grid.map((row, ri) => (
          <div key={ri} style={{ whiteSpace: "pre", textAlign: "center" }}>
            {row.map((cell, ci) => {
              if (cell.intensity === 0 && cell.char === " ") {
                return <span key={ci}> </span>;
              }

              const glitchSeed = frame * 13 + ri * 31 + ci;
              const isGlitched = cell.isAccent && audio.onset && seededRand(glitchSeed) < 0.5;

              let cellColor = shapeColor;
              if (cell.isKeyword) {
                cellColor = glowColor;
              } else if (isGlitched) {
                cellColor = GLITCH_COLORS[Math.floor(seededRand(glitchSeed + 1) * GLITCH_COLORS.length)];
              }

              const cellGlow = cell.isKeyword
                ? `0 0 ${12 + audio.rms * 25}px ${glowColor}, 0 0 ${25 + audio.rms * 35}px ${glowColor}40`
                : cell.isAccent
                ? `0 0 ${6 + audio.rms * 15}px ${glowColor}`
                : "none";

              return (
                <span
                  key={ci}
                  style={{
                    color: cellColor,
                    opacity: cell.intensity * (0.7 + audio.rms * 0.3),
                    fontWeight: cell.isKeyword ? 900 : cell.isAccent ? 700 : 400,
                    textShadow: cellGlow,
                    fontSize: cell.isKeyword ? fontSize * 1.3 : undefined,
                  }}
                >
                  {cell.char}
                </span>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};
