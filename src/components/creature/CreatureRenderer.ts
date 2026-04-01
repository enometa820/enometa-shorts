/**
 * ENOMETA ASCII 크리처 렌더러 v2
 * Fuggler 어글리토이 × ASCII 동물 — 못생겼지만 귀여운
 *
 * 주요 변경:
 * - 큰 캔버스 (500×520), fontSize 22px
 * - 더 알아보기 쉬운 Fuggler 비율 템플릿
 * - 이빨: 입 아래 고정 줄로 명확하게
 * - 눈: 비대칭이지만 귀여운 크기
 */

import { CreatureConfig } from "../../types";
import { AudioFrame } from "../../hooks/useAudioData";

export type CreatureEmotion =
  | "neutral"
  | "tension"
  | "awakening"
  | "somber"
  | "hopeful";

// ─────────────────────────────────────────────
// 종별 ASCII 템플릿
// {L} = 왼눈, {R} = 오른눈, {M} = 입, {TH} = 이빨줄
// {EL} = 왼귀, {ER} = 오른귀
// ─────────────────────────────────────────────

const TEMPLATES: Record<string, string[]> = {
  cat: [
    "  {EL}     {ER}  ",
    " /           \\ ",
    "|  {L}     {R}  |",
    "|      __      |",
    "|   ( {M}  )   |",
    "|   {TH}    |",
    " \\  _______  / ",
    "   |       |   ",
    "  /|       |\\ ",
    " (_)       (_) ",
  ],
  rabbit: [
    "  {EL}   {ER}  ",
    "  |       |   ",
    " /           \\ ",
    "| {L}       {R} |",
    "|      __      |",
    "|   ( {M}  )   |",
    "|   {TH}    |",
    " \\___________/ ",
    "    /     \\   ",
    "   (_)   (_)  ",
  ],
  bear: [
    " ({EL})   ({ER}) ",
    " /           \\ ",
    "|  {L}     {R}  |",
    "|   ~     ~    |",
    "|   ( {M}  )   |",
    "|   {TH}    |",
    " \\___________/ ",
    "  /|       |\\ ",
    " ( |       | ) ",
    "  \\_)     (_/ ",
  ],
  owl: [
    "   /\\_____/\\  ",
    "  /           \\ ",
    " | ({L})   ({R}) |",
    " |    ___      |",
    " |   >{M}<     |",
    " |   {TH}   |",
    "  \\_________/ ",
    "   /|     |\\  ",
    "  V |     | V  ",
    "    |     |    ",
  ],
  dog: [
    "  {EL}       {ER}",
    " /             \\ ",
    "|   {L}     {R}   |",
    "|      __       |",
    "|   ( {M}   )   |",
    "|   {TH}     |",
    " \\___________/ ",
    "   /|     |\\  ",
    "  / |     | \\ ",
    "    |     |    ",
  ],
  blob: [
    "   /~~~~~~~~~\\ ",
    "  /             \\ ",
    " |  {L}       {R}  |",
    " |      __       |",
    " |   ( {M}   )   |",
    " |   {TH}     |",
    "  \\___________/ ",
    "    | |   | |  ",
    "    | |   | |  ",
    "   (_)     (_) ",
  ],
};

// 귀 타입 → 문자 (2char)
const EAR_MAP: Record<string, string> = {
  pointy: "/\\",
  round:  "()",
  long:   "||",
  broken: "/|",
  tiny:   "``",
};

// 이빨 줄 생성 — Fuggler 시그니처: 불규칙 크기 이빨
function buildTeethRow(config: CreatureConfig, width = 10): string {
  if (config.mouth.teeth.length === 0) return " ".repeat(width);
  const slots = Math.min(config.mouth.teeth.length, 6);
  let row = "";
  for (let i = 0; i < slots; i++) {
    const t = config.mouth.teeth[i];
    // 이빨 크기에 따라 다른 문자
    if (t.scale > 1.3) row += "█";
    else if (t.scale > 0.9) row += "▌";
    else row += "▏";
    // 이빨 사이 간격 (불규칙)
    row += t.offset > 1 ? "  " : " ";
  }
  return row.substring(0, width).padEnd(width, " ");
}

// 시드 기반 결정론적 랜덤
function sr(seed: number, i: number): number {
  const x = Math.sin(seed * 9301 + i * 49297 + 233) * 10000;
  return x - Math.floor(x);
}

// 글리치 문자 치환
function maybeGlitch(
  ch: string,
  rate: number,
  glitchChars: string[],
  seed: number,
  idx: number,
  onset: boolean
): string {
  const r = onset ? Math.min(rate * 5, 0.45) : rate;
  if (sr(seed, idx) < r) {
    return glitchChars[Math.floor(sr(seed + 1, idx) * glitchChars.length)] ?? ch;
  }
  return ch;
}

// ─────────────────────────────────────────────
// 템플릿 조립
// ─────────────────────────────────────────────

