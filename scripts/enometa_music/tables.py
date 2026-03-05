"""enometa_music/tables.py — 데이터 테이블 (감정 매핑, 아크, 장르, 편곡)"""
import numpy as np


# v13: 하드코딩 패턴 제거, sequence_generators.py 사용.
EMOTION_MAP = {
    # === 뉴트럴 계열: 미니멀, 관찰적 ===
    "neutral": {
        "energy": 0.35,
        "bass_drone": {"active": True, "volume": 0.6},
        "clicks": {"active": True, "density": 0.3, "pan_spread": 0.4},
        "fm_bass": {"active": True, "volume": 0.25},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.35},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "neutral_curious": {
        "energy": 0.4,
        "bass_drone": {"active": True, "volume": 0.65},
        "clicks": {"active": True, "density": 0.5, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.35},
        "arpeggio": {"active": True, "speed": 0.35, "volume": 0.25},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.25},
        "hi_hat": {"active": True, "volume": 0.15},
        "sub_pulse": {"active": True, "volume": 0.4},
        "noise_burst": {"active": True, "density": 0.15},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.2, "duty": 0.25},
        "chiptune_drum": {"active": False},
    },
    "neutral_analytical": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.7},
        "clicks": {"active": True, "density": 0.6, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.4},
        "arpeggio": {"active": True, "speed": 0.25, "volume": 0.35},
        "glitch": {"active": True, "density": 0.25},
        "kick": {"active": True, "volume": 0.35},
        "hi_hat": {"active": True, "volume": 0.2},
        "sub_pulse": {"active": True, "volume": 0.45},
        "metallic_hit": {"active": True, "volume": 0.2, "density": 0.2},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.2},
    },
    "curious": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.7},
        "clicks": {"active": True, "density": 0.5, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.35},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.35},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.3},
        "hi_hat": {"active": True, "volume": 0.18},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.15, "duty": 0.5},
        "chiptune_drum": {"active": False},
    },
    # === 솜버 계열: 어둡고 무거운 ===
    "somber": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.85},
        "clicks": {"active": True, "density": 0.2, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.45},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "somber_reflective": {
        "energy": 0.5,
        "bass_drone": {"active": True, "volume": 0.8},
        "clicks": {"active": True, "density": 0.15, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.45},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "somber_repetitive": {
        "energy": 0.55,
        "bass_drone": {"active": True, "volume": 0.85},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.4},
        "fm_bass": {"active": True, "volume": 0.45},
        "arpeggio": {"active": True, "speed": 0.22, "volume": 0.6},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.25},
        "hi_hat": {"active": True, "volume": 0.15},
        "sub_pulse": {"active": True, "volume": 0.5},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.15},
    },
    "somber_analytical": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.9},
        "clicks": {"active": True, "density": 0.45, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.2, "volume": 0.65},
        "glitch": {"active": True, "density": 0.3},
        "kick": {"active": True, "volume": 0.35},
        "hi_hat": {"active": True, "volume": 0.18},
        "sub_pulse": {"active": True, "volume": 0.55},
        "noise_burst": {"active": True, "density": 0.2},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "somber_warning": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.9},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.45},
        "arpeggio": {"active": True, "speed": 0.2, "volume": 0.55},
        "glitch": {"active": True, "density": 0.25},
        "noise_sweep": {"active": True, "direction": "down", "speed": 0.3},
        "kick": {"active": True, "volume": 0.4},
        "hi_hat": {"active": True, "volume": 0.2},
        "sub_pulse": {"active": True, "volume": 0.6},
        "bytebeat": {"active": True, "volume": 0.15, "formula": "drone"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    # === 텐션 계열: 강렬, 공격적 ===
    "tension": {
        "energy": 0.75,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 1.2, "pan_spread": 0.8},
        "fm_bass": {"active": True, "volume": 0.6},
        "arpeggio": {"active": True, "speed": 0.15, "volume": 0.8},
        "glitch": {"active": True, "density": 0.7},
        "noise_sweep": {"active": True, "direction": "up", "speed": 0.3},
        "kick": {"active": True, "volume": 0.65},
        "hi_hat": {"active": True, "volume": 0.35},
        "acid_bass": {"active": True, "volume": 0.5, "sweep_dir": "down"},
        "saw_sequence": {"active": True, "volume": 0.7},  # v9
        "gate_stutter": {"active": True, "volume": 0.4},  # v9
        "sub_pulse": {"active": True, "volume": 0.8},
        "noise_burst": {"active": True, "density": 0.5},
        "bytebeat": {"active": True, "volume": 0.2, "formula": "industrial"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.25},
        "pulse_train": {"active": True, "volume": 0.3},
    },
    "tension_reveal": {
        "energy": 0.7,
        "bass_drone": {"active": True, "volume": 0.95},
        "clicks": {"active": True, "density": 1.0, "pan_spread": 0.7},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.18, "volume": 0.7},
        "glitch": {"active": True, "density": 0.55},
        "kick": {"active": True, "volume": 0.5},
        "hi_hat": {"active": True, "volume": 0.3},
        "sub_pulse": {"active": True, "volume": 0.7},
        "noise_burst": {"active": True, "density": 0.4},
        "metallic_hit": {"active": True, "volume": 0.25, "density": 0.25},
        "bytebeat": {"active": True, "volume": 0.15, "formula": "glitch"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "tension_transformative": {
        "energy": 0.8,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 1.1, "pan_spread": 0.8},
        "fm_bass": {"active": True, "volume": 0.6},
        "arpeggio": {"active": True, "speed": 0.12, "volume": 0.85},
        "glitch": {"active": True, "density": 0.7},
        "kick": {"active": True, "volume": 0.65},
        "hi_hat": {"active": True, "volume": 0.35},
        "acid_bass": {"active": True, "volume": 0.6, "sweep_dir": "up"},
        "sub_pulse": {"active": True, "volume": 0.8},
        "stutter_gate": {"active": True, "divisions": 8, "blend": 0.3},
        "bytebeat": {"active": True, "volume": 0.2, "formula": "chaos"},
        "feedback": {"active": True, "volume": 0.2, "iterations": 4},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "tension_redefine": {
        "energy": 0.78,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 1.0, "pan_spread": 0.75},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.14, "volume": 0.75},
        "glitch": {"active": True, "density": 0.6},
        "kick": {"active": True, "volume": 0.6},
        "hi_hat": {"active": True, "volume": 0.32},
        "synth_lead": {"active": True, "volume": 0.35, "note_duration": 1.0},
        "sub_pulse": {"active": True, "volume": 0.75},
        "noise_burst": {"active": True, "density": 0.35},
        "bytebeat": {"active": False},
        "feedback": {"active": True, "volume": 0.15, "iterations": 3},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.2},
    },
    "tension_frustrated": {
        "energy": 0.85,
        "bass_drone": {"active": True, "volume": 1.1},
        "clicks": {"active": True, "density": 1.4, "pan_spread": 0.9},
        "fm_bass": {"active": True, "volume": 0.65},
        "arpeggio": {"active": True, "speed": 0.1, "volume": 0.9},
        "glitch": {"active": True, "density": 0.85},
        "kick": {"active": True, "volume": 0.7},
        "hi_hat": {"active": True, "volume": 0.4},
        "acid_bass": {"active": True, "volume": 0.65, "sweep_dir": "down"},
        "sub_pulse": {"active": True, "volume": 0.9},
        "stutter_gate": {"active": True, "divisions": 16, "blend": 0.4},
        "bytebeat": {"active": True, "volume": 0.25, "formula": "industrial"},
        "feedback": {"active": True, "volume": 0.1},  # v8 C-2: enometa 피드백 텍스처
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "tension_peak": {
        "energy": 0.95,
        "bass_drone": {"active": True, "volume": 1.2},
        "clicks": {"active": True, "density": 1.8, "pan_spread": 1.0},
        "fm_bass": {"active": True, "volume": 0.7},
        "arpeggio": {"active": True, "speed": 0.1, "volume": 1.0},
        "glitch": {"active": True, "density": 1.0},
        "noise_sweep": {"active": True, "direction": "up", "speed": 0.3},
        "kick": {"active": True, "volume": 0.8},
        "hi_hat": {"active": True, "volume": 0.45},
        "acid_bass": {"active": True, "volume": 0.7, "sweep_dir": "down"},
        "saw_sequence": {"active": True, "volume": 1.0},  # v9
        "gate_stutter": {"active": True, "volume": 0.6},  # v9
        "sub_pulse": {"active": True, "volume": 1.0},
        "stutter_gate": {"active": True, "divisions": 16, "blend": 0.5},
        "noise_burst": {"active": True, "density": 0.6},
        "bytebeat": {"active": True, "volume": 0.3, "formula": "chaos"},
        "feedback": {"active": True, "volume": 0.15},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
        "pulse_train": {"active": True, "volume": 0.5},
    },
    # === 각성 계열: 에너지 상승, 해방 ===
    "awakening_spark": {
        "energy": 0.8,
        "bass_drone": {"active": True, "volume": 0.95},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.7},
        "arpeggio": {"active": True, "speed": 0.25, "volume": 0.45},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.45},
        "hi_hat": {"active": True, "volume": 0.25},
        "synth_lead": {"active": True, "volume": 0.4, "note_duration": 0.6},
        "sub_pulse": {"active": True, "volume": 0.6},
        "metallic_hit": {"active": True, "volume": 0.25, "density": 0.2},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.25, "duty": 0.125},
        "chiptune_drum": {"active": True, "volume": 0.2},
    },
    "awakening_climax": {
        "energy": 1.0,
        "bass_drone": {"active": True, "volume": 1.2},
        "clicks": {"active": True, "density": 0.5, "pan_spread": 0.6},
        "fm_bass": {"active": True, "volume": 0.8},
        "arpeggio": {"active": True, "speed": 0.18, "volume": 0.6},
        "glitch": {"active": True, "density": 0.25},
        "kick": {"active": True, "volume": 0.75},
        "hi_hat": {"active": True, "volume": 0.4},
        "synth_lead": {"active": True, "volume": 0.5, "note_duration": 0.5},
        "acid_bass": {"active": True, "volume": 0.5, "sweep_dir": "up"},
        "saw_sequence": {"active": True, "volume": 0.8},  # v9
        "gate_stutter": {"active": True, "volume": 0.5},  # v9
        "sub_pulse": {"active": True, "volume": 0.7},
        "stutter_gate": {"active": True, "divisions": 8, "blend": 0.25},
        "bytebeat": {"active": True, "volume": 0.15, "formula": "cascade"},
        "feedback": {"active": True, "volume": 0.12},
        "chiptune_lead": {"active": True, "volume": 0.3, "duty": 0.25},
        "chiptune_drum": {"active": True, "volume": 0.25},
        "pulse_train": {"active": True, "volume": 0.45},
    },
    "awakening": {
        "energy": 0.85,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 0.3, "pan_spread": 0.4},
        "fm_bass": {"active": True, "volume": 0.7},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.35},
        "glitch": {"active": True, "density": 0.12},
        "kick": {"active": True, "volume": 0.5},
        "hi_hat": {"active": True, "volume": 0.25},
        "synth_lead": {"active": True, "volume": 0.45, "note_duration": 0.7},
        "sub_pulse": {"active": True, "volume": 0.6},
        "metallic_hit": {"active": True, "volume": 0.2, "density": 0.15},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.2, "duty": 0.5},
        "chiptune_drum": {"active": True, "volume": 0.2},
        "pulse_train": {"active": True, "volume": 0.35},
    },
    # === 희망/초월 계열 ===
    "hopeful": {
        "energy": 0.7,
        "bass_drone": {"active": True, "volume": 0.85},
        "clicks": {"active": True, "density": 0.2, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.6},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.4},
        "glitch": {"active": False},
        "kick": {"active": True, "volume": 0.4},
        "hi_hat": {"active": True, "volume": 0.2},
        "synth_lead": {"active": True, "volume": 0.4, "note_duration": 0.9},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.2, "duty": 0.5},
        "chiptune_drum": {"active": False},
    },
    "transcendent": {
        "energy": 0.65,
        "bass_drone": {"active": True, "volume": 0.75},
        "clicks": {"active": True, "density": 0.1, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.55},
        "arpeggio": {"active": True, "speed": 0.35, "volume": 0.25},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "synth_lead": {"active": True, "volume": 0.35, "note_duration": 1.2},
        "sub_pulse": {"active": True, "volume": 0.4},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
        "pulse_train": {"active": True, "volume": 0.2},
    },
    "transcendent_open": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.7},
        "clicks": {"active": True, "density": 0.08, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.4, "volume": 0.2},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "synth_lead": {"active": True, "volume": 0.3, "note_duration": 1.5},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    # === 페이드 아웃 ===
    "fade": {
        "energy": 0.1,
        "bass_drone": {"active": True, "volume": 0.25},
        "clicks": {"active": False},
        "fm_bass": {"active": True, "volume": 0.15},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
}


