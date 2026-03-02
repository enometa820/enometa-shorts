import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep004: 우리의 선택은 몇 번이나 우리의 것이었을까
import visualScriptJson from "../episodes/ep004/visual_script.json";
import audioAnalysisJson from "../episodes/ep004/audio_analysis.json";
import narrationTimingJson from "../episodes/ep004/narration_timing.json";

export const ep004VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep004Title: string = (visualScriptJson as any).title || "ENOMETA";
export const ep004AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep004AudioSrc: string = "ep004/mixed.wav";
export const ep004NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
