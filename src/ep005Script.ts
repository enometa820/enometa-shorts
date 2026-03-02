import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep005: 공포와 각성의 화학식은 같다
import visualScriptJson from "../episodes/ep005/visual_script.json";
import audioAnalysisJson from "../episodes/ep005/audio_analysis.json";
import narrationTimingJson from "../episodes/ep005/narration_timing.json";

export const ep005VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep005Title: string = (visualScriptJson as any).title || "공포와 각성의 화학식은 같다";
export const ep005AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep005AudioSrc: string = "ep005/mixed.wav";
export const ep005NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