# ============================================================
# v8 C-4: 감정별 사인파 멜로디 시퀀스 — 4마디마다 주파수 쌍 전환
# _render_continuous_sine_interference()에서 사용
# ============================================================

def build_sine_melody_sequences(pad_root: float) -> dict:
    """v9: key_palette의 pad_root 기반으로 SINE_MELODY_SEQUENCES 동적 생성.
    하드코딩된 220Hz 대신 실제 선택된 키의 음정을 사용.
    beat_offset: 맥놀이 주파수 (Hz) — 작을수록 느린 비팅
    """
    r = pad_root
    # 스케일 음정 비율 (단조: 1, 9/8, 6/5, 4/3, 3/2, 8/5, 9/5)
    scale = [r, r * 9/8, r * 6/5, r * 4/3, r * 3/2, r * 8/5, r * 9/5, r * 2]
    def bp(f, beat): return (round(f, 1), round(f + beat, 1))
    return {
        "ascending":  [bp(scale[0], 3), bp(scale[2], 4), bp(scale[4], 3), bp(scale[6], 5)],
        "descending": [bp(scale[6], 5), bp(scale[4], 3), bp(scale[2], 4), bp(scale[0], 3)],
        "tension":    [bp(scale[0], 7), bp(scale[0], 13), bp(scale[0], 20), bp(scale[0], 27)],
        "release":    [bp(scale[4], 27), bp(scale[4], 20), bp(scale[4], 13), bp(scale[4], 7)],
        "neutral":    [bp(scale[0], 3), bp(scale[2], 3), bp(scale[0], 3), bp(scale[2], 3)],
    }

