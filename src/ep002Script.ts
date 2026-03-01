import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep002: 당신의 오답이 뇌를 가장 크게 깨운다
import visualScriptJson from "../episodes/ep002/visual_script.json";
import audioAnalysisJson from "../episodes/ep002/audio_analysis.json";
import narrationTimingJson from "../episodes/ep002/narration_timing.json";

export const ep002VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep002Title: string = (visualScriptJson as any).title || "ENOMETA";
export const ep002AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep002AudioSrc: string = "ep002/mixed.wav";
export const ep002NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
