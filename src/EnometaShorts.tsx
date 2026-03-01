import React from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import {
  useSimulatedAudio,
  useAudioData,
  AudioAnalysis,
} from "./hooks/useAudioData";
import { TitleSection } from "./components/TitleSection";
import { VisualSection } from "./components/VisualSection";
import { SubtitleSection } from "./components/SubtitleSection";
import { LogoEndcard } from "./components/LogoEndcard";
import { getPalette } from "./utils/palettes";
import { VisualScript, NarrationSegment } from "./types";

// 테스트용 비주얼 스크립트 (Phase 0 프로토타입)
import { testVisualScript } from "./testScript";

interface EnometaShortsProps {
  visualScript?: VisualScript;
  audioSrc?: string;
  title?: string;
  audioAnalysis?: AudioAnalysis;
  narrationSegments?: NarrationSegment[];
  highlightWords?: string[];
  endcardDurationSec?: number; // 엔드카드 길이 (초), 기본 6초
}

export const EnometaShorts: React.FC<EnometaShortsProps> = ({
  visualScript,
  audioSrc,
  title,
  audioAnalysis,
  narrationSegments,
  highlightWords,
  endcardDurationSec = 6,
}) => {
  const script = visualScript || testVisualScript;
  const palette = getPalette(script.global.palette || "phantom");
  const simulatedAudio = useSimulatedAudio();
  const realAudio = useAudioData(audioAnalysis);
  const audio = audioAnalysis ? realAudio : simulatedAudio;
  const displayTitle = title || (script as any).title || "ENOMETA";

  // 엔드카드: 마지막 씬 종료 후 시작
  const lastScene = script.scenes[script.scenes.length - 1];
  const endcardStartSec = lastScene ? lastScene.end_sec : 30; // 씬 끝나자마자 엔드카드
  const endcardStartFrame = Math.round(endcardStartSec * 30);
  const endcardDurationFrames = Math.round(endcardDurationSec * 30);

  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg }}>
      {/* 오디오 트랙 (있을 경우) */}
      {audioSrc && <Audio src={staticFile(audioSrc)} />}

      {/* 9:16 레이아웃: 1080 × 1920 (YouTube Shorts UI 세이프존 반영) */}
      {/*
        상단 ~100px: 상태바/Shorts 레이블 (가려짐)
        하단 ~200px: 채널명/구독/음악 (가려짐)
        우측 하단: 좋아요/댓글/공유 버튼

        레이아웃:
        - 제목: y=100~370 (상태바 아래, 270px 영역)
        - 비주얼: y=370~1450 (1080px)
        - 자막: 비주얼 안쪽 하단 오버레이 (MarginV=80)
        - 하단 여백: y=1450~1920 (470px, YouTube UI 영역)
      */}
      <div
        style={{
          width: 1080,
          height: 1920,
          position: "relative",
        }}
      >
        {/* 상단: 제목 (상태바 100px 아래부터) */}
        <TitleSection
          title={displayTitle}
          audio={audio}
          accentColor={palette.accent}
          glowColor={palette.glow}
          highlightWords={highlightWords}
        />

        {/* 중앙: 비주얼 (1080 × 1080px, y=370 시작) */}
        <div style={{ position: "absolute", top: 370, left: 0 }}>
          <VisualSection
            scenes={script.scenes}
            audio={audio}
            bgColor={palette.bg}
          />
        </div>

        {/* 자막: 비주얼 안쪽 하단에 오버레이 (y=1450 - 80 - textHeight 근처) */}
        <SubtitleSection
          scenes={script.scenes}
          audio={audio}
          accentColor={palette.accent}
          narrationSegments={narrationSegments}
        />

        {/* 엔드카드: 로고 애니메이션 (에피소드 팔레트 적용) */}
        <LogoEndcard
          startFrame={endcardStartFrame}
          durationFrames={endcardDurationFrames}
          palette={palette}
        />
      </div>
    </AbsoluteFill>
  );
};
