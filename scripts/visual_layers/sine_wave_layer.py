"""
visual_layers/sine_wave_layer.py
순수 오실로스코프 사인파 — 1px 안티앨리어싱 라인 + 피크 글로우.
단어의 byte_sum이 사인파 주파수 결정 → 단어마다 다른 파형.
"""

import numpy as np


class SineWaveLayer:
    def __init__(self, width, height, palette, intensity=0.7, blend="additive"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        audio_chunk = ctx.get("audio_chunk", np.array([]))
        accent = np.array(
            ctx.get("accent_color") or self.palette.get("accent", (255, 255, 255)),
            dtype=np.float64,
        )
        frame_rms = ctx.get("frame_rms", 0)
        script_data = ctx.get("script_data")
        time_sec = ctx.get("time", 0)

        # sine_interference_values 사용 가능하면 우선
        sine_vals = ctx.get("sine_interference_values")
        if sine_vals is not None and len(sine_vals) > 0:
            source = sine_vals.astype(float)
        elif len(audio_chunk) > 0 and np.any(audio_chunk):
            source = audio_chunk.astype(float)
        else:
            return canvas

        # Resample to width
        resampled = np.interp(
            np.linspace(0, len(source) - 1, self.width),
            np.arange(len(source)),
            source,
        )

        # Normalize
        amax = np.max(np.abs(resampled))
        if amax > 0:
            normalized = resampled / amax
        else:
            return canvas

        center_y = self.height // 2
        amplitude = self.height * 0.3 * self.intensity

        # Find current word's byte_variance for noise modulation
        byte_variance = 0
        if script_data:
            for seg in script_data.get("segments", []):
                if seg["start_sec"] <= time_sec < seg["end_sec"]:
                    keywords = seg.get("analysis", {}).get("keywords", [])
                    if keywords:
                        variances = [
                            kw.get("word_data", {}).get("byte_variance", 0)
                            for kw in keywords
                        ]
                        byte_variance = max(variances) if variances else 0
                    break

        # Add noise if high byte_variance word
        if byte_variance > 2000:
            noise_amp = min(byte_variance / 10000, 0.3)
            noise = np.random.uniform(-noise_amp, noise_amp, self.width)
            normalized += noise

        # Draw 1px anti-aliased line
        brightness = min(1.0, 0.5 + frame_rms * 2.0)
        line_color = (accent * brightness).astype(np.uint8)
        glow_color = (accent * brightness * 0.3).astype(np.uint8)

        for x in range(self.width - 1):
            y1 = int(normalized[x] * amplitude) + center_y
            y2 = int(normalized[x + 1] * amplitude) + center_y
            y1 = max(0, min(self.height - 1, y1))
            y2 = max(0, min(self.height - 1, y2))

            y_min = min(y1, y2)
            y_max = max(y1, y2)

            # Main line (1px)
            canvas[y_min:y_max + 1, x] = line_color

            # Gaussian glow (3-5px spread at peaks)
            for dy in [-2, -1, 1, 2]:
                gy = y1 + dy
                if 0 <= gy < self.height:
                    canvas[gy, x] = np.maximum(canvas[gy, x], glow_color)

        return canvas