# 기본값 (generate_music_script에서 키 선택 후 덮어씌움)
SINE_MELODY_SEQUENCES = build_sine_melody_sequences(329.6)  # E_minor 기본

# 감정 → 시퀀스 매핑
EMOTION_TO_MELODY = {
    "neutral": "neutral", "neutral_curious": "neutral", "neutral_analytical": "neutral",
    "curious": "ascending",
    "somber": "descending", "somber_reflective": "descending", "somber_repetitive": "descending",
    "somber_analytical": "descending", "somber_warning": "tension",
    "tension": "tension", "tension_reveal": "tension", "tension_transformative": "tension",
    "tension_redefine": "tension", "tension_frustrated": "tension", "tension_peak": "tension",
    "awakening_spark": "ascending", "awakening_climax": "ascending", "awakening": "ascending",
    "hopeful": "release", "transcendent": "release", "transcendent_open": "release",
    "fade": "neutral",
}


# ============================================================
# Song Arc 프리셋 — 기승전결 매크로 구조
# 섹션별 smooth_envelope 위에 곱해지는 상위 에너지 엔벨로프
# ============================================================

SONG_ARC_PRESETS = {
    "narrative": {
        "description": "v10: 공격적 기승전결 — intro(active) → buildup(intense) → climax(brutal) → outro(fade)",
        "phases": [
            {
                "name": "intro",
                "start_pct": 0.0,
                "end_pct": 0.12,
                "energy_range": (0.7, 0.9),   # v10: 0.25-0.45 → 0.7-0.9 (intro도 공격적)
                "density_mult": 0.8,
            },
            {
                "name": "buildup",
                "start_pct": 0.12,
                "end_pct": 0.50,
                "energy_range": (0.9, 1.2),   # v10: 0.45-0.85 → 0.9-1.2
                "density_mult": 1.1,
            },
            {
                "name": "climax",
                "start_pct": 0.50,
                "end_pct": 0.80,
                "energy_range": (1.2, 1.5),   # v10: 0.85-1.2 → 1.2-1.5 (브루탈)
                "density_mult": 1.5,
            },
            {
                "name": "outro",
                "start_pct": 0.80,
                "end_pct": 1.0,
                "energy_range": (0.9, 0.2),   # v10: 0.7-0.15 → 0.9-0.2 (더 늦게 떨어짐)
                "density_mult": 0.7,
            },
        ],
    },
    "crescendo": {
        "description": "서서히 성장 — 끝에 최대 에너지",
        "phases": [
            {
                "name": "grow",
                "start_pct": 0.0,
                "end_pct": 0.85,
                "energy_range": (0.2, 1.1),
                "density_mult": 1.0,
            },
            {
                "name": "release",
                "start_pct": 0.85,
                "end_pct": 1.0,
                "energy_range": (1.1, 0.3),
                "density_mult": 0.8,
            },
        ],
    },
    "flat": {
        "description": "균등 에너지 — 기존 동작과 동일 (아크 없음)",
        "phases": [
            {
                "name": "constant",
                "start_pct": 0.0,
                "end_pct": 1.0,
                "energy_range": (1.0, 1.0),
                "density_mult": 1.0,
            },
        ],
    },
    "adaptive": {
        "description": "적응형 — semantic_intensity 곡선에서 내러티브 구조 자동 추출 (script_data 필수, 없으면 narrative fallback)",
        "phases": [],  # 동적 생성 — _compute_adaptive_arc()에서 계산
    },
    # ── D-3b: 추가 arc 프리셋 3종 (v11.2) ──
    "wave": {
        "description": "파동 — 두 개의 피크, 중간에 밸리. 이중 나선 구조(C)에 적합",
        "phases": [
            {
                "name": "rise1",
                "start_pct": 0.0,
                "end_pct": 0.25,
                "energy_range": (0.8, 1.1),
                "density_mult": 1.0,
            },
            {
                "name": "dip",
                "start_pct": 0.25,
                "end_pct": 0.45,
                "energy_range": (1.1, 0.6),
                "density_mult": 0.8,
            },
            {
                "name": "rise2",
                "start_pct": 0.45,
                "end_pct": 0.75,
                "energy_range": (0.6, 1.4),
                "density_mult": 1.3,
            },
            {
                "name": "fade",
                "start_pct": 0.75,
                "end_pct": 1.0,
                "energy_range": (1.0, 0.3),
                "density_mult": 0.6,
            },
        ],
    },
    "shockwave": {
        "description": "충격파 — 강한 시작, 긴 감쇠, 여진. 역순 각성 구조(B)에 적합",
        "phases": [
            {
                "name": "spike",
                "start_pct": 0.0,
                "end_pct": 0.15,
                "energy_range": (1.4, 1.5),
                "density_mult": 1.5,
            },
            {
                "name": "decay",
                "start_pct": 0.15,
                "end_pct": 0.55,
                "energy_range": (1.2, 0.6),
                "density_mult": 0.8,
            },
            {
                "name": "aftershock",
                "start_pct": 0.55,
                "end_pct": 0.75,
                "energy_range": (0.6, 0.9),
                "density_mult": 1.0,
            },
            {
                "name": "settle",
                "start_pct": 0.75,
                "end_pct": 1.0,
                "energy_range": (0.7, 0.2),
                "density_mult": 0.5,
            },
        ],
    },
    "staircase": {
        "description": "계단 — 점진적 4단계 상승. 3단계 변환 구조(A)의 점진형 변형",
        "phases": [
            {
                "name": "step1",
                "start_pct": 0.0,
                "end_pct": 0.25,
                "energy_range": (0.6, 0.7),
                "density_mult": 0.7,
            },
            {
                "name": "step2",
                "start_pct": 0.25,
                "end_pct": 0.50,
                "energy_range": (0.8, 0.9),
                "density_mult": 0.9,
            },
            {
                "name": "step3",
                "start_pct": 0.50,
                "end_pct": 0.75,
                "energy_range": (1.0, 1.2),
                "density_mult": 1.2,
            },
            {
                "name": "step4",
                "start_pct": 0.75,
                "end_pct": 1.0,
                "energy_range": (1.3, 1.0),
                "density_mult": 1.4,
            },
        ],
    },
}


