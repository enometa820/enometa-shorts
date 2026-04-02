/**
 * ENOMETA 픽셀아트 크리처 렌더러 v5
 * 16×16 PNG 스프라이트 → nearest-neighbor 업스케일 → Canvas 렌더
 *
 * 오디오 리액티브: bass scale / onset jolt / glitch pixel scatter
 * 표정: 색상 오버레이 (이미지 교체 없이 emotion→tint로 표현)
 */

import { CreatureConfig } from "../../types";
import { AudioFrame } from "../../hooks/useAudioData";

export type CreatureEmotion =
  | "neutral"
  | "tension"
  | "awakening"
  | "somber"
  | "hopeful";

export interface RenderCreatureOptions {
  ctx: CanvasRenderingContext2D;
  config: CreatureConfig;
  frame: number;
  audio: AudioFrame;
  sceneProgress: number;
  emotion: CreatureEmotion;
  canvasWidth: number;
  canvasHeight: number;
  spriteImage: HTMLImageElement | null;
}

// 시드 기반 결정론적 랜덤
function sr(seed: number, i: number): number {
  const x = Math.sin(seed * 9301 + i * 49297 + 233) * 10000;
  return x - Math.floor(x);
}

// 감정 → 컬러 오버레이 설정
function emotionTint(emotion: CreatureEmotion): { r: number; g: number; b: number; a: number } {
  switch (emotion) {
    case "tension":    return { r: 255, g:  60, b:  40, a: 0.18 }; // 붉은 긴장
    case "awakening":  return { r: 180, g: 255, b:  80, a: 0.15 }; // 밝은 각성
    case "somber":     return { r:  80, g: 120, b: 200, a: 0.20 }; // 파란 우수
    case "hopeful":    return { r: 255, g: 220, b:  80, a: 0.15 }; // 따뜻한 희망
    default:           return { r:   0, g:   0, b:   0, a: 0.00 }; // 중립
  }
}

// 감정 → glow 색상
function emotionGlow(emotion: CreatureEmotion, accentColor: string): string {
  switch (emotion) {
    case "tension":   return "#ff3c28";
    case "awakening": return "#b4ff50";
    case "somber":    return "#5078c8";
    case "hopeful":   return "#ffdc50";
    default:          return accentColor;
  }
}

export function renderCreature({
  ctx,
  config,
  frame,
  audio,
  sceneProgress,
  emotion,
  canvasWidth,
  canvasHeight,
  spriteImage,
}: RenderCreatureOptions): void {
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  if (!spriteImage) return;

  // ── 1. 오디오 리액티브 변환 ──────────────────────────────────
  const bassScale = 1 + audio.bass * config.expressiveness * 0.06;
  const onsetJolt = audio.onset ? -4 * config.expressiveness : 0;

  // idle 애니메이션
  let idleY = 0;
  let idleX = 0;
  if (config.idle_animation === "breathe") {
    idleY = Math.sin(frame * 0.04) * 6;
  } else if (config.idle_animation === "wobble") {
    idleY = Math.sin(frame * 0.10) * 9;
    idleX = Math.cos(frame * 0.07) * 3;
  } else if (config.idle_animation === "twitch") {
    idleY = sr(frame, 7) < 0.06 ? (sr(frame, 8) - 0.5) * 12 : 0;
    idleX = sr(frame, 11) < 0.06 ? (sr(frame, 12) - 0.5) * 6 : 0;
  } else if (config.idle_animation === "vibrate") {
    idleY = (sr(frame, 9) - 0.5) * 4;
    idleX = (sr(frame, 13) - 0.5) * 2;
  }

  // ── 2. 스프라이트 크기 & 위치 ────────────────────────────────
  // 16px → 캔버스에서 큰 픽셀 블록으로 (nearest-neighbor)
  const SCALE = 18;                          // 16×18 = 288px 정사각형
  const spriteW = spriteImage.naturalWidth  * SCALE;
  const spriteH = spriteImage.naturalHeight * SCALE;

  const centerX = canvasWidth  / 2 + idleX;
  const centerY = canvasHeight / 2 + idleY + onsetJolt;

  const drawX = centerX - spriteW / 2;
  const drawY = centerY - spriteH / 2;

  // ── 3. glow 효과 ─────────────────────────────────────────────
  const glowColor = emotionGlow(emotion, config.accent_color ?? "#a855f7");
  const glowSize  = emotion === "awakening" ? 18 : (emotion === "neutral" ? 8 : 12);

  ctx.save();
  ctx.translate(canvasWidth / 2, canvasHeight / 2);
  ctx.scale(bassScale, bassScale);
  ctx.translate(-canvasWidth / 2, -canvasHeight / 2);

  // glow pass (낮은 opacity의 큰 shadow)
  ctx.shadowColor  = glowColor;
  ctx.shadowBlur   = glowSize;
  ctx.imageSmoothingEnabled = false;

  ctx.drawImage(spriteImage, drawX, drawY, spriteW, spriteH);

  // ── 4. 감정 컬러 오버레이 ─────────────────────────────────────
  const tint = emotionTint(emotion);
  if (tint.a > 0) {
    ctx.shadowBlur = 0;
    ctx.globalCompositeOperation = "source-atop";
    ctx.fillStyle = `rgba(${tint.r}, ${tint.g}, ${tint.b}, ${tint.a})`;
    ctx.fillRect(drawX, drawY, spriteW, spriteH);
    ctx.globalCompositeOperation = "source-over";
  }

  ctx.restore();

  // ── 5. onset 글리치: 픽셀 블록 스캐터 ────────────────────────
  if (audio.onset && config.glitch.rate > 0.02) {
    const gSeed = Math.floor(frame / 2);
    const glitchCount = Math.floor(config.glitch.rate * 40);
    const pixSize = SCALE;

    ctx.save();
    ctx.globalAlpha = 0.6;
    for (let i = 0; i < glitchCount; i++) {
      if (sr(gSeed, i * 7) < 0.5) continue;
      // 스프라이트 내 랜덤 픽셀 위치
      const px = Math.floor(sr(gSeed, i * 3)     * spriteImage.naturalWidth)  * SCALE + drawX;
      const py = Math.floor(sr(gSeed, i * 3 + 1) * spriteImage.naturalHeight) * SCALE + drawY;
      const ox = (sr(gSeed, i * 3 + 2) - 0.5) * SCALE * 4;
      const oy = (sr(gSeed, i * 3 + 3) - 0.5) * SCALE * 2;

      ctx.drawImage(
        spriteImage,
        Math.floor(sr(gSeed, i * 3) * spriteImage.naturalWidth),
        Math.floor(sr(gSeed, i * 3 + 1) * spriteImage.naturalHeight),
        1, 1,
        px + ox, py + oy,
        pixSize, pixSize
      );
    }
    ctx.restore();
  }

  // ── 6. 깜빡임: onset 시 전체 flash ───────────────────────────
  if (audio.onset) {
    ctx.save();
    ctx.globalAlpha = 0.15;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    ctx.restore();
  }
}
