import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep006: 틀리면서 닿는다. 그게 삶이다
import visualScriptJson from "../episodes/ep006/visual_script.json";
import audioAnalysisJson from "../episodes/ep006/audio_analysis.json";
import narrationTimingJson from "../episodes/ep006/narration_timing.json";

export const ep006VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep006Title: string = (visualScriptJson as any).title || "틀리면서 닿는다. 그게 삶이다";
export const ep006AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep006AudioSrc: string = "ep006/mixed.wav";
export const ep006NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
