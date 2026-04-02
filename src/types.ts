import { AudioFrame } from "./hooks/useAudioData";

// 비주얼 어휘 파라미터 — 각 어휘별로 다른 params를 가질 수 있음
export type VocabParams = Record<string, any>;

// 오디오 리액티브 설정
export type AudioReactiveConfig = Record<string, any>;

// 씬 내 비주얼 어휘 항목
export interface VocabEntry {
  vocab: string;
  params: VocabParams;
  variant?: string;
}

// 배경 설정
export interface BackgroundConfig {
  vocab: string;
  params: VocabParams;
  variant?: string;
  transition_to?: string;
}

// 씬 레이어
export interface SceneLayers {
  semantic: VocabEntry[];
  audio_reactive: AudioReactiveConfig;
  background?: BackgroundConfig;
}

// ShapeMotion 파라미터 (B-6: visual_script에서 수신)
export interface ShapeParams {
  speed?: number;   // 속도 배율 (기본: 1.0)
  scale?: number;   // 크기 배율 (기본: 1.0)
  count?: number;   // 요소 개수 배율 (기본: 1)
}

// 씬 정의
export interface Scene {
  id: string;
  sentence: string;
  start_sec: number;
  end_sec: number;
  emotion: string;
  layers: SceneLayers;
  shape_params?: ShapeParams;       // B-6: ShapeMotion 파라미터 오버라이드
  creature_species?: string;        // 씬별 크리처 종 오버라이드 (없으면 글로벌 species 사용)
}

// 전환 설정
export interface TransitionConfig {
  type: string;
  duration_sec?: number;
  note?: string;
}

// 나레이션 세그먼트 (문장 단위 자막 타이밍)
export interface NarrationSegment {
  index: number;
  text: string;
  start_sec: number;
  end_sec: number;
  duration_sec: number;
}

// 비주얼 스크립트 메타 정보 (생성기가 출력)
export interface VisualScriptMeta {
  render_mode?: "hybrid";
  frames_dir?: string;
  total_frames?: number;
  strategy?: string;
  genre?: string;
  palette?: string;
  seed?: number;
}

// ASCII 크리처 설정 — Fuggler(어글리토이) × ASCII 동물 × 글리치 데이터 생명체
export interface CreatureTeeth {
  char: string;
  offset: number;
  scale: number;
}

export interface CreatureConfig {
  // 11종 픽셀아트 스프라이트 (public/creatures/{id}.png)
  species: "cat" | "dog" | "fox" | "frog" | "jellyfish"
         | "mouse" | "duck" | "bird" | "bee" | "squirrel" | "dolphin"
         | string; // 하위호환 (구 종족명은 cat으로 폴백)
  body_color: string;
  accent_color: string;
  body_width: number;
  body_height: number;
  fill_char: string;
  head_scale: number;
  eyes: {
    left_char: string;
    right_char: string;
    left_scale: number;
    right_scale: number;
  };
  ears: {
    left_type: string;
    right_type: string;
  };
  mouth: {
    char: string;
    teeth?: CreatureTeeth[];
  };
  limbs: Array<{
    type: string;
    length: number;
    side: "left" | "right";
  }>;
  tail: string | null;
  glitch: {
    rate: number;
    chars: string[];
  };
  idle_animation: "breathe" | "wobble" | "twitch" | "vibrate";
  blink_rate: number;
  expressiveness: number;
  // 레거시 필드 (하위호환)
  ascii_lines?: string[];
  eye_positions?: { left: [number, number]; right: [number, number] };
  mouth_position?: [number, number];
}

// 비주얼 스크립트 전체 구조
export interface VisualScript {
  global: {
    color_palette: string[];
    background_color: string;
    particle_total: number;
    font: string;
    palette?: string;
  };
  meta?: VisualScriptMeta;
  creature?: CreatureConfig;
  scenes: Scene[];
  transitions?: Record<string, TransitionConfig>;
}

// 비주얼 어휘 컴포넌트의 공통 props
export interface VocabComponentProps {
  audio: AudioFrame;
  audioReactive: AudioReactiveConfig;
  sceneProgress: number;
  frame: number;
  fps: number;
  width: number;
  height: number;
  [key: string]: any;
}
