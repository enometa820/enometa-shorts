"""
visual_layers/bytebeat_layer.py
bytebeat 공식의 원본 값이 직접 픽셀이 되는 레이어.
데이터가 곧 소리이고 곧 화면이다.
"""

import numpy as np


class BytebeatLayer:
    def __init__(self, width, height, palette, intensity=0.8):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.prev_frame = None

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bb_values = ctx["bytebeat_values"]
        audio_chunk = ctx["audio_chunk"]

        accent = np.array(self.palette["accent"], dtype=float)
        mid = np.array(self.palette["mid"], dtype=float)

        # --- 스캔라인: bytebeat 값이 행별 밝기 ---
        if len(bb_values) > 0 and np.any(bb_values):
            resampled = np.interp(
                np.linspace(0, len(bb_values) - 1, self.height),
                np.arange(len(bb_values)),
                bb_values.astype(float),
            )
            vmax, vmin = resampled.max(), resampled.min()
            if vmax > vmin:
                normalized = (resampled - vmin) / (vmax - vmin)
            else:
                normalized = np.zeros(self.height)

            for y in range(self.height):
                val = normalized[y] * self.intensity
                color = (mid * (1 - val) + accent * val).astype(np.uint8)
                # x축: bytebeat 비트 패턴 매핑
                raw_int = int(bb_values[y % len(bb_values)]) & 0xFFFF
                for x in range(self.width):
                    bit = (raw_int >> (x % 16)) & 1
                    if bit:
                        canvas[y, x] = color
                    else:
                        canvas[y, x] = (color * 0.15).astype(np.uint8)

        # --- 하단 1/3: 오디오 청크 직접 매핑 ---
        chunk_h = self.height // 3
        y_off = self.height - chunk_h

        if len(audio_chunk) > 0 and np.any(audio_chunk):
            resampled_a = np.interp(
                np.linspace(0, len(audio_chunk) - 1, self.width),
                np.arange(len(audio_chunk)),
                audio_chunk.astype(float),
            )
            amax, amin = resampled_a.max(), resampled_a.min()
            if amax > amin:
                norm_a = (resampled_a - amin) / (amax - amin)
            else:
                norm_a = np.zeros(self.width)

            accent_u8 = np.array(self.palette["accent"], dtype=np.uint8)
            for x in range(self.width):
                bar_h = int(norm_a[x] * chunk_h * self.intensity)
                if bar_h > 0:
                    y_start = y_off + chunk_h - bar_h
                    canvas[y_start:y_off + chunk_h, x] = accent_u8

        # 잔상
        if self.prev_frame is not None:
            canvas = (canvas.astype(float) * 0.7 + self.prev_frame.astype(float) * 0.3).astype(np.uint8)
        self.prev_frame = canvas.copy()

        return canvas
