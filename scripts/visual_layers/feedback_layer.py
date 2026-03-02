"""
visual_layers/feedback_layer.py
피드백 루프 시각화.
이전 프레임이 다음 프레임에 영향 — 자기참조 구조.
harsh_noise 장르의 핵심 비주얼.
"""

import numpy as np


class FeedbackLayer:
    def __init__(self, width, height, palette, intensity=0.9, blend="normal"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend
        self.feedback_buffer = np.zeros((height, width, 3), dtype=np.float32)

    def render(self, ctx: dict) -> np.ndarray:
        audio_chunk = ctx["audio_chunk"]
        rms = np.sqrt(np.mean(audio_chunk ** 2)) if len(audio_chunk) > 0 and np.any(audio_chunk) else 0

        accent = np.array(self.palette["accent"], dtype=np.float32)

        # 새 입력: 오디오 기반 노이즈
        noise = np.random.rand(self.height, self.width).astype(np.float32)
        noise *= rms * self.intensity

        new_input = np.zeros((self.height, self.width, 3), dtype=np.float32)
        for c in range(3):
            new_input[:, :, c] = noise * accent[c] / 255.0

        # 피드백: 이전 프레임을 변형해서 혼합
        shifted = np.roll(self.feedback_buffer, 1, axis=0)
        shifted = np.roll(shifted, int(rms * 5), axis=1)

        feedback_amount = 0.85 + rms * 0.1

        self.feedback_buffer = shifted * feedback_amount + new_input * (1 - feedback_amount)
        self.feedback_buffer = np.clip(self.feedback_buffer, 0, 1)

        return (self.feedback_buffer * 255).astype(np.uint8)
