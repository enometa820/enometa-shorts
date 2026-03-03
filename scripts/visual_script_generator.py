"""
ENOMETA 비주얼 스크립트 자동 생성기
- 대본(script.txt) + 나레이션 타이밍(narration_timing.json) → visual_script.json
- 문장별 키워드 분석 → 감정 매핑 → 비주얼 어휘 자동 배정
- 에피소드마다 다른 조합이 나오도록 시드 기반 랜덤
"""

import sys
import os
import json
import random
import re
from typing import List, Dict, Any, Tuple, Optional

# 같은 scripts/ 디렉토리에서 임포트
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visual_strategies import (
    get_strategy, get_default_strategy, boost_reactivity,
)

# ============================================================
# 팔레트 정의 (src/utils/palettes.ts와 동기화)
# ============================================================
PALETTES = {
    "phantom": {
        "bg": "#06060A",
        "accent": "#8B5CF6",
        "glow": "#7C3AED",
        "colors": ["#8B5CF6", "#C084FC", "#06B6D4", "#F43F5E"],
        "particles": ["#FFFFFF", "#C8C8D0", "#8888AA", "#555577", "#AAAACC"],
    },
    "neon_noir": {
        "bg": "#0A0A0F",
        "accent": "#00F5D4",
        "glow": "#00D4B8",
        "colors": ["#00F5D4", "#FF006E", "#3A86FF", "#FFBE0B"],
        "particles": ["#FFFFFF", "#D0D0D8", "#88AAAA", "#557777", "#AACCCC"],
    },
    "cold_steel": {
        "bg": "#080810",
        "accent": "#64748B",
        "glow": "#475569",
        "colors": ["#64748B", "#94A3B8", "#CBD5E1", "#E2E8F0"],
        "particles": ["#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#475569"],
    },
    "ember": {
        "bg": "#0A0604",
        "accent": "#F97316",
        "glow": "#EA580C",
        "colors": ["#F97316", "#EF4444", "#FBBF24", "#DC2626"],
        "particles": ["#FFFFFF", "#FFD4AA", "#FFAA77", "#CC7744", "#AA5522"],
    },
    "synapse": {
        "bg": "#060A08",
        "accent": "#10B981",
        "glow": "#059669",
        "colors": ["#10B981", "#06B6D4", "#8B5CF6", "#F43F5E"],
        "particles": ["#FFFFFF", "#C8D0CC", "#88AA99", "#557766", "#AACCBB"],
    },
    "gameboy": {
        "bg": "#0f380f",
        "accent": "#9bbc0f",
        "glow": "#8bac0f",
        "colors": ["#9bbc0f", "#8bac0f", "#306230", "#0f380f"],
        "particles": ["#9bbc0f", "#8bac0f", "#306230", "#0f380f", "#9bbc0f"],
    },
    "c64": {
        "bg": "#40318D",
        "accent": "#A59ADE",
        "glow": "#7869C4",
        "colors": ["#A59ADE", "#7869C4", "#FFFFFF", "#FFFACD"],
        "particles": ["#7869C4", "#A59ADE", "#FFFFFF", "#6C5EB5", "#FFFACD"],
    },
    "ikeda": {
        "bg": "#000000",
        "accent": "#FFFFFF",
        "glow": "#CCCCCC",
        "colors": ["#FFFFFF", "#AAAAAA", "#555555", "#222222"],
        "particles": ["#FFFFFF", "#CCCCCC", "#888888", "#444444", "#222222"],
    },
}

# ============================================================
# 비주얼 어휘 레지스트리 (23개)
# ============================================================
# 카테고리별로 분류 — 자동 매핑 시 카테고리 기반 선택
VOCAB_CATEGORIES = {
    "particle": [
        "particle_birth", "particle_scatter", "particle_converge",
        "particle_orbit", "particle_escape", "particle_chain_awaken",
        "particle_split_ratio",
    ],
    "text": ["text_reveal"],  # mode: wave/glitch/scatter/typewriter
    "grid": ["grid_morph", "grid_mesh"],
    "network": ["neural_network"],
    "ring": ["loop_ring"],
    "fractal": ["fractal_crack"],
    "data": ["data_bar", "data_ring", "counter_up"],
    "waveform": ["waveform", "waveform_spectrum", "waveform_circular"],
    "color": ["color_shift", "color_drain", "color_bloom",
              "color_shift_warm", "color_shift_cold"],
    "light": ["brightness_pulse", "light_source"],
    "pixel": [
        "pixel_grid", "pixel_grid_outline", "pixel_grid_life", "pixel_grid_rain",
        "pixel_waveform", "pixel_waveform_steps", "pixel_waveform_cascade",
    ],
}

