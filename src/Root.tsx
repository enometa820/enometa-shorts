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
import {
  ep002VisualScript,
  ep002Title,
  ep002AudioAnalysis,
  ep002AudioSrc,
  ep002NarrationSegments,
} from "./ep002Script";
import {
  ep003VisualScript,
  ep003Title,
  ep003AudioAnalysis,
  ep003AudioSrc,
  ep003NarrationSegments,
} from "./ep003Script";
import {
  ep004VisualScript,
  ep004Title,
  ep004AudioAnalysis,
  ep004AudioSrc,
  ep004NarrationSegments,
} from "./ep004Script";
import {
  ep005VisualScript,
  ep005Title,
  ep005AudioAnalysis,
  ep005AudioSrc,
  ep005NarrationSegments,
} from "./ep005Script";

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
        durationInFrames={2929}
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
      {/* EP002: 당신의 오답이 뇌를 가장 크게 깨운다 */}
      {/* 134.232s + 0.5s 여유 + 6s 엔드카드 = 140.732s × 30fps = 4222 */}
      <Composition
        id="EP002"
        component={EnometaShorts}
        durationInFrames={4222}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          visualScript: ep002VisualScript,
          title: ep002Title,
          audioAnalysis: ep002AudioAnalysis,
          audioSrc: ep002AudioSrc,
          narrationSegments: ep002NarrationSegments,
          highlightWords: ["오답", "설계"],
        }}
      />
      {/* EP003: 우리의 기억은 매번 다시 만들어진다 */}
      {/* 96.186s + 6s 엔드카드 = 102.186s × 30fps = 3066 */}
      <Composition
        id="EP003"
        component={EnometaShorts}
        durationInFrames={3066}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          visualScript: ep003VisualScript,
          title: ep003Title,
          audioAnalysis: ep003AudioAnalysis,
          audioSrc: ep003AudioSrc,
          narrationSegments: ep003NarrationSegments,
          highlightWords: ["기억", "해석"],
        }}
      />
      {/* EP004: 우리의 선택은 몇 번이나 우리의 것이었을까 */}
      {/* 93.37s + 6s 엔드카드 = 99.37s × 30fps = 2982 */}
      <Composition
        id="EP004"
        component={EnometaShorts}
        durationInFrames={2982}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          visualScript: ep004VisualScript,
          title: ep004Title,
          audioAnalysis: ep004AudioAnalysis,
          audioSrc: ep004AudioSrc,
          narrationSegments: ep004NarrationSegments,
          highlightWords: ["선택"],
        }}
      />
      {/* EP005: 공포와 각성의 화학식은 같다 */}
      {/* 123.602s + 6s 엔드카드 = 129.602s × 30fps = 3888 */}
      <Composition
        id="EP005"
        component={EnometaShorts}
        durationInFrames={3888}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          visualScript: ep005VisualScript,
          title: ep005Title,
          audioAnalysis: ep005AudioAnalysis,
          audioSrc: ep005AudioSrc,
          narrationSegments: ep005NarrationSegments,
          highlightWords: ["화학식"],
        }}
      />
    </>
  );
};
