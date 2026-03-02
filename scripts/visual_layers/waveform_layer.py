"""
visual_layers/waveform_layer.py
오디오 파형을 직접 화면에 그리는 레이어.
FFT 요약이 아닌 실제 샘플값을 사용.
"""

import numpy as np


class WaveformLayer:
    def __init__(self, width, height, palette, intensity=0.5, blend="additive"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        audio_chunk = ctx["audio_chunk"]

        if len(audio_chunk) == 0 or not np.any(audio_chunk):
            return canvas

        # 오디오 → 화면 좌표
        resampled = np.interp(
            np.linspace(0, len(audio_chunk) - 1, self.width),
            np.arange(len(audio_chunk)),
            audio_chunk.astype(float),
        )

        amax, amin = resampled.max(), resampled.min()
        if amax != amin:
            normalized = (resampled - amin) / (amax - amin)
        else:
            normalized = np.full(self.width, 0.5)

        center_y = self.height // 2
        accent = np.array(self.palette["accent"], dtype=np.uint8)

        # 파형 라인 (두께 2px)
        for x in range(self.width - 1):
            y1 = int((normalized[x] - 0.5) * self.height * 0.8 * self.intensity) + center_y
            y2 = int((normalized[x + 1] - 0.5) * self.height * 0.8 * self.intensity) + center_y

            y_min = max(0, min(y1, y2) - 1)
            y_max = min(self.height - 1, max(y1, y2) + 1)
            canvas[y_min:y_max + 1, x] = accent

        # RMS 기반 글로우
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        glow_r = int(rms * 50 * self.intensity)
        if glow_r > 0:
            mid_color = np.array(self.palette["mid"], dtype=float)
            for dy in range(-glow_r, glow_r + 1):
                y = center_y + dy
                if 0 <= y < self.height:
                    alpha = 1.0 - abs(dy) / glow_r
                    glow = (mid_color * alpha * 0.3).astype(np.uint8)
                    canvas[y] = np.maximum(canvas[y], glow)

        return canvas
