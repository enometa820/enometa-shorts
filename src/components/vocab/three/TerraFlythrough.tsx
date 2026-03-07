import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { VocabComponentProps } from "../../../types";
import { ThreeVocabWrapper } from "./ThreeVocabWrapper";

function seededRand(seed: number): number {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

interface RingData {
  baseZ: number;
  scale: number;
  rotationOffset: number;
}

export const TerraFlythrough: React.FC<VocabComponentProps> = ({
  ringCount = 14,
  tunnelLength = 30,
  speed = 0.08,
  ringColor = "#00ffcc",
  shape = "circle" as "circle" | "square" | "hexagon",
  audio,
  sceneProgress,
  frame: _frame,
  fps: _fps,
  width = 1080,
  height = 1080,
  vocab,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isSquare = vocab === "terra_tunnel" || shape === "square";

  // 오디오 리액티브
  const bassSpeed = speed + audio.bass * 0.04;
  const midScale = 1 + audio.mid * 0.3;
  const onsetBurst = audio.onset ? 0.5 : 0;

  // 링 데이터 (결정론적)
  const rings = useMemo(() => {
    const r: RingData[] = [];
    for (let i = 0; i < ringCount; i++) {
      r.push({
        baseZ: (i / ringCount) * tunnelLength,
        scale: 0.8 + seededRand(i * 17) * 0.4,
        rotationOffset: seededRand(i * 31) * Math.PI * 2,
      });
    }
    return r;
  }, [ringCount, tunnelLength]);

  // 프레임 기반 이동 — 링이 카메라 쪽으로 다가옴
  const totalMove = frame * bassSpeed + onsetBurst * frame * 0.01;

  return (
    <ThreeVocabWrapper width={width} height={height}>
      {rings.map((ring, i) => {
        // Z 위치: 무한 터널 (카메라 통과 후 뒤로 재배치)
        let z = ring.baseZ - (totalMove % tunnelLength);
        if (z < -2) z += tunnelLength;

        // 거리에 따른 투명도 (가까울수록 불투명)
        const distRatio = Math.max(0, Math.min(1, z / tunnelLength));
        const opacity = 0.15 + (1 - distRatio) * 0.7 + audio.rms * 0.15;

        // 회전
        const rotation =
          ring.rotationOffset + frame * 0.005 + audio.mid * 0.02;

        // 스케일: 가까울수록 크게 (원근감)
        const perspScale = ring.scale * midScale * (1 + (1 - distRatio) * 0.5);

        // sceneProgress에 따른 점진적 밀도 증가
        const visibleThreshold = sceneProgress * ringCount;
        if (i > visibleThreshold + 3) return null;

        if (isSquare) {
          // 사각형 터널
          return (
            <mesh
              key={i}
              position={[0, 0, -z]}
              rotation={[0, 0, rotation]}
              scale={[perspScale, perspScale, 1]}
            >
              <ringGeometry args={[1.8, 2.0, 4]} />
              <meshBasicMaterial
                color={ringColor}
                wireframe
                transparent
                opacity={opacity}
              />
            </mesh>
          );
        }

        // 원형 터널
        return (
          <mesh
            key={i}
            position={[0, 0, -z]}
            rotation={[0, 0, rotation]}
            scale={[perspScale, perspScale, 1]}
          >
            <torusGeometry args={[2, 0.02, 8, shape === "hexagon" ? 6 : 32]} />
            <meshBasicMaterial
              color={ringColor}
              transparent
              opacity={opacity}
            />
          </mesh>
        );
      })}

      {/* 중심축 가이드 라인 (미세한 깊이감) */}
      {[0, Math.PI / 2, Math.PI, (3 * Math.PI) / 2].map((angle, i) => {
        const lineX = Math.cos(angle) * 0.15;
        const lineY = Math.sin(angle) * 0.15;
        return (
          <mesh key={`guide-${i}`} position={[lineX, lineY, -tunnelLength / 2]}>
            <boxGeometry args={[0.005, 0.005, tunnelLength]} />
            <meshBasicMaterial
              color={ringColor}
              transparent
              opacity={0.08 + audio.rms * 0.05}
            />
          </mesh>
        );
      })}
    </ThreeVocabWrapper>
  );
};