# ============================================================
# 장르 프리셋 v11 — ENOMETA Single Genre: enometa (대본 리액티브 댄스 뮤직)
# 6장르 통합 → enometa 단일 장르 + 패턴 엔진
# ============================================================

GENRE_PRESETS = {
    "enometa": {
        # v12: BPM 135 고정 (가변 BPM 제거 — 한 곡 통일감, 최소 120)
        "bpm_override": 135,
        "volume_scale": {
            # v9: 리듬 레이어 볼륨 정상화 (거의 안 들리던 수준에서 탈출)
            "kick": 0.8,          # 강한 킥
            "hi_hat": 0.8,        # v12: 하이햇 존재감 강화 (0.5→0.8)
            "saw_sequence": 1.0,  # 쏘우파 시퀀서 메인
            "arpeggio": 0.5,      # 아르페지오 서포트
            "bass_drone": 0.4,    # 드론 서브
            "sub_pulse": 0.35,    # 서브 베이스
            # enometa 시그니처 텍스처
            "sine_interference": 0.8,
            "data_click": 0.9,
            "pulse_train": 0.7,
            "ultrahigh_texture": 0.6,
            "clicks": 0.6,
            # 절제된 레이어
            "bytebeat": 0.15,
            "feedback": 0.2,       # B-4: 기본 활성화 (볼륨 상한 0.3)
            "fm_bass": 0.15,       # B-4: 기본 활성화
            "chiptune_lead": 0, "chiptune_drum": 0,
            "synth_lead": 0.15, "acid_bass": 0.4,  # B-4: synth_lead 기본 활성화
        },
        "force_active": [
            "saw_sequence", "sine_interference", "data_click", "pulse_train",
        ],
        # v9: acid_bass + chiptune_lead 허용 (EMOTION_MAP에서 제어)
        "force_inactive": ["chiptune_lead", "chiptune_drum"],  # B-4: fm_bass, synth_lead 제거
        "synthesis_overrides": {
            "enometa_mode": True,
            "rhythm_mode": "euclidean",  # 유클리드 리듬 패턴 유지
        },
        "description": "ENOMETA v11 — 대본 리액티브 댄스 뮤직: 패턴 엔진 + 드럼 뼈대 + build/drop 문법",
    },
}