# ============================================================
# Variant 레지스트리 — 각 vocab별 사용 가능한 variant 목록
# ============================================================
VARIANT_REGISTRY = {
    "particle_birth": ["default", "triangles_rise", "lines_scatter", "dots_grid"],
    "particle_scatter": ["default", "directional_wind", "spiral_out"],
    "particle_converge": ["default", "multi_point", "collapse_line"],
    "particle_orbit": ["default", "ellipse_drift", "figure_eight"],
    "particle_escape": ["default", "chain_break", "explosion"],
    "fractal_crack": ["default", "edge_shatter", "web_crack"],
    "neural_network": ["default", "tree_branch", "constellation"],
    "flow_field_calm": ["default", "vortex", "opposing"],
    "flow_field_turbulent": ["default", "vortex", "opposing"],
    "grid_morph": ["default", "wave_propagation", "pixel_dissolve"],
    "grid_mesh": ["default", "wave_propagation", "pixel_dissolve"],
}


def select_variant(vocab: str, rng: random.Random, recent_used: set = None) -> Optional[str]:
    """vocab에 대한 variant를 선택. variant가 없는 vocab은 None 반환."""
    variants = VARIANT_REGISTRY.get(vocab)
    if not variants:
        return None

    # 최근 사용된 조합 회피
    if recent_used:
        preferred = [v for v in variants if f"{vocab}:{v}" not in recent_used]
        if preferred:
            return rng.choice(preferred)

    return rng.choice(variants)


# ============================================================
# Vocab 이력 추적 (에피소드 간 중복 회피)
# ============================================================
HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vocab_history.json")


def load_vocab_history() -> Dict[str, Any]:
    """vocab_history.json 로드 (없으면 빈 구조 반환)"""
    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"episodes": {}}


def save_vocab_history(history: Dict[str, Any]) -> None:
    """vocab_history.json 저장"""
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_recent_used(history: Dict[str, Any], lookback: int = 2) -> set:
    """최근 lookback개 에피소드에서 사용된 vocab:variant 조합 반환"""
    episodes = history.get("episodes", {})
    # 에피소드 키를 정렬해서 최근 N개 선택
    sorted_eps = sorted(episodes.keys(), reverse=True)[:lookback]
    recent = set()
    for ep_key in sorted_eps:
        for combo in episodes[ep_key].get("used_combos", []):
            recent.add(combo)
    return recent


def record_episode_history(history: Dict[str, Any], episode_id: str, scenes: List[Dict]) -> None:
    """에피소드의 vocab:variant 사용 이력 기록"""
    combos = set()
    for scene in scenes:
        for entry in scene.get("layers", {}).get("semantic", []):
            vocab = entry.get("vocab", "")
            variant = entry.get("variant", "default")
            combos.add(f"{vocab}:{variant}")
        bg = scene.get("layers", {}).get("background", {})
        if bg.get("variant"):
            combos.add(f"{bg['vocab']}:{bg['variant']}")
    history.setdefault("episodes", {})[episode_id] = {
        "used_combos": sorted(combos),
    }


# ============================================================
# 장르 → 비주얼 오버라이드 (8bit 장르에서 픽셀 비주얼 주입)
# ============================================================
GENRE_VISUAL_OVERRIDES = {
    "bytebeat": {
        "palette": "gameboy",
        "inject_vocabs": [
            "pixel_grid", "pixel_grid_life", "pixel_grid_rain",
            "pixel_waveform_steps", "pixel_waveform_cascade",
        ],
        "inject_chance": 0.7,  # 70% 확률로 8bit 비주얼 삽입
        "force_bg_pixel": True,  # 배경에도 pixel_grid 사용
    },
    "chiptune": {
        "palette": "gameboy",
        "inject_vocabs": [
            "pixel_grid", "pixel_grid_outline", "pixel_grid_life",
            "pixel_waveform", "pixel_waveform_steps",
        ],
        "inject_chance": 0.6,
        "force_bg_pixel": False,
    },
    "algorave": {
        "palette": "neon_noir",
        "inject_vocabs": ["pixel_grid_rain", "pixel_waveform_cascade"],
        "inject_chance": 0.3,
        "force_bg_pixel": False,
    },
    "harsh_noise": {
        "palette": "cold_steel",
        "inject_vocabs": ["pixel_grid_life", "pixel_waveform_cascade"],
        "inject_chance": 0.2,
        "force_bg_pixel": False,
    },
    # techno: 기본 비주얼 유지, 오버라이드 없음
    "ikeda": {
        "palette": "ikeda",
        "inject_vocabs": ["pixel_grid_rain", "pixel_grid_life", "pixel_waveform_cascade"],
        "inject_chance": 0.25,  # 씬의 25% 확률로 8bit 격자/파형 등장
        "force_bg_pixel": False,
    },
}

