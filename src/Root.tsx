import React from "react";
import { Composition, CalculateMetadataFunction, staticFile } from "remotion";
import { EnometaShorts } from "./EnometaShorts";
import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ─── v2: 에피소드 레지스트리 ───────────────────────────────────────────────
// 새 에피소드 추가 방법:
//   1. py scripts/enometa_render.py episodes/epXXX --title "제목" ... 실행
//   2. 아래 EPISODES 배열에 한 줄 추가
//   (데이터 파일은 public/epXXX/ 에 자동 복사됨: mixed.wav + JSON 3종)
// ──────────────────────────────────────────────────────────────────────────

type EpisodeMeta = {
  episodeId: string;  // "ep017"
  title: string;
  highlightWords?: string[];
};

const EPISODES: EpisodeMeta[] = [
  { episodeId: "ep011", title: "뇌는 예측 기계다", highlightWords: ["예측", "뇌", "오류"] },
];

// ─── calculateMetadata: public/<episodeId>/ 에서 JSON 동적 로드 ────────────
const calcMeta: CalculateMetadataFunction<EpisodeMeta & {
  visualScript?: VisualScript;
  audioAnalysis?: AudioAnalysis;
  narrationSegments?: NarrationSegment[];
  audioSrc?: string;
  endcardDurationSec?: number;
}> = async ({ props }) => {
  const { episodeId, title, highlightWords } = props;
  const base = episodeId;

  const [visualScript, audioAnalysis, narrationTiming] = await Promise.all([
    fetch(staticFile(`${base}/visual_script.json`)).then((r) => r.json()),
    fetch(staticFile(`${base}/audio_analysis.json`)).then((r) => r.json()),
    fetch(staticFile(`${base}/narration_timing.json`)).then((r) => r.json()),
  ]);

  const endcardSec = 6;
  const scenes = (visualScript as VisualScript)?.scenes ?? [];
  const lastSceneEnd =
    scenes.length > 0
      ? scenes[scenes.length - 1].end_sec
      : ((audioAnalysis as AudioAnalysis)?.duration_sec ?? 120);
  const endcardStartFrame = Math.round(lastSceneEnd * 30);
  const endcardFrames = Math.round(endcardSec * 30);

  return {
    durationInFrames: endcardStartFrame + endcardFrames,
    props: {
      ...props,
      visualScript: visualScript as VisualScript,
      audioAnalysis: audioAnalysis as AudioAnalysis,
      narrationSegments: (narrationTiming as any)?.segments ?? [],
      audioSrc: `${base}/mixed.wav`,
      title,
      highlightWords: highlightWords ?? [],
      endcardDurationSec: endcardSec,
    },
  };
};

// ─── Root ─────────────────────────────────────────────────────────────────
export const Root: React.FC = () => (
  <>
    {/* 개발/테스트용 기본 Composition */}
    <Composition
      id="EnometaShorts"
      component={EnometaShorts}
      durationInFrames={30 * 30}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{}}
    />

    {/* v2: EPISODES 레지스트리에서 동적 생성 */}
    {EPISODES.map((ep) => (
      <Composition
        key={ep.episodeId}
        id={ep.episodeId.toUpperCase().replace(/-/g, "")}
        component={EnometaShorts}
        durationInFrames={30 * 30}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={calcMeta}
        defaultProps={ep}
      />
    ))}
  </>
);
