import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep011: 자연은 우리보다 38억 년 먼저 코딩했다
import visualScriptJson from "../episodes/ep011/visual_script.json";
import audioAnalysisJson from "../episodes/ep011/audio_analysis.json";
import narrationTimingJson from "../episodes/ep011/narration_timing.json";

export const ep011VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep011Title: string = (visualScriptJson as any).title || "자연은 우리보다 38억 년 먼저 코딩했다";
export const ep011AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep011AudioSrc: string = "ep011/mixed.wav";
export const ep011NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