# ============================================================
# 감정 키워드 사전 (한국어)
# ============================================================
EMOTION_KEYWORDS = {
    "neutral_curious": [
        "떠올려", "생각해", "상상해", "무엇", "어떤", "왜", "질문", "궁금",
        "보자", "살펴", "어쩌면", "혹시", "가능", "한번",
    ],
    "tension_reveal": [
        "않는다", "아니다", "사실", "진실", "밝혀", "드러나", "반전",
        "충격", "놀라", "실제", "정체", "폭로", "깨달", "다시",
    ],
    "neutral_analytical": [
        "과학", "연구", "이론", "분석", "데이터", "시스템", "구조",
        "메커니즘", "원리", "법칙", "증명", "실험", "뇌", "신경",
    ],
    "somber_reflective": [
        "슬프", "아프", "잃", "사라", "그리", "외로", "고독",
        "과거", "추억", "기억", "따뜻", "차갑", "같다", "변하",
    ],
    "somber_warning": [
        "위험", "경고", "주의", "조심", "함부로", "치명", "위협",
        "독", "해로", "파괴", "무너", "무서", "공포", "두려",
    ],
    "awakening_spark": [
        "깨닫", "발견", "찾", "알게", "보이", "눈뜨", "자각",
        "인식", "의식", "새로", "처음", "비로소", "순간",
    ],
    "tension_transformative": [
        "변환", "전환", "바꾸", "변화", "달라", "진화", "성장",
        "극복", "넘어", "돌파", "혁신", "혁명", "전복",
    ],
    "tension_redefine": [
        "재정의", "다시 정의", "새롭게", "재해석", "의미", "본질",
        "정의", "규정", "재구성", "재조합", "리셋",
    ],
    "hopeful": [
        "희망", "빛", "미래", "가능", "꿈", "나아", "앞으로",
        "열리", "시작", "기회", "좋", "아름다", "따뜻",
    ],
    "awakening_climax": [
        "최고", "절정", "폭발", "극대", "최대", "가장", "궁극",
        "완전", "절대", "정점", "클라이맥스",
    ],
    "transcendent_open": [
        "초월", "넘어서", "경계", "무한", "영원", "자유",
        "존재", "우주", "세계", "차원", "열린", "끝없",
    ],
}

# ============================================================
# 감정 → 비주얼 어휘 풀 매핑
# ============================================================
EMOTION_VOCAB_POOL = {
    "neutral_curious": {
        "primary": ["particle_birth", "particle_orbit", "flow_field_calm"],
        "secondary": ["waveform", "counter_up", "brightness_pulse"],
        "text_mode": "wave",
        "bg_mode": "calm",
        "reactivity": "low",
    },
    "tension_reveal": {
        "primary": ["particle_scatter", "neural_network", "fractal_crack"],
        "secondary": ["grid_morph", "waveform_spectrum", "color_shift"],
        "text_mode": "glitch",
        "bg_mode": "turbulent",
        "reactivity": "high",
    },
    "neutral_analytical": {
        "primary": ["grid_morph", "data_bar", "neural_network"],
        "secondary": ["waveform_spectrum", "counter_up", "grid_mesh"],
        "text_mode": "typewriter",
        "bg_mode": "calm",
        "reactivity": "medium",
    },
    "somber_reflective": {
        "primary": ["particle_converge", "color_shift", "flow_field_calm"],
        "secondary": ["loop_ring", "brightness_pulse", "light_source"],
        "text_mode": "wave",
        "bg_mode": "calm",
        "reactivity": "low",
    },
    "somber_warning": {
        "primary": ["fractal_crack", "color_drain", "particle_scatter"],
        "secondary": ["waveform", "data_bar", "grid_morph"],
        "text_mode": "glitch",
        "bg_mode": "turbulent",
        "reactivity": "high",
    },
    "awakening_spark": {
        "primary": ["particle_escape", "light_source", "particle_chain_awaken"],
        "secondary": ["brightness_pulse", "color_bloom", "waveform_circular"],
        "text_mode": "scatter",
        "bg_mode": "calm",
        "reactivity": "medium",
    },
    "tension_transformative": {
        "primary": ["grid_morph", "particle_split_ratio", "fractal_crack"],
        "secondary": ["neural_network", "waveform_spectrum", "color_shift"],
        "text_mode": "glitch",
        "bg_mode": "turbulent",
        "reactivity": "high",
    },
    "tension_redefine": {
        "primary": ["particle_split_ratio", "grid_mesh", "data_bar"],
        "secondary": ["loop_ring", "color_shift", "waveform"],
        "text_mode": "glitch",
        "bg_mode": "turbulent",
        "reactivity": "high",
    },
    "hopeful": {
        "primary": ["light_source", "particle_converge", "color_bloom"],
        "secondary": ["brightness_pulse", "particle_orbit", "waveform_circular"],
        "text_mode": "wave",
        "bg_mode": "calm",
        "reactivity": "medium",
    },
    "awakening_climax": {
        "primary": ["particle_chain_awaken", "particle_escape", "fractal_crack"],
        "secondary": ["waveform_circular", "brightness_pulse", "light_source"],
        "text_mode": "scatter",
        "bg_mode": "turbulent",
        "reactivity": "max",
    },
    "transcendent_open": {
        "primary": ["particle_orbit", "light_source", "flow_field_calm"],
        "secondary": ["color_bloom", "brightness_pulse", "waveform_circular"],
        "text_mode": "wave",
        "bg_mode": "calm",
        "reactivity": "medium",
    },
}

