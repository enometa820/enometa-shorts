"""
visual_layers/composite.py
여러 레이어를 하나의 프레임으로 합성.
"""

import numpy as np


def composite_layers(
    background: np.ndarray,
    layers: list,
) -> np.ndarray:
    """레이어를 background 위에 순차 합성 (additive blend)"""
    result = background.astype(np.float32)

    for layer in layers:
        if layer is None:
            continue
        result = result + layer.astype(np.float32)

    return np.clip(result, 0, 255).astype(np.uint8)


def composite_dual_source(
    background: np.ndarray,
    music_layer: np.ndarray,
    tts_layer: np.ndarray,
    blend_ratio: float = 0.5,
    arc_energy: float = 1.0,
) -> np.ndarray:
    """Dual-source 레이어 합성

    TTS 비주얼과 음악 비주얼을 독립 가중치로 합성.
    arc_energy가 음악 레이어 강도를 변조하여 기승전결 구조 반영.

    Args:
        background: 배경 캔버스 (h, w, 3) uint8
        music_layer: 음악 기반 레이어 합성 결과 (h, w, 3) uint8
        tts_layer: TTS/대본 기반 레이어 합성 결과 (h, w, 3) uint8
        blend_ratio: 0.0=TTS 전용, 1.0=Music 전용, 0.5=균등
        arc_energy: Song Arc 에너지 (0~1.5) — 음악 레이어 강도에 영향

    Returns:
        np.ndarray: 최종 합성 결과 (h, w, 3) uint8
    """
    bg = background.astype(np.float32)
    music = music_layer.astype(np.float32)
    tts = tts_layer.astype(np.float32)

    # Arc energy modulates music layer intensity
    music_weight = blend_ratio * max(arc_energy, 0.1)
    tts_weight = (1.0 - blend_ratio)

    # Normalize to prevent oversaturation while keeping arc influence
    total_weight = music_weight + tts_weight
    if total_weight > 1.5:
        music_weight = music_weight / total_weight * 1.5
        tts_weight = tts_weight / total_weight * 1.5

    result = bg + music * music_weight + tts * tts_weight

    return np.clip(result, 0, 255).astype(np.uint8)
