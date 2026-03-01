import React from "react";
import { Composition } from "remotion";
import { EnometaShorts } from "./EnometaShorts";
import {
  ep001VisualScript,
  ep001Title,
  ep001AudioAnalysis,
  ep001AudioSrc,
  ep001NarrationSegments,
} from "./ep001Script";

export const Root: React.FC = () => {
  return (
    <>
      {/* 프로토타입 (테스트 스크립트) */}
      <Composition
        id="EnometaShorts"
        component={EnometaShorts}
        durationInFrames={30 * 30}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{}}
      />

      {/* EP001: 당신의 뇌는 어제를 복사하고 있다 */}
      <Composition
        id="EP001"
        component={EnometaShorts}
        durationInFrames={2734}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          visualScript: ep001VisualScript,
          title: ep001Title,
          audioAnalysis: ep001AudioAnalysis,
          audioSrc: ep001AudioSrc,
          narrationSegments: ep001NarrationSegments,
          highlightWords: ["뇌", "복사"],
        }}
      />
    </>
  );
};
