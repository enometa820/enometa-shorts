"""
ENOMETA 비주얼 전략 프리셋

에피소드 전체의 비주얼 밀도/리듬/구성을 결정하는 상위 전략.
visual_script_generator.py에서 --strategy 옵션으로 사용.
"""

from typing import Dict, Any

# ============================================================
# 전략 6종 정의
# ============================================================
STRATEGIES: Dict[str, Dict[str, Any]] = {
    "dense": {
        "description": "빽빽한 입자+레이어 — 압도적 시각 밀도",
        "max_semantic_layers": 4,
        "particle_density": 1.5,      # 파티클 count 배율
        "text_chance": 0.7,           # 텍스트 비주얼 삽입 확률
        "bg_opacity_mult": 1.2,       # 배경 opacity 배율
        "prefer_vocabs": ["particle_birth", "particle_scatter", "neural_network", "grid_morph"],
        "avoid_vocabs": [],
        "reactivity_boost": 0,        # reactivity level 상향 (0=없음, 1=한단계 상향)
    },
    "breathing": {
        "description": "여백 + 느린 호흡 — 명상적, 미니멀",
        "max_semantic_layers": 2,
        "particle_density": 0.5,
        "text_chance": 0.3,
        "bg_opacity_mult": 0.6,
        "prefer_vocabs": ["particle_orbit", "flow_field_calm", "light_source", "color_shift"],
        "avoid_vocabs": ["fractal_crack", "particle_scatter", "grid_morph"],
        "reactivity_boost": -1,
    },
    "collision": {
        "description": "충돌/분열 중심 — 대비+충격",
        "max_semantic_layers": 3,
        "particle_density": 1.2,
        "text_chance": 0.5,
        "bg_opacity_mult": 1.0,
        "prefer_vocabs": ["particle_scatter", "fractal_crack", "particle_split_ratio", "particle_escape"],
        "avoid_vocabs": ["particle_orbit", "light_source"],
        "reactivity_boost": 1,
    },
    "layered": {
        "description": "배경-중경-전경 분리 — 깊이감",
        "max_semantic_layers": 3,
        "particle_density": 1.0,
        "text_chance": 0.5,
        "bg_opacity_mult": 0.8,
        "prefer_vocabs": ["flow_field_calm", "grid_morph", "particle_orbit", "waveform"],
        "avoid_vocabs": [],
        "reactivity_boost": 0,
    },
    "minimal": {
        "description": "단일 포커스 — 집중력",
        "max_semantic_layers": 1,
        "particle_density": 0.4,
        "text_chance": 0.6,
        "bg_opacity_mult": 0.4,
        "prefer_vocabs": ["light_source", "counter_up", "data_bar", "text_reveal"],
        "avoid_vocabs": ["particle_birth", "particle_scatter", "neural_network"],
        "reactivity_boost": -1,
    },
    "glitch": {
        "description": "글리치+노이즈 — 불안정+긴장감",
        "max_semantic_layers": 3,
        "particle_density": 1.0,
        "text_chance": 0.8,
        "bg_opacity_mult": 1.0,
        "prefer_vocabs": ["fractal_crack", "grid_morph", "neural_network", "waveform_spectrum"],
        "avoid_vocabs": ["light_source", "color_bloom"],
        "reactivity_boost": 1,
        "force_text_mode": "glitch",
    },
    "enometa": {
        "description": "ENOMETA data art - minimal+terminal+sine",
        "max_semantic_layers": 2,
        "particle_density": 0.0,
        "text_chance": 0.9,
        "bg_opacity_mult": 1.0,
        "prefer_vocabs": ["text_reveal"],
        "avoid_vocabs": ["particle_birth", "particle_scatter", "color_bloom",
                         "neural_network", "light_source", "fractal_crack",
                         "data_bar", "counter_up"],
        "reactivity_boost": 0,
    },
}

# ============================================================
# 장르 → 기본 전략 매핑
# ============================================================
GENRE_DEFAULT_STRATEGY: Dict[str, str] = {
    "techno": "dense",
    "algorave": "collision",
    "harsh_noise": "glitch",
    "bytebeat": "minimal",
    "chiptune": "layered",
    "enometa": "enometa",
    "ikeda": "enometa",  # 하위호환
}

# ============================================================
# 리액티비티 레벨 순서 (boost 적용용)
# ============================================================
REACTIVITY_LEVELS = ["low", "medium", "high", "max"]


def get_strategy(name: str) -> Dict[str, Any]:
    """전략 프리셋 반환 (없으면 dense 기본)"""
    return STRATEGIES.get(name, STRATEGIES["dense"])


def get_default_strategy(genre: str) -> str:
    """장르에 맞는 기본 전략 이름 반환"""
    return GENRE_DEFAULT_STRATEGY.get(genre, "dense")


def boost_reactivity(level: str, boost: int) -> str:
    """리액티비티 레벨을 boost만큼 상향/하향"""
    if boost == 0:
        return level
    try:
        idx = REACTIVITY_LEVELS.index(level)
    except ValueError:
        idx = 1  # medium default
    new_idx = max(0, min(len(REACTIVITY_LEVELS) - 1, idx + boost))
    return REACTIVITY_LEVELS[new_idx]