# ============================================================
# 오디오 리액티비티 프리셋
# ============================================================
REACTIVITY_PRESETS = {
    "low": {
        "particle_opacity": "rms * 0.7 + 0.3",
        "particle_size": "bass * 3 + 1",
        "glow_intensity": "rms * 0.8",
    },
    "medium": {
        "particle_opacity": "rms * 0.8 + 0.2",
        "particle_size": "bass * 4 + 1",
        "glow_intensity": "bass * 3",
        "displacement": "rms * 3",
    },
    "high": {
        "particle_opacity": "rms * 0.9 + 0.1",
        "particle_size": "bass * 5 + 1",
        "glow_intensity": "bass * 5",
        "displacement": "bass * 4",
        "speed_mult": "onset ? 4 : 1",
    },
    "max": {
        "particle_opacity": "rms * 0.95 + 0.05",
        "particle_size": "bass * 7 + 1",
        "glow_intensity": "bass * 7",
        "displacement": "bass * 5",
        "speed_mult": "onset ? 6 : 1",
        "glitch_trigger": "onset ? 12 : 0",
    },
}


# ============================================================
# 핵심 함수들
# ============================================================

def detect_emotion(sentence: str, prev_emotion: str = "") -> str:
    """문장 내용을 분석하여 감정을 자동 감지"""
    scores: Dict[str, int] = {}
    sentence_lower = sentence.lower()

    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in sentence_lower:
                score += 1
        if score > 0:
            scores[emotion] = score

    if not scores:
        # 키워드 매칭 없으면 문장 위치 기반 기본값
        return "neutral_curious"

    # 최고 점수 감정 선택 (동점이면 랜덤)
    max_score = max(scores.values())
    candidates = [e for e, s in scores.items() if s == max_score]

    # 이전 감정과 다른 것 선호
    if prev_emotion in candidates and len(candidates) > 1:
        candidates.remove(prev_emotion)

    return random.choice(candidates)


def extract_highlight_word(sentence: str) -> Optional[str]:
    """문장에서 핵심 키워드(한글 명사) 추출 — 텍스트 비주얼용"""
    # 한자어/전문용어 우선 (2~4글자, 조사 앞)
    patterns = [
        r'([가-힣]{2,4})(?:이?라|을|를|은|는|이|가|의|에|도|만|와|과|로|으로)',
        r'([가-힣]{2,4})(?:하다|한다|된다|이다|하는|되는|인)',
    ]
    candidates = []
    for p in patterns:
        matches = re.findall(p, sentence)
        # findall with groups returns group(1) directly
        candidates.extend(matches)

    # 일반적인 단어 제외
    stopwords = {"우리", "그것", "이것", "자기", "자신", "모든", "하나",
                 "지금", "여기", "거기", "어디", "누구", "무엇",
                 "때문", "사이", "안에", "밖에", "위에", "아래"}
    candidates = [w for w in candidates if w not in stopwords and len(w) >= 2]

    if candidates:
        return candidates[0]
    return None


