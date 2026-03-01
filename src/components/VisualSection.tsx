import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { AudioFrame } from "../hooks/useAudioData";
import { Scene, VocabComponentProps } from "../types";

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
};

interface VisualSectionProps {
  scenes: Scene[];
  audio: AudioFrame;
  bgColor: string;
}

export const VisualSection: React.FC<VisualSectionProps> = ({
  scenes,
  audio,
  bgColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const SIZE = 1080;

  // 현재 시간에 해당하는 씬 찾기
  const activeScene = scenes.find(
    (s) => currentTime >= s.start_sec && currentTime < s.end_sec,
  );

  if (!activeScene) {
    return (
      <div
        style={{
          width: SIZE,
          height: SIZE,
          background: bgColor,
        }}
      />
    );
  }

  // 씬 내 진행도 (0~1)
  const sceneProgress =
    (currentTime - activeScene.start_sec) /
    (activeScene.end_sec - activeScene.start_sec);

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
      {/* 배경 레이어 */}
      {activeScene.layers.background && (() => {
        const bgVocab = activeScene.layers.background.vocab;
        const BgComponent = VOCAB_MAP[bgVocab];
        if (!BgComponent) return null;

        return (
          <BgComponent
            {...activeScene.layers.background.params}
            vocab={bgVocab}
            audio={audio}
            audioReactive={activeScene.layers.audio_reactive}
            sceneProgress={sceneProgress}
            frame={frame}
            fps={fps}
            width={SIZE}
            height={SIZE}
          />
        );
      })()}

      {/* 의미 레이어 — 비주얼 어휘 컴포넌트 렌더링 */}
      {activeScene.layers.semantic.map((vocabEntry, i) => {
        const Component = VOCAB_MAP[vocabEntry.vocab];
        if (!Component) return null;

        return (
          <Component
            key={`${activeScene.id}-${vocabEntry.vocab}-${i}`}
            {...vocabEntry.params}
            vocab={vocabEntry.vocab}
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

      {/* 포스트프로세싱 오버레이 — 모든 씬 위에 비네트/스캔라인/플래시 */}
      <PostProcess audio={audio} width={SIZE} height={SIZE} />
    </div>
  );
};
