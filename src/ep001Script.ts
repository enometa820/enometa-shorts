import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep001: 당신의 뇌는 어제를 복사하고 있다
import visualScriptJson from "../episodes/ep001/visual_script.json";
import audioAnalysisJson from "../episodes/ep001/audio_analysis.json";
import narrationTimingJson from "../episodes/ep001/narration_timing.json";

export const ep001VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep001Title: string = (visualScriptJson as any).title || "ENOMETA";
export const ep001AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep001AudioSrc: string = "ep001/mixed.wav";
export const ep001NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
