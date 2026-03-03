"""
ENOMETA Python 비주얼 렌더러

음악 엔진의 raw_visual_data.npz를 직접 소비하여
프레임 시퀀스(PNG)를 생성한다.

사용법:
  python scripts/visual_renderer.py episodes/ep005 --genre techno
"""

import sys
import os
import json
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

# 같은 scripts/ 디렉토리에서 임포트
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visual_layers import (
    BytebeatLayer, WaveformLayer, ParticleLayer,
    DataMatrixLayer, FeedbackLayer,
    BarcodeLayer, SineWaveLayer, DataStreamLayer, TextDataLayer,
    composite_layers, composite_dual_source,
)


# ============================================================
# 팔레트 (RGB 튜플 — Pillow/numpy용)
# ============================================================
PALETTES = {
    "phantom":    {"bg": (6, 6, 10),    "accent": (139, 92, 246),  "mid": (60, 40, 120)},
    "neon_noir":  {"bg": (5, 5, 8),     "accent": (255, 45, 85),   "mid": (120, 20, 40)},
    "cold_steel": {"bg": (8, 8, 12),    "accent": (0, 240, 255),   "mid": (0, 80, 100)},
    "ember":      {"bg": (10, 8, 6),    "accent": (255, 107, 0),   "mid": (120, 50, 0)},
    "synapse":    {"bg": (6, 6, 24),    "accent": (65, 105, 225),  "mid": (30, 50, 110)},
    "gameboy":    {"bg": (15, 56, 15),  "accent": (155, 188, 15),  "mid": (48, 98, 48)},
    "c64":        {"bg": (64, 49, 141), "accent": (165, 154, 222), "mid": (110, 100, 180)},
    "ikeda":      {"bg": (0, 0, 0),     "accent": (255, 255, 255), "mid": (80, 80, 80)},
}

# v8: ikeda 단일 장르 — 팔레트 항상 ikeda
GENRE_PALETTE = {
    "ikeda": "ikeda",
}

# ============================================================
# Ikeda 씬별 색 전환 시스템
# ============================================================
IKEDA_EMOTION_COLORS = {
    "neutral":    (255, 255, 255),  # 순백
    "neutral_curious": (200, 200, 255),
    "neutral_analytical": (180, 220, 255),
    "curious":    (200, 200, 255),
    "tension":    (255, 30, 60),    # 빨간 (공포)
    "tension_peak": (255, 20, 40),
    "tension_reveal": (255, 60, 80),
    "tension_frustrated": (255, 40, 50),
    "tension_transformative": (255, 80, 100),
    "tension_redefine": (255, 50, 70),
    "fear":       (255, 30, 60),    # 빨간
    "awakening":  (0, 240, 255),    # 시안 (각성)
    "awakening_spark": (0, 200, 255),
    "awakening_climax": (0, 255, 200),
    "flow":       (255, 255, 255),  # 순백 (몰입)
    "flow_immersion": (240, 240, 255),
    "climax":     (0, 255, 65),     # 초록 (데이터)
    "resolution": (180, 180, 255),  # 연한 블루
    "resolution_chemical": (160, 200, 255),
    "resolution_memory": (180, 180, 240),
    "somber":     (120, 120, 160),
    "somber_analytical": (140, 140, 180),
    "fade":       (100, 100, 100),
}

# ============================================================
# 장르별 레이어 프리셋
# ============================================================
# ============================================================
# 장르별 레이어 프리셋 (v2 — 풍성한 레이어 조합)
# ============================================================
# 원칙:
#   1. 모든 장르에 TTS 4레이어 기본 장착 (script_data만 있으면 동작)
#   2. 음악 레이어 3개 (장르 리드 + 범용 보조 2개)
#   3. 장르 차별화 = intensity 분배 + blend_ratio + palette
#   4. 데이터 의존성: BytebeatLayer→bytebeat/chiptune, SineWaveLayer→ikeda
#
# intensity 설계 철학:
#   리드 레이어: 0.7~0.9 (장르 시그니처)
#   서포트 레이어: 0.3~0.5 (깊이감 추가)
#   TTS 레이어: 장르별 강약 조절 (0.3~0.7)
# ============================================================