function assembleLines(
  config: CreatureConfig,
  emotion: CreatureEmotion,
  frame: number,
  audio: AudioFrame
): string[] {
  const tmpl = TEMPLATES[config.species] ?? TEMPLATES.cat;

  // 감정별 눈 문자
  let L = config.eyes.left_char;
  let R = config.eyes.right_char;
  if (emotion === "tension")   { L = "◉"; R = "◉"; }
  if (emotion === "somber")    { L = "."; R = "."; }
  if (emotion === "awakening") { L = "★"; R = "★"; }
  if (emotion === "hopeful")   { L = "◕"; R = "◕"; }

  // 깜빡임
  const blinkPeriod = Math.max(4, Math.round(30 / config.blink_rate));
  if (frame % blinkPeriod < 2) { L = "—"; R = "—"; }

  // 입 — rms 높으면 벌어짐
  let M = config.mouth.char;
  if (audio.rms > 0.55 && emotion !== "somber") M = "D";
  if (emotion === "awakening") M = "D";
  if (emotion === "somber")    M = "_";

  // 귀
  const EL = EAR_MAP[config.ears.left_type]  ?? "/\\";
  const ER = EAR_MAP[config.ears.right_type] ?? "/\\";

  // 이빨 줄
  const TH = buildTeethRow(config, 10);

  // 치환
  return tmpl.map((line) =>
    line
      .replace("{L}", L)
      .replace("{R}", R)
      .replace("{M}", M)
      .replace("{TH}", TH)
      .replace("{EL}", EL)
      .replace("{ER}", ER)
  );
}

// ─────────────────────────────────────────────
// 메인 렌더
// ─────────────────────────────────────────────

export interface RenderCreatureOptions {
  ctx: CanvasRenderingContext2D;
  config: CreatureConfig;
  frame: number;
  audio: AudioFrame;
  sceneProgress: number;
  emotion: CreatureEmotion;
  canvasWidth: number;
  canvasHeight: number;
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
}: RenderCreatureOptions): void {
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  const fontSize = 38;
  const lineH = fontSize * 1.20;
  // neodgm 폰트 (프로젝트에 있으면 사용, 없으면 monospace 폴백)
  ctx.font = `${fontSize}px 'NeoDunggeunmo', 'D2Coding', 'Courier New', monospace`;
  ctx.textBaseline = "top";

  // ── 오디오 리액티브 변환 ──
  const bassScale = 1 + audio.bass * config.expressiveness * 0.07;
  const onsetJolt = audio.onset ? -6 * config.expressiveness : 0;

  // idle 애니메이션
  let idleY = 0;
  if (config.idle_animation === "breathe") {
    idleY = Math.sin(frame * 0.04) * 5;
  } else if (config.idle_animation === "wobble") {
    idleY = Math.sin(frame * 0.10) * 7;
  } else if (config.idle_animation === "twitch") {
    idleY = sr(frame, 7) < 0.06 ? (sr(frame, 8) - 0.5) * 10 : 0;
  } else if (config.idle_animation === "vibrate") {
    idleY = (sr(frame, 9) - 0.5) * 3;
  }

  const lines = assembleLines(config, emotion, frame, audio);
  const totalH = lines.length * lineH;
  const startY = (canvasHeight - totalH) / 2 + idleY + onsetJolt;

  // charWidth 고정 (monospace 기준)
  const charW = fontSize * 0.60;

  // 글리치 시드
  const gSeed = Math.floor(frame / 4);
  const rowShiftSeed = Math.floor(frame / 10);

  ctx.save();
  ctx.translate(canvasWidth / 2, canvasHeight / 2);
  ctx.scale(bassScale, bassScale);
  ctx.translate(-canvasWidth / 2, -canvasHeight / 2);

  lines.forEach((line, rowIdx) => {
    const y = startY + rowIdx * lineH;

    // onset 시 행 밀림 글리치
    let rowX = (canvasWidth - line.length * charW) / 2;
    if (audio.onset && sr(rowShiftSeed, rowIdx * 3) < 0.25) {
      rowX += (sr(rowShiftSeed, rowIdx * 3 + 1) - 0.5) * 12;
    }

    for (let ci = 0; ci < line.length; ci++) {
      const raw = line[ci];
      const ch = maybeGlitch(
        raw, config.glitch.rate, config.glitch.chars,
        gSeed, rowIdx * 200 + ci, audio.onset
      );

      const isGlitch  = config.glitch.chars.includes(ch);
      const isEye     = [config.eyes.left_char, config.eyes.right_char,
                         "◉", "★", "◕", "—", "."].includes(ch);
      const isTooth   = ["█", "▌", "▏"].includes(ch);
      const isOutline = ["/", "\\", "|", "(", ")", "_", "~", "V", ">", "<"].includes(ch);

      // 색상 + glow
      ctx.shadowBlur = 0;
      if (isGlitch) {
        ctx.fillStyle = config.accent_color;
        ctx.shadowColor = config.accent_color;
        ctx.shadowBlur = 8;
      } else if (isEye) {
        ctx.fillStyle = config.body_color;
        ctx.shadowColor = config.body_color;
        ctx.shadowBlur = emotion === "awakening" ? 12 : 4;
      } else if (isTooth) {
        ctx.fillStyle = "#f0e6c8";   // Fuggler 이빨색 (약간 누른)
        ctx.shadowBlur = 0;
      } else if (isOutline) {
        ctx.fillStyle = "rgba(200, 200, 200, 0.9)";
      } else {
        ctx.fillStyle = "rgba(160, 160, 160, 0.7)";
      }

      ctx.fillText(ch, rowX + ci * charW, y);
    }
  });

  ctx.restore();
  ctx.shadowBlur = 0;
}
