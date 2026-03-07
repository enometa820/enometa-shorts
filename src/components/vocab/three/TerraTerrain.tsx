import React, { useMemo, useRef, useEffect } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { VocabComponentProps } from "../../../types";
import { ThreeVocabWrapper } from "./ThreeVocabWrapper";

function seededRand(seed: number): number {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

// 결정론적 하이트맵 (사인파 조합)
function terrainHeight(x: number, z: number, time: number): number {
  return (
    Math.sin(x * 1.5 + time * 0.3) * 0.3 +
    Math.sin(z * 2.1 + time * 0.2) * 0.2 +
    Math.sin((x + z) * 0.8 + time * 0.5) * 0.15 +
    Math.sin(x * 3.7 - z * 1.3) * 0.1
  );
}

interface BarData {
  gridX: number;
  gridZ: number;
  maxHeight: number;
  seed: number;
}

const TerrainMesh: React.FC<{
  segments: number;
  heightScale: number;
  terrainColor: string;
  frame: number;
  fps: number;
  audio: VocabComponentProps["audio"];
  rotationY: number;
}> = ({ segments, heightScale, terrainColor, frame, fps, audio, rotationY }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const time = frame / fps;

  // 지형 정점 업데이트
  useEffect(() => {
    if (!meshRef.current) return;
    const geometry = meshRef.current.geometry as THREE.PlaneGeometry;
    const positions = geometry.attributes.position;
    const colors = new Float32Array(positions.count * 3);

    const bassWave = audio.bass * 0.3;

    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const z = positions.getY(i); // PlaneGeometry의 Y가 우리의 Z

      // 높이 계산 (오디오 리액티브 + 시간 기반)
      const h =
        terrainHeight(x, z, time) * heightScale * (1 + bassWave) +
        Math.sin(x * 2 + frame * 0.05) * audio.rms * 0.2;

      positions.setZ(i, h);

      // 높이 기반 색상 (90년대 flat shading 감성)
      const normalizedH = (h / heightScale + 1) * 0.5;
      const baseColor = new THREE.Color(terrainColor);
      const r = baseColor.r * (0.3 + normalizedH * 0.7);
      const g = baseColor.g * (0.3 + normalizedH * 0.7);
      const b = baseColor.b * (0.3 + normalizedH * 0.7);
      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }

    positions.needsUpdate = true;
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geometry.computeVertexNormals();
  }, [frame, heightScale, terrainColor, time, audio, fps]);

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 3, 0, rotationY]} position={[0, -0.5, 0]}>
      <planeGeometry args={[6, 6, segments, segments]} />
      <meshStandardMaterial
        flatShading
        vertexColors
        transparent
        opacity={0.85}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
};

export const TerraTerrain: React.FC<VocabComponentProps> = ({
  segments = 12,
  heightScale = 0.8,
  barCount = 8,
  terrainColor = "#00ccaa",
  barColor = "#ff6644",
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

  const showBars = vocab === "terra_terrain_bars";
  const rotationY = frame * 0.01;

  // 데이터 바 위치 (결정론적)
  const bars = useMemo(() => {
    const b: BarData[] = [];
    for (let i = 0; i < barCount; i++) {
      b.push({
        gridX: (seededRand(i * 7 + 1) - 0.5) * 4,
        gridZ: (seededRand(i * 13 + 3) - 0.5) * 4,
        maxHeight: 0.3 + seededRand(i * 23 + 5) * 1.2,
        seed: i,
      });
    }
    return b;
  }, [barCount]);

  // 바 점진적 등장
  const visibleBars = Math.floor(sceneProgress * barCount);

  return (
    <ThreeVocabWrapper width={width} height={height}>
      {/* 지형 메시 */}
      <TerrainMesh
        segments={segments}
        heightScale={heightScale}
        terrainColor={terrainColor}
        frame={frame}
        fps={fps}
        audio={audio}
        rotationY={rotationY}
      />

      {/* 와이어프레임 그리드 오버레이 */}
      <mesh rotation={[-Math.PI / 3, 0, rotationY]} position={[0, -0.48, 0]}>
        <planeGeometry args={[6, 6, segments, segments]} />
        <meshBasicMaterial
          color={terrainColor}
          wireframe
          transparent
          opacity={0.15 + audio.rms * 0.1}
        />
      </mesh>

      {/* 데이터 바 (terra_terrain_bars 모드) */}
      {showBars &&
        bars.slice(0, visibleBars).map((bar, i) => {
          // stagger 등장: sceneProgress 기반
          const barProgress = Math.min(
            1,
            (sceneProgress - i / barCount) * barCount,
          );
          if (barProgress <= 0) return null;

          const currentHeight =
            bar.maxHeight * barProgress * (1 + audio.rms * 0.3);
          const pulse = audio.onset ? 1.3 : 1;

          // 지형 위에 바 배치 (회전 적용)
          const cos = Math.cos(rotationY);
          const sin = Math.sin(rotationY);
          const rx = bar.gridX * cos - bar.gridZ * sin;
          const rz = bar.gridX * sin + bar.gridZ * cos;

          return (
            <mesh
              key={i}
              position={[rx * 0.7, currentHeight * 0.5 - 0.3, rz * 0.5 - 1]}
              scale={[0.12 * pulse, currentHeight, 0.12 * pulse]}
            >
              <boxGeometry args={[1, 1, 1]} />
              <meshStandardMaterial
                color={audio.onset ? "#ffffff" : barColor}
                flatShading
                transparent
                opacity={0.8}
              />
            </mesh>
          );
        })}
    </ThreeVocabWrapper>
  );
};
