import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep009: 우리의 뇌는 지금 누구를 위해 일하는가
import visualScriptJson from "../episodes/ep009/visual_script.json";
import audioAnalysisJson from "../episodes/ep009/audio_analysis.json";
import narrationTimingJson from "../episodes/ep009/narration_timing.json";

export const ep009VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep009Title: string = (visualScriptJson as any).title || "우리의 뇌는 지금 누구를 위해 일하는가";
export const ep009AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep009AudioSrc: string = "ep009/mixed.wav";
export const ep009NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
