"""
visual_layers/barcode_layer.py
수직 바코드 스트라이프 — 각 토큰의 UTF-8 바이트가 고유 패턴 생성.
"공포" (eab3b5ed8fac) ≠ "각성" (eab081ec84b1) → 완전히 다른 바코드.

v2: semantic_intensity 기반 다이나믹 비주얼
    - 선 굵기: 2→12px (kw_intensity + BPM 맥동)
    - 선 높이: 60~100% (intensity 비례)
    - 색상: 키워드별 밝기, 채도 변조
    - 이펙트: scanlines/chromatic/glitch/data click
    - 스크롤 속도: si 비례 가속
"""

import numpy as np
from . import tts_effects


class BarcodeLayer:
    def __init__(self, width, height, palette, intensity=0.5, blend="additive"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend
        self._scroll_offset = 0.0

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        script_data = ctx.get("script_data")
        time_sec = ctx.get("time", 0)
        frame_rms = ctx.get("frame_rms", 0)
        frame_idx = ctx.get("frame_index", 0)
        accent = np.array(
            ctx.get("accent_color") or self.palette.get("accent", (255, 255, 255)),
            dtype=np.float32
        )
        data_click = ctx.get("data_click_frame", False)
        si = ctx.get("semantic_intensity", 0.2)
        reactive = ctx.get("reactive_level", 0.2)
        bpm = ctx.get("bpm", 128)

        # Find current segment
        current_seg = None
        if script_data:
            for seg in script_data.get("segments", []):
                if seg["start_sec"] <= time_sec < seg["end_sec"]:
                    current_seg = seg
                    break

        if not current_seg:
            return canvas

        keywords = current_seg.get("analysis", {}).get("keywords", [])
        if not keywords:
            return canvas

        # ===== Build barcode pattern =====
        barcode_bits = []
        for kw in keywords:
            word_data = kw.get("word_data", {})
            raw_bytes = word_data.get("raw_bytes", [])
            kw_type = kw.get("type", "noun")
            kw_intensity = kw.get("intensity", 0.3)

            # 기본 선 굵기: 2→12px (kw_intensity 비례)
            base_stripe_w = int(2 + 10 * kw_intensity)

            for b in raw_bytes:
                for bit_idx in range(7, -1, -1):
                    bit = (b >> bit_idx) & 1

                    if kw_type == "noun":
                        stripe_w = base_stripe_w if bit else max(1, base_stripe_w // 3)
                    elif kw_type == "verb":
                        stripe_w = int(base_stripe_w * 0.7)
                    elif kw_type == "number":
                        stripe_w = max(1, base_stripe_w // 2)
                    elif kw_type in ("chemical", "body"):
                        stripe_w = int(base_stripe_w * 0.8) if bit else int(base_stripe_w * 0.6)
                    else:
                        stripe_w = max(1, base_stripe_w // 2)

                    # BPM 맥동
                    stripe_w = tts_effects.scale_pulse(
                        stripe_w, kw_intensity, frame_idx, bpm, 0.2
                    )

                    barcode_bits.append((bit, stripe_w, kw_type, kw_intensity))

        if not barcode_bits:
            return canvas

        # ===== Scroll =====
        total_byte_sum = sum(
            kw.get("word_data", {}).get("byte_sum", 0) for kw in keywords
        )
        base_scroll = (total_byte_sum % 5) + 1
        scroll_speed = base_scroll * (0.5 + si * 2.0)
        self._scroll_offset += scroll_speed

        # ===== Render barcode stripes =====
        x = int(-self._scroll_offset) % max(self.width, 1)

        # 전체 밝기: si 베이스 + rms 변조
        base_brightness = min(1.0, 0.3 + frame_rms * 3.0) * self.intensity

        for bit, stripe_w, kw_type, kw_int in barcode_bits:
            if bit == 1:
                # 키워드별 밝기
                kw_brightness = base_brightness * (0.4 + kw_int * 0.6)
                color = (accent * kw_brightness).astype(np.uint8)

                # 선 높이: kw_int에 따라 60~100%
                if kw_int > 0.7:
                    y_start, y_end = 0, self.height
                elif kw_int > 0.4:
                    margin = int(self.height * 0.1)
                    y_start, y_end = margin, self.height - margin
                else:
                    margin = int(self.height * 0.2)
                    y_start, y_end = margin, self.height - margin

                x_pos = x % self.width
                x_end = min(x_pos + stripe_w, self.width)

                if kw_type == "verb":
                    # Verb: dashed pattern (대시 길이: 3→7px)
                    dash_len = int(3 + kw_int * 4)
                    for y in range(y_start, y_end, dash_len * 2):
                        dy_end = min(y + dash_len, y_end)
                        if x_pos < self.width:
                            canvas[y:dy_end, x_pos:x_end] = color
                else:
                    if x_pos < self.width:
                        canvas[y_start:y_end, x_pos:x_end] = color

            x += stripe_w + 1

        # ===== Post-Processing =====

        # 스캔라인 (항상, 가볍게)
        canvas = tts_effects.scanlines(canvas, reactive * 0.5, line_spacing=4, darkness=0.25)

        # Chromatic aberration (si > 0.5)
        if si > 0.5:
            canvas = tts_effects.chromatic_aberration(canvas, si * 0.7, max_offset=6)

        # 글리치 블록 (si > 0.7)
        if si > 0.7:
            canvas = tts_effects.glitch_blocks(canvas, si, frame_idx, max_blocks=3)

        # Data click 폭발
        if data_click:
            canvas = tts_effects.data_click_explosion(
                canvas,
                tuple(accent.astype(int)),
                si, frame_idx
            )

        return canvas