# ============================================================
# v12: 댄스 음악 편곡 테이블 — 곡 구조 role별 악기 편성
# smooth_envelope과 호환: instruments[key]["active"]=bool, instruments[key]["volume"]=float
# ============================================================

ARRANGEMENT_TABLE = {
    # role: 각 악기의 볼륨 (0이면 inactive)
    "intro": {
        "kick": 0.6, "hi_hat": 0.4, "snare": 0.0,
        "saw_sequence": 0.3, "arpeggio": 0.0, "bass_drone": 0.4, "fm_bass": 0.1,
        "sub_pulse": 0.2, "sine_interference": 0.3, "pulse_train": 0.2,
        "ultrahigh_texture": 0.0, "gate_stutter": 0.0,
        "data_click": 0.3, "clicks": 0.2,
        "feedback": 0.0, "bytebeat": 0.0, "synth_lead": 0.0, "acid_bass": 0.0,
    },
    "buildup": {
        "kick": 0.7, "hi_hat": 0.5, "snare": 0.0,
        "saw_sequence": 0.6, "arpeggio": 0.3, "bass_drone": 0.6, "fm_bass": 0.15,
        "sub_pulse": 0.3, "sine_interference": 0.5, "pulse_train": 0.4,
        "ultrahigh_texture": 0.2, "gate_stutter": 0.2,
        "data_click": 0.5, "clicks": 0.4,
        "feedback": 0.1, "bytebeat": 0.1, "synth_lead": 0.1, "acid_bass": 0.2,
    },
    "drop": {
        "kick": 1.0, "hi_hat": 0.6, "snare": 0.2,
        "saw_sequence": 1.0, "arpeggio": 0.7, "bass_drone": 0.8, "fm_bass": 0.2,
        "sub_pulse": 0.4, "sine_interference": 0.8, "pulse_train": 0.7,
        "ultrahigh_texture": 0.5, "gate_stutter": 0.4,
        "data_click": 0.8, "clicks": 0.6,
        "feedback": 0.15, "bytebeat": 0.15, "synth_lead": 0.15, "acid_bass": 0.4,
    },
    "breakdown": {
        "kick": 0.0, "hi_hat": 0.3, "snare": 0.0,
        "saw_sequence": 0.2, "arpeggio": 0.4, "bass_drone": 0.3, "fm_bass": 0.1,
        "sub_pulse": 0.15, "sine_interference": 0.4, "pulse_train": 0.2,
        "ultrahigh_texture": 0.1, "gate_stutter": 0.1,
        "data_click": 0.3, "clicks": 0.2,
        "feedback": 0.05, "bytebeat": 0.0, "synth_lead": 0.0, "acid_bass": 0.1,
    },
    "drop2": {
        "kick": 1.0, "hi_hat": 0.6, "snare": 0.25,
        "saw_sequence": 1.0, "arpeggio": 0.8, "bass_drone": 1.0, "fm_bass": 0.2,
        "sub_pulse": 0.4, "sine_interference": 0.8, "pulse_train": 0.7,
        "ultrahigh_texture": 0.6, "gate_stutter": 0.5,
        "data_click": 0.9, "clicks": 0.6,
        "feedback": 0.2, "bytebeat": 0.15, "synth_lead": 0.15, "acid_bass": 0.4,
    },
    "outro": {
        "kick": 0.4, "hi_hat": 0.3, "snare": 0.0,
        "saw_sequence": 0.15, "arpeggio": 0.0, "bass_drone": 0.3, "fm_bass": 0.1,
        "sub_pulse": 0.1, "sine_interference": 0.2, "pulse_train": 0.1,
        "ultrahigh_texture": 0.0, "gate_stutter": 0.0,
        "data_click": 0.2, "clicks": 0.1,
        "feedback": 0.0, "bytebeat": 0.0, "synth_lead": 0.0, "acid_bass": 0.0,
    },
}

