import { useCurrentFrame, useVideoConfig, staticFile } from "remotion";
import { useMemo } from "react";

export interface AudioFrame {
  bass: number;    // 0~1, 저주파 에너지 (20-250Hz)
  mid: number;     // 0~1, 중주파 에너지 (250-4000Hz)
  high: number;    // 0~1, 고주파 에너지 (4000-20000Hz)
  rms: number;     // 0~1, 전체 볼륨
  onset: boolean;  // 비트/온셋 감지 여부
}

export interface AudioAnalysis {
  fps: number;
  duration_sec: number;
  frames: AudioFrame[];
}

// 오디오 분석 데이터에서 현재 프레임에 맞는 값을 반환
export const useAudioData = (analysis?: AudioAnalysis | null): AudioFrame => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const defaultFrame: AudioFrame = {
    bass: 0,
    mid: 0,
    high: 0,
    rms: 0,
    onset: false,
  };

  if (!analysis || !analysis.frames || analysis.frames.length === 0) {
    return defaultFrame;
  }

  const audioFps = analysis.fps || fps;
  const audioFrameIndex = Math.floor((frame / fps) * audioFps);
  const clampedIndex = Math.min(audioFrameIndex, analysis.frames.length - 1);

  return analysis.frames[Math.max(0, clampedIndex)];
};

// 테스트/프로토타입용: 시뮬레이트된 오디오 데이터
export const useSimulatedAudio = (): AudioFrame => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // 간단한 시뮬레이션: 사인파 기반
  const bass = Math.pow(Math.sin(t * 2.0) * 0.5 + 0.5, 2);
  const mid = Math.pow(Math.sin(t * 3.5 + 1.0) * 0.5 + 0.5, 1.5);
  const high = Math.pow(Math.sin(t * 7.0 + 2.0) * 0.5 + 0.5, 2);
  const rms = (bass * 0.4 + mid * 0.35 + high * 0.25) * 0.8 + 0.1;
  const onset = Math.sin(t * 4.0) > 0.95;

  return { bass, mid, high, rms, onset };
};
