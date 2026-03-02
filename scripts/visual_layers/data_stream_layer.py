"""
visual_layers/data_stream_layer.py
수평 스크롤 데이터 스트림 — 컴퓨터가 텍스트를 해석하는 과정 시각화.
8-12줄의 데이터 행이 각각 다른 속도로 스크롤.

v2: semantic_intensity 기반 다이나믹 비주얼
    - 폰트: 16→36px, 행높이 가변
    - 색상: 채도/밝기/white bloom
    - 이펙트: glow/scanlines/chromatic/행별 jitter
    - 스크롤 속도: si 비례 가속
"""

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from . import tts_effects


class DataStreamLayer:
    def __init__(self, width, height, palette, intensity=0.5, blend="additive"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend
        self._scroll_offsets = [0.0] * 12
        self._cached_seg_idx = -1
        self._cached_rows = []

    def _build_rows(self, seg):
        """세그먼트에서 데이터 행 생성"""
        rows = []
        text = seg.get("text", "")
        analysis = seg.get("analysis", {})
        tokens = analysis.get("tokens", [])
        keywords = analysis.get("keywords", [])

        # 행 1: 원문 텍스트
        rows.append(("kr", f"  {text}  "))

        # 행 2: 토큰화 결과
        token_str = " ".join(f"[{t['text']}]" for t in tokens)
        rows.append(("kr", f"  TOKENS: {token_str}  "))

        # 행 3: 바이트 인코딩 (첫 3개 키워드)
        hex_parts = []
        for kw in keywords[:3]:
            wd = kw.get("word_data", {})
            hex_parts.append(f"{kw['text']}={wd.get('hex', '??')}")
        rows.append(("mono", f"  HEX: {' | '.join(hex_parts)}  "))

        # 행 4: 이진 변환
        bin_parts = []
        for kw in keywords[:2]:
            wd = kw.get("word_data", {})
            binary = wd.get("binary", "")
            if len(binary) > 40:
                binary = binary[:40] + "..."
            bin_parts.append(binary)
        rows.append(("mono", f"  BIN: {' '.join(bin_parts)}  "))

        # 행 5: 한글 분해
        hangul_parts = []
        for kw in keywords[:3]:
            wd = kw.get("word_data", {})
            hangul = wd.get("hangul", [])
            for h in hangul[:2]:
                hangul_parts.append(
                    f"{h.get('char','')}:c{h.get('cho',0)}.j{h.get('jung',0)}.j{h.get('jong',0)}"
                )
        if hangul_parts:
            rows.append(("mono", f"  HANGUL: {' '.join(hangul_parts)}  "))

        # 행 6-7: 숫자 다중 표현
        numbers = analysis.get("numbers", [])
        for n in numbers[:2]:
            for kw in keywords:
                if kw.get("type") == "number" and kw.get("text") == str(n):
                    nd = kw.get("number_data", {})
                    rows.append(("mono",
                        f"  {n} = {nd.get('hex','?')} = {nd.get('binary','?')} "
                        f"= {nd.get('freq_hz','?')}Hz = {nd.get('period_ms','?')}ms  "
                    ))
                    break

        # 행 8-9: XOR 해시 패턴
        xor_parts = []
        for kw in keywords[:5]:
            wd = kw.get("word_data", {})
            xor_parts.append(f"{kw['text']}={wd.get('xor_hex', '?')}")
        rows.append(("mono", f"  XOR: {' '.join(xor_parts)}  "))

        # 행 10: freq 매핑
        freq_parts = []
        for kw in keywords[:4]:
            wd = kw.get("word_data", {})
            freq = wd.get("freq_hz", 0)
            freq_parts.append(f"{kw['text']}={freq}Hz")
        rows.append(("mono", f"  FREQ: {' '.join(freq_parts)}  "))

        return rows

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        if not HAS_PIL:
            return canvas

        script_data = ctx.get("script_data")
        time_sec = ctx.get("time", 0)
        frame_rms = ctx.get("frame_rms", 0)
        frame_idx = ctx.get("frame_index", 0)
        accent = ctx.get("accent_color") or self.palette.get("accent", (255, 255, 255))
        data_click = ctx.get("data_click_frame", False)
        si = ctx.get("semantic_intensity", 0.2)
        reactive = ctx.get("reactive_level", 0.2)

        # Find current segment
        current_seg = None
        seg_idx = -1
        if script_data:
            for i, seg in enumerate(script_data.get("segments", [])):
                if seg["start_sec"] <= time_sec < seg["end_sec"]:
                    current_seg = seg
                    seg_idx = i
                    break

        if not current_seg:
            return canvas

        # Rebuild rows on segment change
        if seg_idx != self._cached_seg_idx:
            self._cached_seg_idx = seg_idx
            self._cached_rows = self._build_rows(current_seg)
            self._scroll_offsets = [float(i * 50) for i in range(12)]

        rows = self._cached_rows
        if not rows:
            return canvas

        # ===== 다이나믹 폰트 =====
        font_mono, font_size = tts_effects.get_scaled_font(si, 16, 36, monospace=True)
        font_kr, _ = tts_effects.get_scaled_font(si, 16, 36, monospace=False)
        char_width = max(8, int(font_size * 0.6))

        # ===== 다이나믹 색상 =====
        brightness = (si * 0.6 + 0.15) + frame_rms * 0.4
        brightness = min(1.0, brightness) * self.intensity

        # Data click flash
        if data_click:
            brightness = min(1.0, brightness * 3.0)

        text_color = tts_effects.intensity_color(accent, si, brightness)
        dim_color = tts_effects.intensity_color(accent, si * 0.5, brightness * 0.4)

        # PIL rendering
        img = Image.fromarray(canvas)
        draw = ImageDraw.Draw(img)

        # 행 높이: 상위 2행은 si > 0.5이면 1.5배
        base_row_height = self.height // max(len(rows), 1)
        row_heights = []
        for i in range(len(rows)):
            if i < 2 and si > 0.5:
                row_heights.append(int(base_row_height * 1.5))
            else:
                row_heights.append(base_row_height)

        # 행 높이 정규화 (전체 높이에 맞춤)
        total_h = sum(row_heights)
        if total_h > self.height and total_h > 0:
            scale = self.height / total_h
            row_heights = [int(h * scale) for h in row_heights]

        y_pos = 0
        for i, (font_type, text) in enumerate(rows):
            if i >= 12:
                break

            # 스크롤 속도: si 비례 가속
            base_speed = 0.5 + len(text) * 0.02
            speed = base_speed * (0.5 + si * 1.5)
            self._scroll_offsets[i] += speed

            # 행별 jitter (si > 0.4)
            row_jitter = 0
            if si > 0.4 and frame_rms > 0.05:
                row_jitter = int(si * frame_rms * 12 * (1 + (i % 3)))

            y = y_pos + row_jitter
            x_offset = int(-self._scroll_offsets[i]) % max(len(text) * char_width, 1)

            font = font_kr if font_type == "kr" else font_mono
            color = text_color if i < 3 else dim_color

            # Draw text (repeated for seamless scroll)
            draw.text((x_offset, y), text, fill=color, font=font)
            draw.text((x_offset + len(text) * char_width, y), text,
                      fill=color, font=font)

            y_pos += row_heights[i] if i < len(row_heights) else base_row_height

        # ===== Post-Processing 이펙트 =====
        canvas = np.array(img)

        # 텍스트 글로우 (si > 0.3)
        if si > 0.3:
            img_glow = tts_effects.text_glow(img, reactive, glow_radius=4)
            canvas = np.array(img_glow)

        # 스캔라인 (항상)
        canvas = tts_effects.scanlines(canvas, reactive, line_spacing=4, darkness=0.35)

        # Chromatic aberration (si > 0.5)
        if si > 0.5:
            canvas = tts_effects.chromatic_aberration(canvas, si, max_offset=8)

        # Data click 폭발
        if data_click:
            canvas = tts_effects.data_click_explosion(canvas, accent, si, frame_idx)

        return canvas
