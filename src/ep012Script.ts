import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep012: 집단지성의 거짓말
import visualScriptJson from "../episodes/ep012/visual_script.json";
import audioAnalysisJson from "../episodes/ep012/audio_analysis.json";
import narrationTimingJson from "../episodes/ep012/narration_timing.json";

export const ep012VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep012Title: string = (visualScriptJson as any).title || "집단지성의 거짓말";
export const ep012AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep012AudioSrc: string = "ep012/mixed.wav";
export const ep012NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
