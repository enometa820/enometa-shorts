import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep008: 질서는 안정에서 오지 않았다
import visualScriptJson from "../episodes/ep008/visual_script.json";
import audioAnalysisJson from "../episodes/ep008/audio_analysis.json";
import narrationTimingJson from "../episodes/ep008/narration_timing.json";

export const ep008VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep008Title: string = (visualScriptJson as any).title || "질서는 안정에서 오지 않았다";
export const ep008AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep008AudioSrc: string = "ep008/mixed.wav";
export const ep008NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
