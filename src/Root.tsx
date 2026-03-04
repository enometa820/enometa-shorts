import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
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
import {
  ep006VisualScript,
  ep006Title,
  ep006AudioAnalysis,
  ep006AudioSrc,
  ep006NarrationSegments,
} from "./ep006Script";
import {
  ep007VisualScript,
  ep007Title,
  ep007AudioAnalysis,
  ep007AudioSrc,
  ep007NarrationSegments,
} from "./ep007Script";
import {
  ep008VisualScript,
  ep008Title,
  ep008AudioAnalysis,
  ep008AudioSrc,
  ep008NarrationSegments,
} from "./ep008Script";

// calculateMetadata: audioAnalysis.duration_sec 기반 durationInFrames 자동 계산
// endcardDurationSec 기본 6초 포함
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const calcMeta: CalculateMetadataFunction<any> = async ({ props }) => {
  const durationSec = props.audioAnalysis?.duration_sec ?? 120;
  const endcardSec = props.endcardDurationSec ?? 6;
  return {
    durationInFrames: Math.ceil((durationSec + endcardSec) * 30),
  };
};

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
        calculateMetadata={calcMeta}
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
      <Composition
        id="EP002"
        component={EnometaShorts}
        durationInFrames={4222}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
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
      <Composition
        id="EP003"
        component={EnometaShorts}
        durationInFrames={3066}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
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
      <Composition
        id="EP004"
        component={EnometaShorts}
        durationInFrames={2982}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
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
      <Composition
        id="EP005"
        component={EnometaShorts}
        durationInFrames={3888}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
        defaultProps={{
          visualScript: ep005VisualScript,
          title: ep005Title,
          audioAnalysis: ep005AudioAnalysis,
          audioSrc: ep005AudioSrc,
          narrationSegments: ep005NarrationSegments,
          highlightWords: ["화학식"],
        }}
      />
      {/* EP007: 알고리즘은 쌓지 않는다. 덜어낸다 */}
      <Composition
        id="EP007"
        component={EnometaShorts}
        durationInFrames={4170}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
        defaultProps={{
          visualScript: ep007VisualScript,
          title: ep007Title,
          audioAnalysis: ep007AudioAnalysis,
          audioSrc: ep007AudioSrc,
          narrationSegments: ep007NarrationSegments,
          highlightWords: ["탐색", "덜어낸다"],
        }}
      />

      {/* EP008: 질서는 안정에서 오지 않았다 */}
      <Composition
        id="EP008"
        component={EnometaShorts}
        durationInFrames={3999}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
        defaultProps={{
          visualScript: ep008VisualScript,
          title: ep008Title,
          audioAnalysis: ep008AudioAnalysis,
          audioSrc: ep008AudioSrc,
          narrationSegments: ep008NarrationSegments,
          highlightWords: ["혼돈", "연료", "창조"],
        }}
      />

      {/* EP006: 틀리면서 닿는다. 그게 삶이다 */}
      <Composition
        id="EP006"
        component={EnometaShorts}
        durationInFrames={3520}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
        defaultProps={{
          visualScript: ep006VisualScript,
          title: ep006Title,
          audioAnalysis: ep006AudioAnalysis,
          audioSrc: ep006AudioSrc,
          narrationSegments: ep006NarrationSegments,
          highlightWords: ["닿는다"],
        }}
      />
    </>
  );
};