# v8: ikeda 단일 장르 — 모든 비주얼 레이어 프리셋
GENRE_LAYER_PRESETS = {
    # ── ikeda (60bpm) ── ENOMETA v8 단일 장르: 데이터아트 + 확장 텍스처
    # Music: SineWave (간섭 패턴) + Waveform (파형) + Particle (에너지)
    # TTS: TextData (데이터 카드) + Barcode (바이트 스트라이프) + DataStream + DataMatrix
    "ikeda": {
        "music_layers": [
            {"layer": "SineWaveLayer",   "intensity": 0.7},
            {"layer": "WaveformLayer",   "intensity": 0.4},
            {"layer": "ParticleLayer",   "intensity": 0.3},
        ],
        "tts_layers": [
            {"layer": "TextDataLayer",   "intensity": 0.95},
            {"layer": "BarcodeLayer",    "intensity": 0.85},
            {"layer": "DataStreamLayer", "intensity": 0.75},
            {"layer": "DataMatrixLayer", "intensity": 0.65},
        ],
        "blend_ratio": 0.45,
    },
}

LAYER_CLASSES = {
    "BytebeatLayer": BytebeatLayer,
    "WaveformLayer": WaveformLayer,
    "ParticleLayer": ParticleLayer,
    "DataMatrixLayer": DataMatrixLayer,
    "FeedbackLayer": FeedbackLayer,
    "BarcodeLayer": BarcodeLayer,
    "SineWaveLayer": SineWaveLayer,
    "DataStreamLayer": DataStreamLayer,
    "TextDataLayer": TextDataLayer,
}

# SI 기반 레이어 강도 스케일 함수
# base_intensity × scale(si) = effective_intensity
# SineWave: 배경 역할 → si 낮을 때 강하고 si 높을 때 약해짐
# Waveform/Particle: 음악 반응 → si에 비례
# TTS 레이어: 텍스트 표시 → si에 완만하게 비례
SI_INTENSITY_SCALE = {
    "SineWaveLayer":   lambda si: max(0.35, 1.0 - si * 0.45),  # 배경→서브, si=0→1.0, si=1→0.55
    "WaveformLayer":   lambda si: 0.25 + si * 0.75,             # si=0→0.25, si=1→1.0
    "ParticleLayer":   lambda si: max(0.05, si ** 1.5),         # si=0→0.05, si=1→1.0 (민감)
    "TextDataLayer":   lambda si: 0.70 + si * 0.30,             # si=0→0.70, si=1→1.0
    "BarcodeLayer":    lambda si: 0.60 + si * 0.40,             # si=0→0.60, si=1→1.0
    "DataStreamLayer": lambda si: 0.50 + si * 0.50,             # si=0→0.50, si=1→1.0
    "DataMatrixLayer": lambda si: max(0.40, si ** 0.8),         # si=0→0.40, si=1→1.0
}


