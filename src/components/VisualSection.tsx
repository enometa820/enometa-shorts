import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { AudioFrame } from "../hooks/useAudioData";
import { Scene, VocabComponentProps, VisualScriptMeta } from "../types";
import { PythonFrameBackground } from "./PythonFrameBackground";

// 비주얼 어휘 컴포넌트 임포트
import { ParticleBirth } from "./vocab/ParticleBirth";
import { ParticleScatter } from "./vocab/ParticleScatter";
import { ParticleConverge } from "./vocab/ParticleConverge";
import { ParticleOrbit } from "./vocab/ParticleOrbit";
import { ParticleEscape } from "./vocab/ParticleEscape";
import { ParticleChainAwaken } from "./vocab/ParticleChainAwaken";
import { ParticleSplitRatio } from "./vocab/ParticleSplitRatio";
import { FlowField } from "./vocab/FlowField";
import { CounterUp } from "./vocab/CounterUp";
import { ColorShift } from "./vocab/ColorShift";
import { BrightnessPulse } from "./vocab/BrightnessPulse";
import { NeuralNetwork } from "./vocab/NeuralNetwork";
import { LoopRing } from "./vocab/LoopRing";
import { FractalCrack } from "./vocab/FractalCrack";
import { LightSource } from "./vocab/LightSource";
import { PostProcess } from "./vocab/PostProcess";
import { TextReveal } from "./vocab/TextReveal";
import { DataBar } from "./vocab/DataBar";
import { GridMorph } from "./vocab/GridMorph";
import { WaveformVisualizer } from "./vocab/WaveformVisualizer";
import { PixelGrid } from "./vocab/PixelGrid";
import { PixelWaveform } from "./vocab/PixelWaveform";
import { Lissajous } from "./vocab/Lissajous";
import { SymbolMotion } from "./vocab/SymbolMotion";
import { AsciiArt } from "./vocab/AsciiArt";
import { TerraGlobe } from "./vocab/three/TerraGlobe";
import { TerraFlythrough } from "./vocab/three/TerraFlythrough";
import { TerraTerrain } from "./vocab/three/TerraTerrain";

// 비주얼 어휘 → 컴포넌트 매핑
const VOCAB_MAP: Record<string, React.FC<VocabComponentProps>> = {
  particle_birth: ParticleBirth,
  particle_scatter: ParticleScatter,
  particle_converge: ParticleConverge,
  particle_orbit: ParticleOrbit,
  particle_escape: ParticleEscape,
  particle_chain_awaken: ParticleChainAwaken,
  particle_split_ratio: ParticleSplitRatio,
  flow_field_calm: FlowField,
  flow_field_turbulent: FlowField,
  counter_up: CounterUp,
  color_shift: ColorShift,
  color_shift_warm: ColorShift,
  color_shift_cold: ColorShift,
  color_drain: ColorShift,
  color_bloom: ColorShift,
  brightness_pulse: BrightnessPulse,
  neural_network: NeuralNetwork,
  loop_ring: LoopRing,
  fractal_crack: FractalCrack,
  light_source: LightSource,
  // 타이포그래피 + 데이터 시각화 + Max Cooper 스타일
  text_reveal: TextReveal,
  text_wave: TextReveal,
  text_glitch: TextReveal,
  text_scatter: TextReveal,
  data_bar: DataBar,
  data_ring: DataBar,
  grid_morph: GridMorph,
  grid_mesh: GridMorph,
  waveform: WaveformVisualizer,
  waveform_spectrum: WaveformVisualizer,
  waveform_circular: WaveformVisualizer,
  // 8bit / 레트로 비주얼
  pixel_grid: PixelGrid,
  pixel_grid_outline: PixelGrid,
  pixel_grid_life: PixelGrid,
  pixel_grid_rain: PixelGrid,
  pixel_waveform: PixelWaveform,
  pixel_waveform_steps: PixelWaveform,
  pixel_waveform_cascade: PixelWaveform,
  // 수학적 패턴
  lissajous: Lissajous,
  lissajous_complex: Lissajous,
  // 품사 기반 추상 도형
  symbol_morph: SymbolMotion,
  // ASCII 아트
  ascii_block: AsciiArt,
  ascii_shape: AsciiArt,
  ascii_matrix: AsciiArt,
  // 3D / Terra Vision (90년대 CGI)
  terra_globe: TerraGlobe,
  terra_globe_data: TerraGlobe,
  terra_flythrough: TerraFlythrough,
  terra_tunnel: TerraFlythrough,
  terra_terrain: TerraTerrain,
  terra_terrain_bars: TerraTerrain,
};

interface VisualSectionProps {
  scenes: Scene[];
  audio: AudioFrame;
  bgColor: string;
  meta?: VisualScriptMeta;
}

export const VisualSection: React.FC<VisualSectionProps> = ({
  scenes,
  audio,
  bgColor,
  meta,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const SIZE = 1080;

  // ── 방어 코드: frames_dir / total_frames 미설정 시 에러 표시 ──
  if (!meta?.frames_dir || !meta?.total_frames) {
    return (
      <div
        style={{
          width: SIZE,
          height: SIZE,
          background: "#000",
          color: "#f00",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 24,
          fontFamily: "monospace",
        }}
      >
        <span>⚠ frames_dir / total_frames 미설정 — hybrid 렌더링 불가</span>
      </div>
    );
  }

  // ── Hybrid 모드: Python 프레임 배경 + Vocab 오버레이 + PostProcess ──
  const activeScene = scenes.find(
    (s) => currentTime >= s.start_sec && currentTime < s.end_sec,
  );

  const sceneProgress = activeScene
    ? (currentTime - activeScene.start_sec) /
      (activeScene.end_sec - activeScene.start_sec)
    : 0;

  return (
    <div
      style={{
        width: SIZE,
        height: SIZE,
        position: "relative",
        overflow: "hidden",
        background: bgColor,
      }}
    >
      {/* Python 렌더 배경 (데이터 비주얼) */}
      <PythonFrameBackground
        framesDir={meta.frames_dir}
        width={SIZE}
        height={SIZE}
        totalFrames={meta.total_frames}
      />

      {/* Vocab 시맨틱 오버레이 (모션그래픽) */}
      {activeScene?.layers.semantic.map((vocabEntry, i) => {
        const Component = VOCAB_MAP[vocabEntry.vocab];
        if (!Component) return null;

        return (
          <Component
            key={`${activeScene.id}-${vocabEntry.vocab}-${i}`}
            {...vocabEntry.params}
            vocab={vocabEntry.vocab}
            variant={vocabEntry.variant}
            audio={audio}
            audioReactive={activeScene.layers.audio_reactive}
            sceneProgress={sceneProgress}
            frame={frame}
            fps={fps}
            width={SIZE}
            height={SIZE}
          />
        );
      })}

      {/* 포스트프로세싱 오버레이 */}
      <PostProcess audio={audio} width={SIZE} height={SIZE} />
    </div>
  );
};
