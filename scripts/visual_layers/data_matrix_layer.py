"""
visual_layers/data_matrix_layer.py
악기별 에너지, 합성 파라미터를 매트릭스/그리드로 직접 시각화.
데이터 자체가 미학이 되는 Ryoji Ikeda 스타일.
"""

import numpy as np


class DataMatrixLayer:
    def __init__(self, width, height, palette, intensity=0.6, blend="additive"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        audio_chunk = ctx["audio_chunk"]
        rms = ctx.get("frame_rms", 0)
        energy = ctx.get("section_energy", 0.5)

        accent = np.array(self.palette["accent"], dtype=float)
        mid = np.array(self.palette["mid"], dtype=float)

        # --- 상단: 에너지 바 ---
        bar_h = 30
        bar_w = int(energy * self.width * self.intensity)
        if bar_w > 0 and bar_h <= self.height:
            color = (mid + (accent - mid) * energy).astype(np.uint8)
            canvas[:bar_h, :bar_w] = color

        # --- 중앙: 비트 매트릭스 (오디오 비트 패턴) ---
        matrix_y = bar_h + 10
        matrix_h = self.height - matrix_y
        if len(audio_chunk) > 0 and matrix_h > 0 and np.any(audio_chunk):
            samples_int = ((audio_chunk + 1) * 127).clip(0, 255).astype(np.uint8)

            cols = min(self.width // 4, len(samples_int))
            rows = min(8, matrix_h // 4)
            if cols > 0 and rows > 0:
                cell_w = self.width // cols
                cell_h = matrix_h // rows

                for bit_row in range(rows):
                    for col in range(min(cols, len(samples_int))):
                        bit = (samples_int[col] >> bit_row) & 1
                        if bit:
                            x = col * cell_w
                            y = matrix_y + bit_row * cell_h
                            if x + cell_w <= self.width and y + cell_h <= self.height:
                                alpha = self.intensity * (0.5 + 0.5 * (bit_row / rows))
                                color = (accent * alpha).astype(np.uint8)
                                canvas[y:y + cell_h - 1, x:x + cell_w - 1] = color

        return canvas