# role별 에너지 (song_arc에 사용)
ROLE_ENERGY = {
    "intro": 0.5, "buildup": 0.8, "drop": 1.0,
    "breakdown": 0.4, "drop2": 1.0, "outro": 0.3,
}

# role별 바 수 비율 (전체 대비). 합계 = 72바 기준
# 짧은 영상(~60초)은 비례 축소, 긴 영상(~140초)은 비례 확대
ROLE_BAR_RATIOS = [
    ("intro",     8),
    ("buildup",  16),
    ("drop",     16),
    ("breakdown", 8),
    ("drop2",    16),
    ("outro",     8),
]


# ============================================================
# 키 프리셋 및 우선순위
# ============================================================

KEY_PRESETS = {
    "C_minor":  {"bass_freq": 65.4, "pad_root": 261.6, "pad_fifth": 392.0, "arp_root": 196.0},
    "D_minor":  {"bass_freq": 73.4, "pad_root": 293.7, "pad_fifth": 440.0, "arp_root": 220.0},
    "E_minor":  {"bass_freq": 82.4, "pad_root": 329.6, "pad_fifth": 493.9, "arp_root": 220.0},
    "F_minor":  {"bass_freq": 87.3, "pad_root": 349.2, "pad_fifth": 523.3, "arp_root": 233.1},
    "G_minor":  {"bass_freq": 98.0, "pad_root": 392.0, "pad_fifth": 587.3, "arp_root": 261.6},
    "A_minor":  {"bass_freq": 110.0, "pad_root": 440.0, "pad_fifth": 659.3, "arp_root": 293.7},
    "Bb_minor": {"bass_freq": 116.5, "pad_root": 466.2, "pad_fifth": 698.5, "arp_root": 311.1},
}

# 키 선택 우선순위 (일반적으로 어둡고 깊은 키 우선)
KEY_PRIORITY = ["E_minor", "D_minor", "G_minor", "A_minor", "C_minor", "F_minor", "Bb_minor"]


# ============================================================
# v8 C-6: TEXTURE_MODULES — 에피소드 간 텍스처 다양화
# ============================================================

AVAILABLE_TEXTURE_MODULES = [
    "euclidean_rhythm",    # 유클리드 리듬 패턴 활용
    "feedback_texture",    # 피드백 루프 텍스처
    "bytebeat_texture",    # 바이트비트 디지털 텍스처
    "melodic_sequence",    # 사인파 멜로디 시퀀스
    "rhythm_backbone",     # 킥/하이햇 리듬 뼈대
]


# ============================================================
# v15: MUSIC_MOOD_PRESETS — 8종 무드별 레이어 조합
# narration_timing.json의 "music_mood" 필드로 선택
# ============================================================

