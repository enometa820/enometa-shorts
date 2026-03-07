import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { VocabComponentProps } from "../../../types";

interface ThreeVocabWrapperProps {
  width: number;
  height: number;
  children: React.ReactNode;
}

export const ThreeVocabWrapper: React.FC<ThreeVocabWrapperProps> = ({
  width,
  height,
  children,
}) => {
  return (
    <ThreeCanvas
      width={width}
      height={height}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        zIndex: 3,
      }}
      gl={{ alpha: true }}
      camera={{ position: [0, 0, 5], fov: 60 }}
    >
      <ambientLight intensity={0.3} />
      <directionalLight position={[5, 5, 5]} intensity={0.6} />
      {children}
    </ThreeCanvas>
  );
};