class VisualRenderer:
    def __init__(self, episode_dir: str, genre: str,
                 width=1080, height=1080, fps=30):
        self.episode_dir = Path(episode_dir)
        self.genre = genre
        self.width = width
        self.height = height
        self.fps = fps

        palette_name = GENRE_PALETTE.get(genre, "ikeda")
        self.palette = PALETTES[palette_name]

        self.raw_data = self._load_raw_data()
        self.visual_script = self._load_visual_script()
        self.script_data = self._load_script_data()
        self.total_frames = int(self.raw_data["total_frames"])
        self.layers = self._init_layers()

        # Ikeda 색 전환: 이전 accent 색 (페이드용)
        self._prev_accent = None

    def _load_raw_data(self) -> dict:
        npz_path = self.episode_dir / "bgm_raw_visual_data.npz"
        data = np.load(npz_path, allow_pickle=True)
        return {key: data[key] for key in data.files}

    def _load_visual_script(self) -> dict:
        script_path = self.episode_dir / "visual_script.json"
        if script_path.exists():
            return json.loads(script_path.read_text(encoding="utf-8"))
        return {"scenes": []}

    def _load_script_data(self) -> dict:
        """script_data.json 로딩 (ikeda 비주얼용)"""
        sd_path = self.episode_dir / "script_data.json"
        if sd_path.exists():
            return json.loads(sd_path.read_text(encoding="utf-8"))
        return None

    def _init_layers(self) -> dict:
        preset = GENRE_LAYER_PRESETS.get(self.genre, GENRE_LAYER_PRESETS["ikeda"])

        # 하위호환: flat list 입력 시 전부 music_layers로 취급
        if isinstance(preset, list):
            preset = {"music_layers": preset, "tts_layers": [], "blend_ratio": 0.8}

        self.blend_ratio = preset.get("blend_ratio", 0.5)

        def _build(cfgs):
            result = []
            for cfg in cfgs:
                cls = LAYER_CLASSES[cfg["layer"]]
                layer = cls(self.width, self.height, self.palette,
                            intensity=cfg["intensity"])
                # SI 동적 스케일링을 위한 기준값 저장
                layer._base_intensity = cfg["intensity"]
                result.append(layer)
            return result

        return {
            "music": _build(preset.get("music_layers", [])),
            "tts": _build(preset.get("tts_layers", [])),
        }

    def _get_current_scene(self, time_sec: float) -> dict:
        for scene in self.visual_script.get("scenes", []):
            start = scene.get("start_sec", scene.get("start", 0))
            end = scene.get("end_sec", scene.get("end", 0))
            if start <= time_sec < end:
                return scene
        return {}

    def _get_ikeda_accent(self, emotion: str) -> tuple:
        """Ikeda 씬별 accent 색 결정 (기본 흰색, 감정별 색 전환)"""
        target = IKEDA_EMOTION_COLORS.get(emotion)
        if not target:
            base = emotion.split("_")[0] if emotion else "neutral"
            target = IKEDA_EMOTION_COLORS.get(base, (255, 255, 255))

        # 부드러운 색 전환 (3-5프레임 페이드)
        if self._prev_accent is None:
            self._prev_accent = target
            return target

        # Lerp 20% per frame (5프레임에 ~67% 전환)
        r = int(self._prev_accent[0] * 0.8 + target[0] * 0.2)
        g = int(self._prev_accent[1] * 0.8 + target[1] * 0.2)
        b = int(self._prev_accent[2] * 0.8 + target[2] * 0.2)
        result = (r, g, b)
        self._prev_accent = result
        return result

    def render_frame(self, frame_idx: int) -> Image.Image:
        """단일 프레임 렌더링 (Dual-Source Architecture)"""
        # 배경
        canvas = np.full((self.height, self.width, 3), self.palette["bg"], dtype=np.uint8)

        # 프레임 컨텍스트
        ctx = {
            "frame_idx": frame_idx,
            "frame_index": frame_idx,
            "audio_chunk": self.raw_data["audio_chunks"][frame_idx],
            "bytebeat_values": self.raw_data["bytebeat_values"][frame_idx],
            "section_energy": float(self.raw_data["section_energies"][frame_idx]),
            "frame_rms": float(self.raw_data["frame_rms"][frame_idx]),
            "bpm": float(self.raw_data["bpm"]),
            "genre": str(self.raw_data["genre"]),
            "total_frames": self.total_frames,
            "time": frame_idx / self.fps,
        }

        # Song Arc 데이터
        if "arc_energy" in self.raw_data:
            ctx["arc_energy"] = float(self.raw_data["arc_energy"][frame_idx])
            ctx["arc_phase"] = str(self.raw_data["arc_phases"][frame_idx])
        else:
            ctx["arc_energy"] = 1.0
            ctx["arc_phase"] = "constant"

        # Ikeda 전용 데이터
        if "sine_interference_values" in self.raw_data:
            ctx["sine_interference_values"] = self.raw_data["sine_interference_values"][frame_idx]
        if "data_click_positions" in self.raw_data:
            ctx["data_click_frame"] = bool(self.raw_data["data_click_positions"][frame_idx] > 0)

        # script_data 전달 + semantic_intensity 주입
        if self.script_data:
            ctx["script_data"] = self.script_data
            # 현재 시간의 세그먼트에서 semantic_intensity 추출
            si = 0.2  # 기본값 (legacy script_data 호환)
            current_keywords = []
            for seg in self.script_data.get("segments", []):
                if seg["start_sec"] <= ctx["time"] < seg["end_sec"]:
                    si = seg.get("analysis", {}).get("semantic_intensity", 0.2)
                    current_keywords = seg.get("analysis", {}).get("keywords", [])
                    break
            ctx["semantic_intensity"] = si
            ctx["current_keywords"] = current_keywords
            # reactive_level: semantic_intensity 80% + rms 20% (최종 반응 레벨)
            rms = ctx["frame_rms"]
            ctx["reactive_level"] = si * 0.8 + min(rms * 2.0, 0.4) * 0.2
        else:
            ctx["semantic_intensity"] = 0.2
            ctx["current_keywords"] = []
            ctx["reactive_level"] = 0.2

        scene = self._get_current_scene(ctx["time"])
        if scene:
            ctx["emotion"] = scene.get("emotion", "neutral")

        # Ikeda accent 색 결정
        if self.genre == "ikeda":
            emotion = ctx.get("emotion", "neutral")
            ctx["accent_color"] = self._get_ikeda_accent(emotion)
        else:
            ctx["accent_color"] = self.palette.get("accent")

        # Dual-Source: 음악 레이어와 TTS 레이어 독립 렌더
        zeros = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # SI 기반 레이어 강도 동적 조절
        si = ctx["semantic_intensity"]
        for layer in self.layers["music"] + self.layers["tts"]:
            layer_name = type(layer).__name__
            scale_fn = SI_INTENSITY_SCALE.get(layer_name)
            if scale_fn and hasattr(layer, "_base_intensity"):
                layer.intensity = layer._base_intensity * scale_fn(si)

        music_images = [layer.render(ctx) for layer in self.layers["music"]]
        tts_images = [layer.render(ctx) for layer in self.layers["tts"]]

        music_composite = composite_layers(zeros, music_images)
        tts_composite = composite_layers(zeros, tts_images)

        # Dual-Source 합성 (arc_energy가 음악 레이어 강도 변조)
        final = composite_dual_source(
            canvas, music_composite, tts_composite,
            blend_ratio=self.blend_ratio,
            arc_energy=ctx["arc_energy"],
        )
        return Image.fromarray(final)

    def render_all(self):
        """전체 프레임 렌더링"""
        frames_dir = self.episode_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        music_names = [type(l).__name__ for l in self.layers["music"]]
        tts_names = [type(l).__name__ for l in self.layers["tts"]]
        arc_name = str(self.raw_data.get("arc_name", "flat"))

        print(f"=== ENOMETA Python Visual Renderer (Dual-Source) ===")
        print(f"  Episode: {self.episode_dir}")
        print(f"  Genre: {self.genre}")
        print(f"  Frames: {self.total_frames}")
        print(f"  Size: {self.width}x{self.height}")
        print(f"  Music layers: {music_names}")
        print(f"  TTS layers:   {tts_names}")
        print(f"  Blend ratio:  {self.blend_ratio}")
        print(f"  Song Arc:     {arc_name}")
        if self.script_data:
            print(f"  Script data: loaded ({len(self.script_data.get('segments', []))} segments)")
        print()

        for i in range(self.total_frames):
            frame = self.render_frame(i)
            frame.save(frames_dir / f"{i:06d}.png")

            if (i + 1) % 30 == 0:
                elapsed = (i + 1) / self.fps
                pct = (i + 1) / self.total_frames * 100
                print(f"  [{i+1}/{self.total_frames}] {elapsed:.1f}s ({pct:.0f}%)")

        print(f"\nDone! Frames saved: {frames_dir}")


def main():
    parser = argparse.ArgumentParser(description="ENOMETA Python 비주얼 렌더러")
    parser.add_argument("episode_dir", help="에피소드 디렉토리 경로")
    parser.add_argument("--genre", default="techno",
                        choices=["techno", "bytebeat", "algorave", "harsh_noise",
                                 "chiptune", "ikeda"])
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    renderer = VisualRenderer(
        args.episode_dir, args.genre,
        args.width, args.height, args.fps,
    )
    renderer.render_all()


if __name__ == "__main__":
    main()
