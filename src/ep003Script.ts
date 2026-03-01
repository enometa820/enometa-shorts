import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep003: 우리의 기억은 매번 다시 만들어진다
import visualScriptJson from "../episodes/ep003/visual_script.json";
import audioAnalysisJson from "../episodes/ep003/audio_analysis.json";
import narrationTimingJson from "../episodes/ep003/narration_timing.json";

export const ep003VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep003Title: string = (visualScriptJson as any).title || "ENOMETA";
export const ep003AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep003AudioSrc: string = "ep003/mixed.wav";
export const ep003NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
