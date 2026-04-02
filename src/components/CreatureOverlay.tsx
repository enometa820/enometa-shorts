/**
 * ENOMETA 픽셀아트 크리처 오버레이
 * 16×16 PNG 스프라이트를 nearest-neighbor 업스케일로 렌더
 *
 * 위치: VisualSection 중앙 (500×520 캔버스)
 * 렌더 순서: Vocab 오버레이 위, PostProcess 아래
 */

import React, { useRef, useEffect, useMemo, useState } from "react";
import { useCurrentFrame, delayRender, continueRender, cancelRender, staticFile } from "remotion";
import { CreatureConfig } from "../types";
import { AudioFrame } from "../hooks/useAudioData";
import { renderCreature, CreatureEmotion } from "./creature/CreatureRenderer";

interface CreatureOverlayProps {
  creature: CreatureConfig;
  audio: AudioFrame;
  sceneProgress: number;
  emotion: string;
  parentWidth: number;
  parentHeight: number;
}

// Scene emotion → CreatureEmotion
function mapEmotion(sceneEmotion: string): CreatureEmotion {
  if (sceneEmotion.startsWith("tension")) return "tension";
  if (sceneEmotion.startsWith("awakening")) return "awakening";
  if (sceneEmotion.startsWith("somber")) return "somber";
  if (sceneEmotion === "hopeful" || sceneEmotion === "transcendent_open") return "hopeful";
  return "neutral";
}

// species → 이미지 경로 매핑
function getSpritePath(species: string): string {
  const known = new Set([
    "cat", "dog", "fox", "frog", "jellyfish",
    "mouse", "duck", "bird", "bee", "squirrel", "dolphin",
  ]);
  const id = known.has(species) ? species : "cat";
  return staticFile(`creatures/${id}.png`);
}

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
  const imgRef = useRef<HTMLImageElement | null>(null);

  const [handle] = useState(() => delayRender("Loading creature sprite"));
  const [loaded, setLoaded] = useState(false);

  const creatureEmotion = useMemo(() => mapEmotion(emotion), [emotion]);
  const spritePath = useMemo(() => getSpritePath(creature.species), [creature.species]);

  // 스프라이트 로드
  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      imgRef.current = img;
      setLoaded(true);
      continueRender(handle);
    };
    img.onerror = (e) => {
      cancelRender(new Error(`크리처 스프라이트 로드 실패: ${spritePath}`));
    };
    img.src = spritePath;
  }, [spritePath, handle]);

  // bass에 따른 미세 위치 드리프트
  const driftX = audio.bass * creature.expressiveness * 6;
  const driftY = Math.sin(frame * 0.03) * 5;

  // 중앙 배치
  const posX = (parentWidth  - CREATURE_W) / 2 + driftX;
  const posY = (parentHeight - CREATURE_H) / 2 + driftY;

  useEffect(() => {
    if (!loaded) return;
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
      spriteImage: imgRef.current,
    });
  }, [frame, audio, sceneProgress, creatureEmotion, creature, loaded]);

  if (!loaded) return null;

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
        background: "rgba(0, 0, 0, 0.45)",
        borderRadius: 4,
      }}
    />
  );
};