def generate_vocab_params(vocab: str, palette: dict, rng: random.Random) -> dict:
    """비주얼 어휘에 맞는 파라미터 자동 생성"""
    colors = palette["colors"]
    accent = palette["accent"]
    glow = palette["glow"]

    R = lambda x: round(x, 3)  # 소수점 3자리

    if vocab == "particle_birth":
        return {
            "count": rng.choice([600, 800, 1000, 1200]),
            "spawn_duration_sec": R(rng.uniform(2.0, 4.0)),
            "spawn_pattern": rng.choice(["center_burst", "random", "edges"]),
            "initial_color": rng.choice(colors),
            "size_range": [1, rng.choice([3, 4, 5])],
        }
    elif vocab == "particle_scatter":
        return {
            "count": rng.choice([300, 500, 700]),
            "color": rng.choice(colors),
            "glow": True,
            "expansion_speed": R(rng.uniform(1.0, 2.5)),
        }
    elif vocab == "particle_converge":
        return {
            "count": rng.choice([400, 600, 800]),
            "color": rng.choice(colors),
            "target": "center",
            "speed": R(rng.uniform(0.5, 1.5)),
        }
    elif vocab == "particle_orbit":
        return {
            "count": rng.choice([300, 500]),
            "color": accent,
            "rings": rng.choice([3, 4, 5]),
            "speed": R(rng.uniform(0.3, 0.8)),
        }
    elif vocab == "particle_escape":
        return {
            "count": rng.choice([500, 800, 1000]),
            "color": accent,
            "burst_speed": R(rng.uniform(2.0, 4.0)),
            "glow": True,
        }
    elif vocab == "particle_chain_awaken":
        return {
            "count": rng.choice([400, 600]),
            "color": accent,
            "chain_speed": R(rng.uniform(1.0, 2.0)),
            "glow_color": glow,
        }
    elif vocab == "particle_split_ratio":
        return {
            "count": rng.choice([500, 700]),
            "ratio": rng.choice([0.5, 0.618, 0.75, 0.95]),
            "color_a": colors[0],
            "color_b": colors[1] if len(colors) > 1 else colors[0],
        }
    elif vocab == "neural_network":
        return {
            "count": rng.choice([40, 60, 80]),
            "color": accent,
        }
    elif vocab in ("grid_morph", "grid_mesh"):
        return {
            "cols": rng.choice([15, 20, 25]),
            "rows": rng.choice([15, 20, 25]),
            "mode": "mesh" if "mesh" in vocab else rng.choice(["dots", "lines", "mesh", "wave"]),
            "color": rng.choice(palette["particles"]),
            "accentColor": accent,
            "morphIntensity": R(rng.uniform(0.5, 1.2)),
            "showConnections": rng.random() > 0.4,
        }
    elif vocab == "loop_ring":
        return {
            "rings": rng.choice([4, 6, 8]),
            "color": accent,
            "pulse_speed": R(rng.uniform(0.5, 1.5)),
        }
    elif vocab == "fractal_crack":
        return {
            "depth": rng.choice([4, 5, 6]),
            "color": accent,
            "spread": R(rng.uniform(0.5, 1.0)),
        }
    elif vocab in ("data_bar", "data_ring"):
        return {
            "bars": rng.choice([8, 12, 16, 20]),
            "color": accent,
            "mode": "ring" if "ring" in vocab else "vertical",
        }
    elif vocab == "counter_up":
        return {
            "target": rng.choice([95, 100, 1000, 99.7]),
            "suffix": rng.choice(["%", "", "x"]),
            "color": accent,
            "fontSize": rng.choice([48, 64, 80]),
        }
    elif vocab.startswith("waveform"):
        mode = "waveform"
        if "spectrum" in vocab:
            mode = "spectrum"
        elif "circular" in vocab:
            mode = "circular"
        return {
            "mode": mode,
            "color": accent,
            "lineWidth": rng.choice([1.5, 2, 3]),
            "sensitivity": R(rng.uniform(1.0, 2.0)),
        }
    elif vocab.startswith("color_"):
        return {
            "from_color": colors[0],
            "to_color": colors[-1],
            "rhythm": rng.choice(["slow", "breath", "pulse"]),
        }
    elif vocab == "brightness_pulse":
        return {
            "intensity": R(rng.uniform(0.3, 0.8)),
            "color": glow,
        }
    elif vocab == "light_source":
        return {
            "rays": rng.choice([12, 16, 20]),
            "color": accent,
            "intensity": R(rng.uniform(0.4, 0.8)),
            "position": rng.choice(["center", "top", "bottom"]),
        }
    elif vocab == "text_reveal":
        return {
            "text": "",
            "mode": "wave",
            "fontSize": rng.choice([48, 56, 64, 72]),
            "color": accent,
            "position": "center",
            "glowColor": glow,
        }
    # --- 8bit / 레트로 비주얼 ---
    elif vocab.startswith("pixel_grid"):
        mode_map = {
            "pixel_grid": "fill",
            "pixel_grid_outline": "outline",
            "pixel_grid_life": "life",
            "pixel_grid_rain": "rain",
        }
        return {
            "cols": rng.choice([24, 32, 40]),
            "rows": rng.choice([24, 32, 40]),
            "mode": mode_map.get(vocab, "fill"),
            "colors": colors[:4],
            "pixelGap": rng.choice([1, 2]),
            "reactivity": round(rng.uniform(0.8, 1.5), 2),
        }
    elif vocab.startswith("pixel_waveform"):
        mode_map = {
            "pixel_waveform": "bars",
            "pixel_waveform_steps": "steps",
            "pixel_waveform_cascade": "cascade",
        }
        return {
            "bars": rng.choice([12, 16, 20, 24]),
            "colors": colors[:4],
            "mode": mode_map.get(vocab, "bars"),
            "quantize": rng.choice([6, 8, 10]),
            "mirror": rng.random() > 0.3,
            "position": rng.choice(["center", "bottom"]),
        }

    return {}


def generate_background(emotion: str, palette: dict, rng: random.Random, scene_idx: int) -> dict:
    """감정에 따른 배경 생성"""
    pool = EMOTION_VOCAB_POOL.get(emotion, EMOTION_VOCAB_POOL["neutral_curious"])
    bg_mode = pool.get("bg_mode", "calm")

    vocab = f"flow_field_{bg_mode}"
    speed = 0.05 if bg_mode == "calm" else rng.uniform(0.15, 0.3)
    noise_scale = rng.uniform(0.002, 0.005) if bg_mode == "calm" else rng.uniform(0.004, 0.008)

    bg: Dict[str, Any] = {
        "vocab": vocab,
        "params": {
            "noise_scale": round(noise_scale, 4),
            "speed": round(speed, 3),
            "line_opacity": round(rng.uniform(0.04, 0.1), 3),
            "line_color": rng.choice(palette["particles"][-3:]),
        },
    }
    # 배경에도 variant 적용 (확률적)
    bg_variant = select_variant(vocab, rng)
    if bg_variant and bg_variant != "default" and rng.random() > 0.5:
        bg["variant"] = bg_variant

    # 일부 씬에서 배경 전환
    if bg_mode == "calm" and rng.random() > 0.7:
        bg["transition_to"] = "flow_field_turbulent"
    elif bg_mode == "turbulent" and rng.random() > 0.7:
        bg["transition_to"] = "flow_field_calm"

    return bg


