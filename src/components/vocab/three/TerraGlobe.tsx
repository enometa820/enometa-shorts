import React, { useMemo } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import * as THREE from "three";
import { VocabComponentProps } from "../../../types";
import { ThreeVocabWrapper } from "./ThreeVocabWrapper";

// 결정론적 시드 기반 난수 (Math.random 금지)
function seededRand(seed: number): number {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

// 위도/경도 → 직교 좌표 변환
function latLonToXYZ(
  lat: number,
  lon: number,
  radius: number,
): [number, number, number] {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return [
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  ];
}

export const TerraGlobe: React.FC<VocabComponentProps> = ({
  dataPoints = 12,
  wireColor = "#00ffcc",
  dotColor = "#ff3366",
  rotationSpeed = 0.015,
  detail = 2,
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

  const showData = vocab === "terra_globe_data";
  const radius = 1.8;

  // 오디오 리액티브
  const rmsBreath = 1 + audio.rms * 0.08;
  const bassRotation = audio.bass * 0.02;
  const rotationY = frame * rotationSpeed + bassRotation * frame;

  // 데이터 포인트 위치 (결정론적)
  const points = useMemo(() => {
    const pts: { pos: [number, number, number]; seed: number }[] = [];
    for (let i = 0; i < dataPoints; i++) {
      const lat = seededRand(i * 7 + 1) * 140 - 70; // -70 ~ 70
      const lon = seededRand(i * 13 + 3) * 360 - 180;
      pts.push({
        pos: latLonToXYZ(lat, lon, radius * 1.02),
        seed: i,
      });
    }
    return pts;
  }, [dataPoints, radius]);

  // sceneProgress에 따른 점진적 등장
  const visibleCount = Math.floor(sceneProgress * dataPoints);

  // 와이어프레임 색상
  const wireMaterial = useMemo(
    () =>
      new THREE.MeshBasicMaterial({
        color: wireColor,
        wireframe: true,
        transparent: true,
        opacity: 0.6 + audio.rms * 0.3,
      }),
    [wireColor, audio.rms],
  );

  return (
    <ThreeVocabWrapper width={width} height={height}>
      {/* 메인 와이어프레임 구체 */}
      <mesh
        rotation={[0.3, rotationY, 0.1]}
        scale={[rmsBreath, rmsBreath, rmsBreath]}
      >
        <icosahedronGeometry args={[radius, detail]} />
        <meshBasicMaterial
          color={wireColor}
          wireframe
          transparent
          opacity={0.6 + audio.rms * 0.3}
        />
      </mesh>

      {/* 내부 솔리드 구체 (어두운 코어) */}
      <mesh
        rotation={[0.3, rotationY, 0.1]}
        scale={[rmsBreath * 0.98, rmsBreath * 0.98, rmsBreath * 0.98]}
      >
        <icosahedronGeometry args={[radius, detail]} />
        <meshStandardMaterial
          color="#0a0a0a"
          flatShading
          transparent
          opacity={0.4}
        />
      </mesh>

      {/* 데이터 포인트 (terra_globe_data 모드) */}
      {showData &&
        points.slice(0, visibleCount).map((pt, i) => {
          const pulse = audio.onset
            ? 1.5
            : 1 + Math.sin(frame * 0.1 + pt.seed) * 0.3;
          const pointScale = 0.04 * pulse;

          return (
            <mesh
              key={i}
              position={pt.pos}
              rotation={[0.3, rotationY, 0.1]}
              scale={[pointScale, pointScale, pointScale]}
            >
              <sphereGeometry args={[1, 6, 6]} />
              <meshBasicMaterial
                color={audio.onset ? "#ffffff" : dotColor}
              />
            </mesh>
          );
        })}

      {/* 적도 링 */}
      <mesh rotation={[Math.PI / 2, 0, rotationY]}>
        <torusGeometry args={[radius * rmsBreath * 1.01, 0.005, 8, 64]} />
        <meshBasicMaterial color={wireColor} transparent opacity={0.3} />
      </mesh>
    </ThreeVocabWrapper>
  );
};