MUSIC_MOOD_PRESETS = {
    "ambient": {
        "bpm_range": (80, 100),
        "drum_default": False,
        "layers": {
            "bass_drone":        {"active": True,  "volume": 0.8},
            "sine_interference": {"active": True,  "volume": 0.5},
            "pulse_train":       {"active": True,  "volume": 0.4},
            "fm_bass":           {"active": False},
            "saw_sequence":      {"active": False},
            "arpeggio":          {"active": False},
            "kick":              {"active": False},
            "snare":             {"active": False},
            "hi_hat":            {"active": False},
            "gate_stutter":      {"active": False},
            "gap_burst":         {"active": False},
            "ultrahigh_texture": {"active": False},
            "feedback":          {"active": False},
            "data_click":        {"active": False},
        },
        "description": "순수 공간감. 드럼 없음. transcendent_open 계열.",
    },
    "ikeda": {
        "bpm_range": (100, 120),
        "drum_default": False,
        "layers": {
            "sine_interference": {"active": True,  "volume": 0.6},
            "data_click":        {"active": True,  "volume": 0.5},
            "pulse_train":       {"active": True,  "volume": 0.45},
            "ultrahigh_texture": {"active": True,  "volume": 0.3},
            "bass_drone":        {"active": True,  "volume": 0.4},
            "fm_bass":           {"active": False},
            "saw_sequence":      {"active": False},
            "arpeggio":          {"active": False},
            "kick":              {"active": False},
            "snare":             {"active": False},
            "hi_hat":            {"active": False},
            "gate_stutter":      {"active": False},
            "gap_burst":         {"active": False},
            "feedback":          {"active": False},
        },
        "description": "Ryoji Ikeda microsound. 사인파+클릭+펄스. 드럼 없음 기본.",
    },
    "experimental": {
        "bpm_range": (120, 150),
        "drum_default": True,
        "drum_pattern": "irregular",
        "layers": {
            "gate_stutter":      {"active": True,  "volume": 0.7},
            "feedback":          {"active": True,  "volume": 0.5},
            "data_click":        {"active": True,  "volume": 0.6},
            "gap_burst":         {"active": True,  "volume": 0.8},
            "kick":              {"active": True,  "volume": 0.6, "pattern": "irregular"},
            "snare":             {"active": True,  "volume": 0.4, "pattern": "irregular"},
            "hi_hat":            {"active": True,  "volume": 0.3, "pattern": "irregular"},
            "bass_drone":        {"active": True,  "volume": 0.4},
            "sine_interference": {"active": True,  "volume": 0.4},
            "saw_sequence":      {"active": False},
            "arpeggio":          {"active": False},
            "ultrahigh_texture": {"active": True,  "volume": 0.3},
            "fm_bass":           {"active": False},
            "pulse_train":       {"active": False},
        },
        "description": "비선형 패턴, 불규칙 리듬. 위험한 텍스처.",
    },
    "minimal": {
        "bpm_range": (90, 110),
        "drum_default": True,
        "layers": {
            "fm_bass":           {"active": True,  "volume": 0.6},
            "bass_drone":        {"active": True,  "volume": 0.5},
            "arpeggio":          {"active": True,  "volume": 0.4, "speed": 0.3},
            "kick":              {"active": True,  "volume": 0.4},
            "snare":             {"active": False},
            "hi_hat":            {"active": False},
            "saw_sequence":      {"active": False},
            "sine_interference": {"active": False},
            "gate_stutter":      {"active": False},
            "gap_burst":         {"active": False},
            "feedback":          {"active": False},
            "data_click":        {"active": False},
            "ultrahigh_texture": {"active": False},
            "pulse_train":       {"active": False},
        },
        "description": "공간감 중심. raw보다 조용하나 비어있지 않음. 미드나잇 드라이브.",
    },
    "chill": {
        "bpm_range": (100, 120),
        "drum_default": True,
        "layers": {
            "kick":              {"active": True,  "volume": 0.45},
            "arpeggio":          {"active": True,  "volume": 0.6, "speed": 0.4},
            "bass_drone":        {"active": True,  "volume": 0.55},
            "saw_sequence":      {"active": True,  "volume": 0.3},
            "fm_bass":           {"active": True,  "volume": 0.4},
            "hi_hat":            {"active": True,  "volume": 0.2},
            "snare":             {"active": False},
            "gate_stutter":      {"active": False},
            "gap_burst":         {"active": False},
            "feedback":          {"active": False},
            "sine_interference": {"active": False},
            "data_click":        {"active": False},
            "ultrahigh_texture": {"active": False},
            "pulse_train":       {"active": False},
        },
        "description": "부드러운 리듬. arpeggio 중심. 경량 킥.",
    },
    "glitch": {
        "bpm_range": (120, 140),
        "drum_default": True,
        "drum_pattern": "irregular",
        "layers": {
            "kick":              {"active": True,  "volume": 0.5, "pattern": "irregular"},
            "gate_stutter":      {"active": True,  "volume": 0.8},
            "gap_burst":         {"active": True,  "volume": 0.7},
            "data_click":        {"active": True,  "volume": 0.65},
            "bass_drone":        {"active": True,  "volume": 0.4},
            "snare":             {"active": False},
            "hi_hat":            {"active": False},
            "saw_sequence":      {"active": False},
            "arpeggio":          {"active": False},
            "fm_bass":           {"active": False},
            "sine_interference": {"active": False},
            "feedback":          {"active": False},
            "ultrahigh_texture": {"active": False},
            "pulse_train":       {"active": False},
        },
        "description": "디지털 에러 미학. 불규칙 킥+스터터+갭버스트.",
    },
    "raw": {
        "bpm_range": (128, 148),
        "drum_default": True,
        "layers": {
            "kick":              {"active": True,  "volume": 0.7},
            "snare":             {"active": True,  "volume": 0.55},
            "hi_hat":            {"active": True,  "volume": 0.35},
            "saw_sequence":      {"active": True,  "volume": 0.7},
            "arpeggio":          {"active": True,  "volume": 0.45},
            "bass_drone":        {"active": True,  "volume": 0.5},
            "fm_bass":           {"active": True,  "volume": 0.3},
            "gate_stutter":      {"active": True,  "volume": 0.4},
            "gap_burst":         {"active": True,  "volume": 0.5},
            "sine_interference": {"active": False},
            "data_click":        {"active": False},
            "ultrahigh_texture": {"active": False},
            "feedback":          {"active": False},
            "pulse_train":       {"active": False},
        },
        "description": "현재 기본 스타일. Matrix 레퍼런스. 킥+스네어+saw+arp.",
    },
    "intense": {
        "bpm_range": (135, 162),
        "drum_default": True,
        "layers": {
            "kick":              {"active": True,  "volume": 0.85},
            "snare":             {"active": True,  "volume": 0.7},
            "hi_hat":            {"active": True,  "volume": 0.45},
            "saw_sequence":      {"active": True,  "volume": 0.8},
            "arpeggio":          {"active": True,  "volume": 0.6},
            "bass_drone":        {"active": True,  "volume": 0.6},
            "fm_bass":           {"active": True,  "volume": 0.5},
            "gate_stutter":      {"active": True,  "volume": 0.6},
            "gap_burst":         {"active": True,  "volume": 0.7},
            "ultrahigh_texture": {"active": True,  "volume": 0.4},
            "feedback":          {"active": True,  "volume": 0.4},
            "sine_interference": {"active": False},
            "data_click":        {"active": False},
            "pulse_train":       {"active": False},
        },
        "description": "각성/클라이맥스. 전 레이어 풀 출력. 필인 풍부.",
    },
}

