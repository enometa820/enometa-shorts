/**
 * PythonFrameBackground.tsx
 * Python 비주얼 엔진이 생성한 프레임 시퀀스(PNG)를 배경으로 표시.
 * Hybrid Visual Architecture — Remotion이 이 컴포넌트를 배경으로 사용.
 */
import React from "react";
import { Img, useCurrentFrame, staticFile } from "remotion";

interface PythonFrameBackgroundProps {
  framesDir: string; // staticFile 기준 상대 경로 (예: "episodes/ep005/frames")
  width: number;
  height: number;
  totalFrames: number;
}

export const PythonFrameBackground: React.FC<PythonFrameBackgroundProps> = ({
  framesDir,
  width,
  height,
  totalFrames,
}) => {
  const frame = useCurrentFrame();
  const clampedFrame = Math.min(frame, totalFrames - 1);
  const padded = String(clampedFrame).padStart(6, "0");
  const src = staticFile(`${framesDir}/${padded}.png`);

  return (
    <Img
      src={src}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width,
        height,
        objectFit: "cover",
      }}
    />
  );
};
