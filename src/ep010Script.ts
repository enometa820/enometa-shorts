import { VisualScript, NarrationSegment } from "./types";
import { AudioAnalysis } from "./hooks/useAudioData";

// ep010: 우리의 믿음이 우리의 몸이 된다
import visualScriptJson from "../episodes/ep010/visual_script.json";
import audioAnalysisJson from "../episodes/ep010/audio_analysis.json";
import narrationTimingJson from "../episodes/ep010/narration_timing.json";

export const ep010VisualScript: VisualScript = visualScriptJson as unknown as VisualScript;
export const ep010Title: string = (visualScriptJson as any).title || "우리의 믿음이 우리의 몸이 된다";
export const ep010AudioAnalysis: AudioAnalysis = audioAnalysisJson as unknown as AudioAnalysis;
export const ep010AudioSrc: string = "ep010/mixed.wav";
export const ep010NarrationSegments: NarrationSegment[] =
  (narrationTimingJson as any).segments as NarrationSegment[];
