import React from "react";
import { interpolate, spring } from "remotion";
import { VocabComponentProps } from "../../types";

/**
 * AsciiArt — ASCII 아트 모션그래픽
 *
 * 3가지 모드로 "데이터가 곧 비주얼" 철학을 텍스트 문자로 표현.
 *
 * params:
 *   text: string        — 키워드 (block/matrix 모드에서 사용)
 *   mode: string        — block | shape | matrix
 *   posType: string     — noun | verb | adjective | science | philosophy (shape 모드용)
 *   color: string       — 기본 색상
 *   glowColor: string   — 글로우 색상
 *   position: string    — center | top | upper | bottom
 *   density: string     — low | medium | high (matrix 모드 밀도)
 */

// 결정론적 해시 기반 랜덤
function seededRand(seed: number): number {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}

// ── 5x7 비트맵 폰트 (A-Z, 0-9) ──────────────────────
// 각 문자를 5열 × 7행 비트맵으로 정의 — block 모드에서 키워드를 ASCII 블록으로 렌더링
const BITMAP_FONT: Record<string, number[]> = {
  A: [0x04, 0x0A, 0x11, 0x1F, 0x11, 0x11, 0x11],
  B: [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E],
  C: [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E],
  D: [0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E],
  E: [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F],
  F: [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10],
  G: [0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F],
  H: [0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11],
  I: [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E],
  J: [0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C],
  K: [0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11],
  L: [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F],
  M: [0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11],
  N: [0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11],
  O: [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
  P: [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10],
  Q: [0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D],
  R: [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11],
  S: [0x0E, 0x11, 0x10, 0x0E, 0x01, 0x11, 0x0E],
  T: [0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04],
  U: [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
  V: [0x11, 0x11, 0x11, 0x11, 0x0A, 0x0A, 0x04],
  W: [0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11],
  X: [0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11],
  Y: [0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04],
  Z: [0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F],
  "0": [0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E],
  "1": [0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E],
  "2": [0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F],
  "3": [0x0E, 0x11, 0x01, 0x06, 0x01, 0x11, 0x0E],
  "4": [0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02],
  "5": [0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E],
  "6": [0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E],
  "7": [0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08],
  "8": [0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E],
  "9": [0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C],
};

// 한글 키워드 → 영어 fallback 사전 (ascii_text 파라미터 미지정 시 사용)
// 주된 번역은 파이프라인에서 Claude가 ascii_text 파라미터로 삽입
const KO_TO_EN_FALLBACK: Record<string, string> = {
  "코드": "CODE", "데이터": "DATA", "시간": "TIME", "뇌": "BRAIN",
  "숫자": "NUM", "패턴": "PTRN", "신호": "SIGNAL", "세포": "CELL",
  "존재": "EXIST", "진화": "EVOLVE", "생명": "LIFE", "자연": "NATURE",
};

// ascii_text 파라미터 → KO_TO_EN fallback → 원문 순으로 결정
function resolveAsciiText(text: string, asciiText?: string): string {
  if (asciiText) return asciiText.toUpperCase();
  if (KO_TO_EN_FALLBACK[text]) return KO_TO_EN_FALLBACK[text];
  if (/^[A-Za-z0-9]+$/.test(text)) return text.toUpperCase();
  return text;
}

// 블록 문자 세트 — 밀도에 따라 선택
const BLOCK_CHARS = ["█", "▓", "▒", "░"];
const DATA_CHARS = "01█▓▒░╔╗╚╝║═├┤┬┴┼─│".split("");

// ── Block 모드: 키워드를 비트맵 블록 문자로 렌더링 ──────

const BlockMode: React.FC<{
  text: string;
  asciiText?: string;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
  width: number;
  sceneProgress: number;
}> = ({ text, asciiText, color, glowColor, frame, fps, rms, bass, onset, width }) => {
  // ascii_text 파라미터 → fallback 사전 → 원문 순으로 결정
  const upperText = resolveAsciiText(text, asciiText);
  const isLatin = /^[A-Z0-9]+$/.test(upperText);

  if (isLatin && upperText.length <= 5) {
    // 비트맵 렌더링: 각 문자를 5x7 그리드로 표시 (v2: 크기 2배)
    const charSpacing = 1;
    const totalCols = upperText.length * (5 + charSpacing) - charSpacing;
    const cellSize = Math.min(Math.floor((width * 0.85) / totalCols), 42);

    // 프레임별 점진적 등장
    const totalCells = totalCols * 7;
    const revealProgress = interpolate(frame, [0, fps * 1.2], [0, 1], {
      extrapolateRight: "clamp",
      extrapolateLeft: "clamp",
    });
    const revealedCells = Math.floor(revealProgress * totalCells);

    const rows: React.ReactNode[] = [];
    let cellIndex = 0;

    for (let row = 0; row < 7; row++) {
      const rowChars: React.ReactNode[] = [];
      let colOffset = 0;

      for (let ci = 0; ci < upperText.length; ci++) {
        const bitmap = BITMAP_FONT[upperText[ci]];
        if (!bitmap) {
          colOffset += 5 + charSpacing;
          cellIndex += 5;
          continue;
        }

        for (let col = 4; col >= 0; col--) {
          const isOn = (bitmap[row] >> col) & 1;
          const isCellRevealed = cellIndex < revealedCells;
          cellIndex++;

          // 글리치: onset 시 60% 셀 깜빡임 (강화: 0.3→0.6)
          const glitchSeed = frame * 31 + row * 7 + colOffset + col;
          const isGlitched = onset && seededRand(glitchSeed) < 0.6;

          // 블록 문자 선택: rms에 따라 밀도 변화
          const blockIdx = isGlitched
            ? Math.floor(seededRand(glitchSeed + 1) * 4)
            : Math.floor((1 - rms) * 2);
          const blockChar = isOn && isCellRevealed
            ? (isGlitched ? DATA_CHARS[Math.floor(seededRand(glitchSeed + 2) * DATA_CHARS.length)] : BLOCK_CHARS[blockIdx])
            : " ";

          rowChars.push(
            <span
              key={`${ci}-${col}`}
              style={{
                width: cellSize,
                height: cellSize * 1.6,
                display: "inline-flex",
                justifyContent: "center",
                alignItems: "center",
                fontSize: cellSize * 1.2,
                color: isGlitched ? glowColor : color,
                opacity: isCellRevealed ? (isOn ? 0.9 : 0.05) : 0,
                textShadow: isOn && isCellRevealed
                  ? `0 0 ${8 + rms * 20}px ${glowColor}, 0 0 ${16 + rms * 30}px ${glowColor}40`
                  : "none",
              }}
            >
              {blockChar}
            </span>
          );
          colOffset++;
        }

        // 문자 간 간격
        if (ci < upperText.length - 1) {
          for (let s = 0; s < charSpacing; s++) {
            rowChars.push(
              <span key={`sp-${ci}-${s}`} style={{ width: cellSize, display: "inline-block" }}>
                {" "}
              </span>
            );
            colOffset++;
          }
        }
      }

      rows.push(
        <div key={row} style={{ display: "flex", justifyContent: "center", lineHeight: 1 }}>
          {rowChars}
        </div>
      );
    }

    return <div style={{ fontFamily: "'Courier New', monospace" }}>{rows}</div>;
  }

  // 한글 fallback: 큰 글자를 블록 문자 배경으로 표현
  const charReveal = interpolate(frame, [0, fps * 0.8], [0, text.length], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  return (
    <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
      {text.split("").map((char, i) => {
        const isRevealed = i < charReveal;
        const glitchSeed = frame * 17 + i * 53;
        const isGlitched = onset && seededRand(glitchSeed) < 0.6;
        // 배경: 작은 블록 문자 패턴
        const bgPattern = Array.from({ length: 6 }, (_, row) =>
          Array.from({ length: 4 }, (_, col) => {
            const seed = i * 100 + row * 10 + col;
            return seededRand(seed + frame * 0.01) > 0.5 ? "█" : "░";
          }).join("")
        ).join("\n");

        return (
          <div
            key={i}
            style={{
              position: "relative",
              width: 120,
              height: 140,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              opacity: isRevealed ? 1 : 0,
              transform: `scale(${isRevealed ? 1 : 0.5})`,
            }}
          >
            {/* 블록 문자 배경 */}
            <pre
              style={{
                position: "absolute",
                fontFamily: "'Courier New', monospace",
                fontSize: 12,
                color: color,
                opacity: 0.15 + rms * 0.15,
                margin: 0,
                lineHeight: 1.2,
                textAlign: "center",
              }}
            >
              {bgPattern}
            </pre>
            {/* 전경 문자 */}
            <span
              style={{
                fontFamily: "Pretendard Variable, sans-serif",
                fontSize: 80,
                fontWeight: 900,
                color: isGlitched ? glowColor : color,
                textShadow: `0 0 ${12 + rms * 25}px ${glowColor}, 0 0 ${20 + rms * 35}px ${glowColor}40`,
                zIndex: 1,
              }}
            >
              {char}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ── Shape 모드: 품사별 ASCII 아트 패턴 ──────

const ASCII_SHAPES: Record<string, string[]> = {
  noun: [
    "  ╔══════╗  ",
    "  ║ ◆◆◆◆ ║  ",
    "  ║ ◆  ◆ ║  ",
    "  ║ ◆◆◆◆ ║  ",
    "  ║ ◆  ◆ ║  ",
    "  ║ ◆  ◆ ║  ",
    "  ╚══════╝  ",
  ],
  verb: [
    "            ►",
    "     ──────► ",
    "   ════════► ",
    "  ═══════════►",
    "   ════════► ",
    "     ──────► ",
    "            ►",
  ],
  adjective: [
    " ～～～～～～～ ",
    "～  ～  ～  ～",
    "  ～  ～  ～  ",
    "～  ～  ～  ～",
    "  ～  ～  ～  ",
    "～  ～  ～  ～",
    " ～～～～～～～ ",
  ],
  science: [
    "   ┌─┬─┬─┐   ",
    "   ├─┼─┼─┤   ",
    "   ├─┼─┼─┤   ",
    "   ├─╬═╬─┤   ",
    "   ├─┼─┼─┤   ",
    "   ├─┼─┼─┤   ",
    "   └─┴─┴─┘   ",
  ],
  philosophy: [
    "    ○     ●    ",
    "   ○ ○   ● ●   ",
    "  ○   ○ ●   ●  ",
    "   ○ ○ ● ●   ",
    "    ○ ● ●    ",
    "   ● ● ○ ○   ",
    "    ●     ○    ",
  ],
};

const ShapeMode: React.FC<{
  posType: string;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
  sceneProgress: number;
}> = ({ posType, color, glowColor, frame, fps, rms, bass, onset, sceneProgress }) => {
  const shape = ASCII_SHAPES[posType] || ASCII_SHAPES.noun;
  const totalChars = shape.reduce((sum, line) => sum + line.length, 0);

  // 타이프라이터 등장
  const revealProgress = interpolate(frame, [0, fps * 1.5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const revealedChars = Math.floor(revealProgress * totalChars);

  // 호흡 스케일 (강화: 0.03→0.08, rms 연동)
  const breathe = 1 + Math.sin(frame * 0.05) * 0.08 + rms * 0.08;
  // onset 시 전체 플래시 (강화: 0.3→0.5)
  const flashOpacity = onset ? 0.5 : 0;

  let charCount = 0;

  return (
    <div
      style={{
        fontFamily: "'Courier New', monospace",
        fontSize: 36 + bass * 16,
        lineHeight: 1.3,
        transform: `scale(${breathe})`,
        position: "relative",
      }}
    >
      {/* onset 플래시 배경 */}
      {flashOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            inset: -20,
            backgroundColor: glowColor,
            opacity: flashOpacity,
            borderRadius: 8,
          }}
        />
      )}
      {shape.map((line, lineIdx) => (
        <div key={lineIdx} style={{ whiteSpace: "pre", textAlign: "center" }}>
          {line.split("").map((char, ci) => {
            const isRevealed = charCount < revealedChars;
            charCount++;
            const isSpecial = char !== " ";
            const glitchSeed = frame * 23 + lineIdx * 11 + ci;
            const isGlitched = onset && isSpecial && seededRand(glitchSeed) < 0.55;

            return (
              <span
                key={ci}
                style={{
                  color: isGlitched
                    ? ["#FF0040", "#00FF80", "#FFD700"][Math.floor(seededRand(glitchSeed + 1) * 3)]
                    : color,
                  opacity: isRevealed ? (isSpecial ? 0.9 : 0.1) : 0,
                  textShadow: isSpecial && isRevealed
                    ? `0 0 ${8 + rms * 18}px ${glowColor}, 0 0 ${14 + rms * 25}px ${glowColor}40`
                    : "none",
                }}
              >
                {isRevealed ? char : " "}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// ── Pattern 모드: 키워드별 ASCII 아트 패턴 (v22) ──────

const PatternMode: React.FC<{
  patternGrid: string[];
  patternId: string;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
  sceneProgress: number;
}> = ({ patternGrid, patternId, color, glowColor, frame, fps, rms, onset, sceneProgress }) => {
  if (!patternGrid || patternGrid.length === 0) {
    return null;
  }

  const totalChars = patternGrid.reduce((sum, line) => sum + line.length, 0);

  // 행 단위 타이프라이터 reveal
  const revealProgress = interpolate(frame, [0, fps * 1.2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const revealedRows = Math.ceil(revealProgress * patternGrid.length);

  // 호흡 스케일 (강화)
  const breathe = 1 + Math.sin(frame * 0.05) * 0.06 + rms * 0.06;
  // onset 시 글리치 (강화: 0.25→0.45)
  const flashOpacity = onset ? 0.45 : 0;
  // rms 기반 glow 강도 (강화)
  const glowIntensity = 10 + rms * 25;

  // 퇴장
  const exitOpacity = interpolate(sceneProgress, [0.85, 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        fontFamily: "'Courier New', monospace",
        fontSize: 36,
        lineHeight: 1.3,
        transform: `scale(${breathe})`,
        position: "relative",
        opacity: exitOpacity,
      }}
    >
      {/* onset 플래시 배경 */}
      {flashOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            inset: -16,
            backgroundColor: glowColor,
            opacity: flashOpacity,
            borderRadius: 8,
          }}
        />
      )}
      {patternGrid.map((line, lineIdx) => {
        const isRowRevealed = lineIdx < revealedRows;
        // 행별 등장 딜레이
        const rowDelay = lineIdx * 3;
        const rowOpacity = interpolate(frame - rowDelay, [0, fps * 0.3], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        return (
          <div
            key={lineIdx}
            style={{
              whiteSpace: "pre",
              textAlign: "center",
              opacity: isRowRevealed ? rowOpacity : 0,
            }}
          >
            {line.split("").map((char, ci) => {
              const isSpecial = char !== " ";
              const glitchSeed = frame * 29 + lineIdx * 13 + ci + (patternId.charCodeAt(0) || 0);
              const isGlitched = onset && isSpecial && seededRand(glitchSeed) < 0.5;
              // onset 글리치: 랜덤 문자로 교체
              const displayChar = isGlitched
                ? DATA_CHARS[Math.floor(seededRand(glitchSeed + 1) * DATA_CHARS.length)]
                : char;

              return (
                <span
                  key={ci}
                  style={{
                    color: isGlitched
                      ? ["#FF0040", "#00FF80", "#FFD700"][Math.floor(seededRand(glitchSeed + 2) * 3)]
                      : color,
                    opacity: isSpecial ? 0.9 : 0.05,
                    textShadow: isSpecial
                      ? `0 0 ${glowIntensity}px ${glowColor}`
                      : "none",
                  }}
                >
                  {displayChar}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

// ── Matrix 모드: 터미널 스타일 데이터 스트림 ──────

const MatrixMode: React.FC<{
  text: string;
  color: string;
  glowColor: string;
  frame: number;
  fps: number;
  rms: number;
  bass: number;
  onset: boolean;
  density: string;
  width: number;
  sceneProgress: number;
}> = ({ text, color, glowColor, frame, fps, rms, bass, onset, density, width, sceneProgress }) => {
  const lineCount = density === "high" ? 10 : density === "low" ? 5 : 8;
  const charsPerLine = Math.floor(width / 26);

  // 스크롤 오프셋
  const scrollSpeed = 0.15 + rms * 0.1;
  const scrollOffset = frame * scrollSpeed;

  // 키워드 강조 행 (중앙 부근)
  const highlightLine = Math.floor(lineCount / 2);

  const lines: React.ReactNode[] = [];

  for (let i = 0; i < lineCount; i++) {
    const lineSeed = (i + Math.floor(scrollOffset)) * 137;
    const isHighlightLine = i === highlightLine;
    const lineOpacity = isHighlightLine ? 1 : 0.5 + seededRand(lineSeed + 99) * 0.35;

    // 각 행의 문자열 생성
    const lineChars: React.ReactNode[] = [];

    if (isHighlightLine) {
      // 키워드 행: "> keyword_" 형식 + 커서 깜빡임
      const prefix = ">> ";
      const suffix = " <<";
      const padding = Math.max(0, charsPerLine - prefix.length - text.length - suffix.length);
      const leftPad = Math.floor(padding / 2);
      const fillChar = onset ? "█" : "─";

      const fullLine = fillChar.repeat(leftPad) + prefix + text + suffix + fillChar.repeat(padding - leftPad);

      for (let c = 0; c < Math.min(fullLine.length, charsPerLine); c++) {
        const ch = fullLine[c];
        const isKeyword = c >= leftPad + prefix.length && c < leftPad + prefix.length + text.length;
        lineChars.push(
          <span
            key={c}
            style={{
              color: isKeyword ? glowColor : color,
              fontWeight: isKeyword ? 900 : "normal",
              fontSize: isKeyword ? "1.25em" : undefined,
              textShadow: isKeyword
                ? `0 0 ${14 + rms * 25}px ${glowColor}, 0 0 ${25 + rms * 40}px ${glowColor}40`
                : "none",
              opacity: isKeyword ? 1 : 0.7,
            }}
          >
            {ch}
          </span>
        );
      }
    } else {
      // 데이터 행: 랜덤 ASCII 데이터
      for (let c = 0; c < charsPerLine; c++) {
        const charSeed = lineSeed + c * 7 + Math.floor(frame * 0.3);
        const charIdx = Math.floor(seededRand(charSeed) * DATA_CHARS.length);
        const isActive = seededRand(charSeed + 50) > 0.7;

        lineChars.push(
          <span
            key={c}
            style={{
              color: isActive ? color : color,
              opacity: isActive ? lineOpacity : lineOpacity * 0.5,
              textShadow: isActive
                ? `0 0 ${6 + rms * 14}px ${glowColor}80`
                : "none",
            }}
          >
            {DATA_CHARS[charIdx]}
          </span>
        );
      }
    }

    lines.push(
      <div
        key={i}
        style={{
          whiteSpace: "pre",
          lineHeight: 1.4,
          opacity: interpolate(
            frame,
            [i * 2, i * 2 + fps * 0.3],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      >
        {lineChars}
      </div>
    );
  }

  // 퇴장
  const exitOpacity = interpolate(sceneProgress, [0.85, 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        fontFamily: "'Courier New', monospace",
        fontSize: 34,
        opacity: exitOpacity,
        padding: "16px 20px",
        backgroundColor: "rgba(0, 0, 0, 0.4)",
        borderRadius: 6,
        border: `1px solid ${color}40`,
        maxWidth: width * 0.92,
      }}
    >
      {/* 터미널 헤더 */}
      <div
        style={{
          fontSize: 14,
          color: color,
          opacity: 0.5,
          marginBottom: 8,
          borderBottom: `1px solid ${color}30`,
          paddingBottom: 6,
        }}
      >
        ┌─ ENOMETA DATA STREAM ─ {text} ─┐
      </div>
      {lines}
    </div>
  );
};

// ── 메인 컴포넌트 ──────────────────────────────────────

export const AsciiArt: React.FC<VocabComponentProps> = ({
  audio,
  sceneProgress,
  frame,
  fps,
  width,
  height,
  ...params
}) => {
  const text: string = params.text || "DATA";
  const asciiText: string | undefined = params.ascii_text || undefined;
  const mode: string = params.mode || "block";
  const posType: string = params.posType || "noun";
  const color: string = params.color || "#00FF80";
  const glowColor: string = params.glowColor || "#00FF80";
  const position: string = params.position || "center";
  const density: string = params.density || "medium";
  const patternGrid: string[] | undefined = params.patternGrid;
  const patternId: string = params.patternId || "";

  const posY =
    position === "top" ? height * 0.15 :
    position === "upper" ? height * 0.32 :
    position === "bottom" ? height * 0.62 :
    height * 0.42;

  // 입장 애니메이션
  const enterProgress = spring({
    frame,
    fps,
    config: { damping: 25, stiffness: 100 },
  });
  const enterOpacity = interpolate(enterProgress, [0, 1], [0, 1]);

  // 퇴장
  const exitOpacity = interpolate(sceneProgress, [0.85, 1], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const opacity = enterOpacity * exitOpacity;

  const sharedProps = {
    color,
    glowColor,
    frame,
    fps,
    rms: audio.rms,
    bass: audio.bass,
    onset: audio.onset,
    sceneProgress,
  };

  const renderMode = () => {
    switch (mode) {
      case "pattern":
        return patternGrid
          ? <PatternMode {...sharedProps} patternGrid={patternGrid} patternId={patternId} />
          : <BlockMode {...sharedProps} text={text} asciiText={asciiText} width={width} />;
      case "block":
        return <BlockMode {...sharedProps} text={text} asciiText={asciiText} width={width} />;
      case "shape":
        return <ShapeMode {...sharedProps} posType={posType} />;
      case "matrix":
        return <MatrixMode {...sharedProps} text={text} density={density} width={width} />;
      default:
        return <BlockMode {...sharedProps} text={text} asciiText={asciiText} width={width} />;
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
          opacity,
        }}
      >
        {renderMode()}
      </div>
    </div>
  );
};