def build_scene(
    idx: int,
    sentence: str,
    start_sec: float,
    end_sec: float,
    emotion: str,
    palette: dict,
    rng: random.Random,
    used_vocabs: set,
    highlight_words: list,
    genre: str = "",
    strategy: dict = None,
    recent_combos: set = None,
    si: float = 0.5,
) -> dict:
    """단일 씬의 비주얼 스크립트 생성 (v5: 장르+전략+variant+SI)"""
    pool = EMOTION_VOCAB_POOL.get(emotion, EMOTION_VOCAB_POOL["neutral_curious"])
    genre_override = GENRE_VISUAL_OVERRIDES.get(genre, {})
    if strategy is None:
        strategy = get_strategy("dense")

    # 전략 기반 vocab 필터링
    avoid = set(strategy.get("avoid_vocabs", []))
    prefer = strategy.get("prefer_vocabs", [])

    # 주요 비주얼 1개 선택 (이전 씬과 다른 것 선호 + 전략 반영)
    primary_candidates = [v for v in pool["primary"] if v not in used_vocabs and v not in avoid]
    if not primary_candidates:
        primary_candidates = [v for v in pool["primary"] if v not in avoid]
    if not primary_candidates:
        primary_candidates = pool["primary"]
    # prefer 가중치: prefer에 있는 후보를 앞에 배치
    preferred = [v for v in primary_candidates if v in prefer]
    if preferred and rng.random() > 0.3:
        primary_vocab = rng.choice(preferred)
    else:
        primary_vocab = rng.choice(primary_candidates)

    # 보조 비주얼 선택 (minimal 전략이면 생략, SI 기반 레이어 수 조절)
    max_layers = strategy.get("max_semantic_layers", 3)
    # SI 낮으면 레이어 수 줄이기: si=0.25→max 1, si=0.5→max 2, si=0.75+→max 3
    si_max_layers = max(1, min(3, int(si * 3.5)))
    max_layers = min(max_layers, si_max_layers)
    secondary_candidates = [v for v in pool["secondary"] if v != primary_vocab and v not in used_vocabs and v not in avoid]
    if not secondary_candidates:
        secondary_candidates = [v for v in pool["secondary"] if v not in avoid]
    if not secondary_candidates:
        secondary_candidates = pool["secondary"]
    secondary_vocab = rng.choice(secondary_candidates) if max_layers >= 2 else None

    # 장르 오버라이드: 8bit 비주얼 주입
    inject_vocabs = genre_override.get("inject_vocabs", [])
    inject_chance = genre_override.get("inject_chance", 0)
    if inject_vocabs and rng.random() < inject_chance:
        # 주요 비주얼을 8bit로 교체
        primary_vocab = rng.choice(inject_vocabs)
    if inject_vocabs and rng.random() < inject_chance * 0.5:
        # 보조 비주얼도 8bit로 교체 (절반 확률)
        secondary_vocab = rng.choice(inject_vocabs)

    # 사용 기록 (최근 2개만 추적)
    used_vocabs.clear()
    used_vocabs.add(primary_vocab)
    if secondary_vocab:
        used_vocabs.add(secondary_vocab)

    # 파라미터 생성 (variant 포함)
    semantic: List[Dict] = []
    primary_params = generate_vocab_params(primary_vocab, palette, rng)
    primary_entry: Dict[str, Any] = {"vocab": primary_vocab, "params": primary_params}
    primary_variant = select_variant(primary_vocab, rng, recent_combos)
    if primary_variant and primary_variant != "default":
        primary_entry["variant"] = primary_variant
    semantic.append(primary_entry)

    if secondary_vocab:
        secondary_params = generate_vocab_params(secondary_vocab, palette, rng)
        secondary_entry: Dict[str, Any] = {"vocab": secondary_vocab, "params": secondary_params}
        secondary_variant = select_variant(secondary_vocab, rng, recent_combos)
        if secondary_variant and secondary_variant != "default":
            secondary_entry["variant"] = secondary_variant
        semantic.append(secondary_entry)

    # 텍스트 비주얼 추가 (전략의 text_chance 반영)
    text_chance = strategy.get("text_chance", 0.5)
    force_text_mode = strategy.get("force_text_mode")
    keyword = extract_highlight_word(sentence)
    if keyword and rng.random() < text_chance:
        text_mode = force_text_mode or pool.get("text_mode", "wave")
        text_params = generate_vocab_params("text_reveal", palette, rng)
        text_params["text"] = keyword
        text_params["mode"] = text_mode
        semantic.append({"vocab": "text_reveal", "params": text_params})
        if keyword not in highlight_words:
            highlight_words.append(keyword)

    # 오디오 리액티비티 (전략의 reactivity_boost 적용 + SI 기반 오버라이드)
    reactivity_level = pool.get("reactivity", "medium")
    reactivity_boost = strategy.get("reactivity_boost", 0)
    if reactivity_boost != 0:
        reactivity_level = boost_reactivity(reactivity_level, reactivity_boost)
    # SI 기반 reactivity 보정: si 높으면 반응성 상향, si 낮으면 하향
    if si >= 0.88:
        reactivity_level = "max"
    elif si >= 0.72:
        reactivity_level = boost_reactivity(reactivity_level, 1)
    elif si <= 0.25:
        reactivity_level = "low"
    audio_reactive = dict(REACTIVITY_PRESETS[reactivity_level])

    # 배경: 8bit 장르면 pixel_grid 배경 사용 가능
    if genre_override.get("force_bg_pixel") and rng.random() > 0.3:
        background = {
            "vocab": "pixel_grid",
            "params": generate_vocab_params("pixel_grid", palette, rng),
        }
        # 배경용 낮은 반응성 + 큰 셀
        background["params"]["reactivity"] = 0.4
        background["params"]["cols"] = rng.choice([16, 20])
        background["params"]["rows"] = rng.choice([16, 20])
    else:
        background = generate_background(emotion, palette, rng, idx)

    return {
        "id": f"scene_{idx + 1:02d}",
        "sentence": sentence,
        "start_sec": round(start_sec, 3),
        "end_sec": round(end_sec, 3),
        "emotion": emotion,
        "layers": {
            "semantic": semantic,
            "audio_reactive": audio_reactive,
            "background": background,
        },
    }


