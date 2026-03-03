import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep007: 알고리즘은 쌓지 않는다. 덜어낸다
import visualScriptJson from "../episodes/ep007/visual_script.json";
import audioAnalysisJson from "../episodes/ep007/audio_analysis.json";
import narrationTimingJson from "../episodes/ep007/narration_timing.json";

export const ep007VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep007Title: string = (visualScriptJson as any).title || "알고리즘은 쌓지 않는다. 덜어낸다";
export const ep007AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep007AudioSrc: string = "ep007/mixed.wav";
export const ep007NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