# 기본 무드
DEFAULT_MUSIC_MOOD = "raw"


# ============================================================
# v15: CRASH_RULES — 무드별 크러쉬/히트음 위치
# crash_at_bars: 해당 마디에 transition_impact() 삽입
# hit_density: 마디당 추가 metallic_hit 확률
# ============================================================

CRASH_RULES = {
    "ambient":      {"crash_at_bars": [],              "hit_density": 0.00},
    "ikeda":        {"crash_at_bars": [32],             "hit_density": 0.05},
    "experimental": {"crash_at_bars": [8, 16, 24],     "hit_density": 0.15},
    "minimal":      {"crash_at_bars": [32],             "hit_density": 0.00},
    "chill":        {"crash_at_bars": [16, 32],         "hit_density": 0.05},
    "glitch":       {"crash_at_bars": [8, 12, 16],      "hit_density": 0.20},
    "raw":          {"crash_at_bars": [16, 32],         "hit_density": 0.10},
    "intense":      {"crash_at_bars": [8, 16, 24, 32],  "hit_density": 0.25},
}


# ============================================================
# v15: FILL_RULES — 무드별 필인 빈도
# fill_every_bars: N마디마다 필인 (0=없음)
# fill_intensity: 필인 강도 (0~1)
# ============================================================

FILL_RULES = {
    "ambient":      {"fill_every_bars": 0,   "fill_intensity": 0.0},
    "ikeda":        {"fill_every_bars": 32,  "fill_intensity": 0.3},
    "experimental": {"fill_every_bars": 4,   "fill_intensity": 0.9},
    "minimal":      {"fill_every_bars": 0,   "fill_intensity": 0.0},
    "chill":        {"fill_every_bars": 16,  "fill_intensity": 0.4},
    "glitch":       {"fill_every_bars": 6,   "fill_intensity": 0.7},
    "raw":          {"fill_every_bars": 8,   "fill_intensity": 0.6},
    "intense":      {"fill_every_bars": 4,   "fill_intensity": 0.8},
}


# ============================================================
# v15: GAP_FILL_INTENSITY — 무드별 드롭 구간 채우기 강도
# 0: 순수 침묵 / 1.0: 최대 stutter+burst
# ============================================================

GAP_FILL_INTENSITY = {
    "ambient":      0.0,   # 순수 침묵 유지
    "ikeda":        0.3,   # data_click + pulse_train 미세 삽입
    "experimental": 1.0,   # 최대 stutter + feedback burst
    "minimal":      0.1,   # 경량 베이스만
    "chill":        0.3,   # 부드러운 갭버스트
    "glitch":       0.8,   # 강한 stutter
    "raw":          0.6,   # gap_burst + 짧은 stutter
    "intense":      0.9,   # 풀 gap_burst + impact
}