def generate_visual_script(
    narration_timing_path: str,
    script_path: Optional[str] = None,
    palette_name: str = "phantom",
    title: str = "",
    seed: Optional[int] = None,
    genre: str = "",
    strategy_name: str = "",
    episode_id: str = "",
) -> dict:
    """전체 비주얼 스크립트 생성 (v5: 장르+전략+이력 기반 비주얼 선택)"""

    # 나레이션 타이밍 로드
    with open(narration_timing_path, 'r', encoding='utf-8') as f:
        timing_data = json.load(f)

    segments = timing_data["segments"]

    # 문장 합치기 (짧은 문장은 합침) + SI 평균 계산
    merged_scenes: List[Dict] = []
    buffer_text = ""
    buffer_start = 0.0
    buffer_end = 0.0
    buffer_si_sum = 0.0
    buffer_count = 0
    MIN_SCENE_DURATION = 3.0  # 최소 씬 길이 (초)

    def _seg_si(seg):
        """세그먼트에서 semantic_intensity 추출 (다양한 포맷 지원)"""
        analysis = seg.get("analysis", {})
        return analysis.get("semantic_intensity", seg.get("semantic_intensity", 0.5))

    for seg in segments:
        if not buffer_text:
            buffer_text = seg["text"]
            buffer_start = seg["start_sec"]
            buffer_end = seg["end_sec"]
            buffer_si_sum = _seg_si(seg)
            buffer_count = 1
        else:
            # 현재 버퍼 길이가 최소 씬 길이 미만이면 합침
            if buffer_end - buffer_start < MIN_SCENE_DURATION:
                buffer_text += " " + seg["text"]
                buffer_end = seg["end_sec"]
                buffer_si_sum += _seg_si(seg)
                buffer_count += 1
            else:
                merged_scenes.append({
                    "text": buffer_text,
                    "start": buffer_start,
                    "end": buffer_end,
                    "si": buffer_si_sum / buffer_count,
                })
                buffer_text = seg["text"]
                buffer_start = seg["start_sec"]
                buffer_end = seg["end_sec"]
                buffer_si_sum = _seg_si(seg)
                buffer_count = 1

    # 마지막 버퍼
    if buffer_text:
        merged_scenes.append({
            "text": buffer_text,
            "start": buffer_start,
            "end": buffer_end,
            "si": buffer_si_sum / buffer_count if buffer_count else 0.5,
        })

    print(f"  Segments: {len(segments)} → Scenes: {len(merged_scenes)}")

    # 전략 해석 (명시적 지정 > 장르 기반 > 기본 dense)
    if not strategy_name and genre:
        strategy_name = get_default_strategy(genre)
    if not strategy_name:
        strategy_name = "dense"
    strategy = get_strategy(strategy_name)
    try:
        print(f"  Strategy: {strategy_name} - {strategy.get('description', '')}")
    except UnicodeEncodeError:
        print(f"  Strategy: {strategy_name}")

    # 이력 로드 (최근 2개 에피소드 vocab:variant 조합 회피)
    vocab_history = load_vocab_history()
    recent_combos = get_recent_used(vocab_history, lookback=2)
    if recent_combos:
        print(f"  History: {len(recent_combos)} combos from recent episodes avoided")

    # 장르 기반 팔레트 오버라이드
    genre_override = GENRE_VISUAL_OVERRIDES.get(genre, {})
    if genre_override.get("palette") and palette_name == "phantom":
        palette_name = genre_override["palette"]

    # 팔레트
    palette = PALETTES.get(palette_name, PALETTES["phantom"])

    # 시드 기반 랜덤
    if seed is None:
        seed = hash(title) & 0xFFFFFFFF
    rng = random.Random(seed)

    # 씬별 비주얼 생성
    scenes = []
    used_vocabs: set = set()
    prev_emotion = ""
    highlight_words: List[str] = []

    for i, scene_data in enumerate(merged_scenes):
        emotion = detect_emotion(scene_data["text"], prev_emotion)

        # 에피소드 전체 감정 아크 보정
        progress = i / max(len(merged_scenes) - 1, 1)
        if progress < 0.15 and emotion not in ("neutral_curious",):
            # 도입부는 neutral 계열 선호
            if rng.random() > 0.5:
                emotion = "neutral_curious"
        elif progress > 0.85 and emotion not in ("transcendent_open", "hopeful", "awakening_climax"):
            # 마무리는 고양 계열 선호
            if rng.random() > 0.5:
                emotion = rng.choice(["transcendent_open", "hopeful"])

        scene = build_scene(
            i, scene_data["text"],
            scene_data["start"], scene_data["end"],
            emotion, palette, rng,
            used_vocabs, highlight_words,
            genre=genre,
            strategy=strategy,
            recent_combos=recent_combos,
            si=scene_data.get("si", 0.5),
        )
        scenes.append(scene)
        prev_emotion = emotion

    # 하이라이트 단어 결정 (상위 2개)
    if not highlight_words:
        # 폴백: 제목에서 추출
        title_words = re.findall(r'[가-힣]{2,4}', title)
        highlight_words = title_words[:2] if title_words else []
    highlight_words = highlight_words[:3]  # 최대 3개

    # 이력 기록 (episode_id가 있으면)
    if episode_id:
        record_episode_history(vocab_history, episode_id, scenes)
        save_vocab_history(vocab_history)
        print(f"  History saved for {episode_id}")

    # v8: frames_dir + total_frames 자동 계산 (hybrid 전용)
    last_end = merged_scenes[-1]["end"] if merged_scenes else 0
    auto_total_frames = int((last_end + 6.0) * 30)  # 30fps, endcard 6초 포함

    return {
        "title": title,
        "highlightWords": highlight_words,
        "meta": {
            "strategy": strategy_name,
            "strategy_description": strategy.get("description", ""),
            "genre": "ikeda",
            "palette": palette_name,
            "seed": seed,
            "render_mode": "hybrid",
            **({"frames_dir": f"{episode_id}/frames"} if episode_id else {}),
            "total_frames": auto_total_frames,
        },
        "global": {
            "color_palette": palette["colors"],
            "background_color": palette["bg"],
            "particle_total": 2000,
            "font": "Pretendard Variable",
            "palette": palette_name,
        },
        "scenes": scenes,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python visual_script_generator.py <narration_timing.json> [output.json] [options]")
        print()
        print("Options:")
        print("  --palette <name>     팔레트 (phantom/neon_noir/cold_steel/ember/synapse/gameboy/c64)")
        print("  --genre <name>       (v8: 무시됨, 항상 ikeda)")
        print("  --strategy <name>    비주얼 전략 (dense/breathing/collision/layered/minimal/glitch)")
        print("  --episode <id>       에피소드 ID (이력 추적용, 예: ep005)")
        print("  --title <title>      에피소드 제목")
        print("  --seed <number>      랜덤 시드 (같은 시드 = 같은 결과)")
        print()
        print("Example:")
        print("  python visual_script_generator.py episodes/ep003/narration_timing.json episodes/ep003/visual_script.json --palette phantom --genre techno --strategy collision --title '우리의 기억은 매번 다시 만들어진다'")
        sys.exit(1)

    narration_timing = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None

    # 옵션 파싱
    palette_name = "phantom"
    title = ""
    seed = None
    genre = ""
    strategy_name = ""
    episode_id = ""

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--palette" and i + 1 < len(sys.argv):
            palette_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--genre" and i + 1 < len(sys.argv):
            genre = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--strategy" and i + 1 < len(sys.argv):
            strategy_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--episode" and i + 1 < len(sys.argv):
            episode_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--title" and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--seed" and i + 1 < len(sys.argv):
            seed = int(sys.argv[i + 1])
            i += 2
        else:
            if output is None and not sys.argv[i].startswith("--"):
                output = sys.argv[i]
            i += 1

    if output is None:
        # narration_timing.json과 같은 디렉토리에 visual_script.json
        output = os.path.join(os.path.dirname(narration_timing), "visual_script.json")

    # v8: 장르 항상 ikeda (단일 장르 시스템)
    if genre and genre != "ikeda":
        print(f"⚠ WARNING: --genre {genre} 무시됨. v8부터 ikeda 단일 장르 시스템입니다.")
    genre = "ikeda"

    print(f"=== ENOMETA Visual Script Generator v8 ===")
    print(f"Narration timing: {narration_timing}")
    print(f"Palette: {palette_name}")
    print(f"Genre: ikeda (v8 단일 장르)")
    if strategy_name:
        print(f"Strategy: {strategy_name}")
    if not title:
        print(f"⚠ WARNING: --title 미지정! 에피소드 제목을 --title 옵션으로 반드시 전달하세요.")
        print(f"  예: --title '공포와 각성의 화학식은 같다'")
        title = "제목 미지정"
    print(f"Title: {title}")

    # episode_id 자동 추출 (경로에서)
    if not episode_id:
        # episodes/ep005/narration_timing.json → ep005
        parts = narration_timing.replace("\\", "/").split("/")
        for p in parts:
            if p.startswith("ep") and p[2:].isdigit():
                episode_id = p
                break

    result = generate_visual_script(
        narration_timing,
        palette_name=palette_name,
        title=title,
        seed=seed,
        genre=genre,
        strategy_name=strategy_name,
        episode_id=episode_id,
    )

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  Scenes: {len(result['scenes'])}")
    print(f"  Highlight words: {result['highlightWords']}")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()
