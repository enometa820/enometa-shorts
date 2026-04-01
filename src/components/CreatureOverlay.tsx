/**
 * ENOMETA ASCII 크리처 오버레이
 * PostProcess와 같은 "always-on" 패턴 — 에피소드 전체 정체성으로 상주
 *
 * 위치: VisualSection 우하단 코너 마스코트
 * 렌더 순서: Vocab 오버레이 위, PostProcess 아래
 */

import React, { useRef, useEffect, useMemo } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { CreatureConfig } from "../types";
import { AudioFrame } from "../hooks/useAudioData";
import { renderCreature, CreatureEmotion } from "./creature/CreatureRenderer";

interface CreatureOverlayProps {
  creature: CreatureConfig;
  audio: AudioFrame;
  sceneProgress: number;
  emotion: string;  // Scene.emotion 값
  parentWidth: number;
  parentHeight: number;
}

// Scene emotion 문자열 → CreatureEmotion 변환
function mapEmotion(sceneEmotion: string): CreatureEmotion {
  if (sceneEmotion.startsWith("tension")) return "tension";
  if (sceneEmotion.startsWith("awakening")) return "awakening";
  if (sceneEmotion.startsWith("somber")) return "somber";
  if (sceneEmotion === "hopeful" || sceneEmotion === "transcendent_open") return "hopeful";
  return "neutral";
}

// 크리처 캔버스 크기 — 중앙 강조 마스코트
const CREATURE_W = 500;
const CREATURE_H = 520;

export const CreatureOverlay: React.FC<CreatureOverlayProps> = ({
  creature,
  audio,
  sceneProgress,
  emotion,
  parentWidth,
  parentHeight,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const creatureEmotion = useMemo(() => mapEmotion(emotion), [emotion]);

  // bass에 따른 미세 위치 드리프트 (±8px)
  const driftX = audio.bass * creature.expressiveness * 6;
  const driftY = Math.sin(frame * 0.03) * 5;

  // 중앙 배치
  const posX = (parentWidth - CREATURE_W) / 2 + driftX;
  const posY = (parentHeight - CREATURE_H) / 2 + driftY;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    renderCreature({
      ctx,
      config: creature,
      frame,
      audio,
      sceneProgress,
      emotion: creatureEmotion,
      canvasWidth: CREATURE_W,
      canvasHeight: CREATURE_H,
    });
  }, [frame, audio, sceneProgress, creatureEmotion, creature]);

  return (
    <canvas
      ref={canvasRef}
      width={CREATURE_W}
      height={CREATURE_H}
      style={{
        position: "absolute",
        left: posX,
        top: posY,
        imageRendering: "pixelated",
        zIndex: 8,
        // 중앙 강조 — 약간의 반투명 배경으로 비주얼 레이어와 분리
        background: "rgba(0, 0, 0, 0.45)",
        borderRadius: 4,
      }}
    />
  );
};
