"""
visual_layers/text_data_layer.py
터미널/콘솔 스타일 — 단어별 고유 메타데이터 표시.
상단: 시스템 상태 헤더
중앙: 단어별 데이터 카드
하단: 문장 구조 파싱

v2: semantic_intensity 기반 다이나믹 비주얼
    - 폰트: 16→48px, 카드: 90→200px
    - 색상: 채도/밝기/hue shift/white bloom
    - 이펙트: jitter/glow/scanlines/chromatic/glitch/wave
"""

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from . import tts_effects


class TextDataLayer:
    def __init__(self, width, height, palette, intensity=0.7, blend="additive"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend

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
        bpm = ctx.get("bpm", 128)

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

        analysis = current_seg.get("analysis", {})
        keywords = analysis.get("keywords", [])
        total_segs = len(script_data.get("segments", [])) if script_data else 0

        img = Image.fromarray(canvas)
        draw = ImageDraw.Draw(img)

        # ===== 다이나믹 색상 =====
        brightness = (si * 0.7 + 0.1) + frame_rms * 0.4
        brightness = min(1.0, brightness) * self.intensity
        accent_color = tts_effects.intensity_color(accent, si, brightness)
        dim_color = tts_effects.intensity_color(accent, si * 0.6, brightness * 0.5)
        very_dim = tts_effects.intensity_color(accent, si * 0.3, brightness * 0.25)

        # Hue shift (si > 0.5)
        if si > 0.5:
            shift = np.sin(time_sec * 0.8) * (si - 0.5) * 0.4
            accent_color = tts_effects.hue_shift_color(accent_color, shift)

        # Data click → brightness surge
        if data_click:
            brightness = min(1.0, brightness * 3.0)
            accent_color = tuple(min(255, int(c * 1.8)) for c in accent_color)

        # ===== 다이나믹 jitter =====
        jitter_x = int(reactive * 30 * frame_rms * 3) if frame_rms > 0.05 else 0
        jitter_y = int((si - 0.6) * 15 * frame_rms * 4) if si > 0.6 else 0

        # ===== 다이나믹 폰트 =====
        header_font, header_size = tts_effects.get_scaled_font(si, 16, 28, monospace=True)
        card_body_font, _ = tts_effects.get_scaled_font(si, 14, 28, monospace=True)
        parse_font, _ = tts_effects.get_scaled_font(si, 14, 24, monospace=True)

        # ===== 상단 (10%): 시스템 상태 헤더 =====
        header_y = 10
        time_str = f"{int(time_sec//60):02d}:{time_sec%60:06.3f}"
        header = (
            f"[{time_str}] SEG_{seg_idx:02d}/{total_segs} | "
            f"TOKENS:{analysis.get('token_count', 0)} "
            f"BYTES:{analysis.get('byte_count', 0)} "
            f"SI:{si:.2f}"
        )
        draw.text((10 + jitter_x, header_y + jitter_y), header,
                  fill=accent_color, font=header_font)

        # 구분선 (BPM 맥동 두께)
        line_y = header_y + header_size + 6
        line_w = tts_effects.scale_pulse(2, si, frame_idx, bpm, 0.5)
        draw.line([(0, line_y), (self.width, line_y)], fill=dim_color, width=line_w)

        # ===== 중앙 (50%): 단어별 데이터 카드 =====
        card_y = line_y + 8

        # 카드 높이: 90→200px (si 비례)
        card_height = int(90 + 110 * si)

        # 카드 열 수: si > 0.7이면 2열 (카드 확대)
        if si > 0.7 and len(keywords) > 2:
            cards_per_row = 2
        else:
            cards_per_row = min(3, max(1, len(keywords)))

        card_width = (self.width - 20) // max(cards_per_row, 1)
        max_cards = cards_per_row * 2  # 최대 2행

        for i, kw in enumerate(keywords[:max_cards]):
            row = i // cards_per_row
            col = i % cards_per_row
            kw_intensity = kw.get("intensity", 0.3)

            # 키워드별 개별 흔들림
            kw_jitter_x = int(kw_intensity * frame_rms * 15)
            kw_jitter_y = int(kw_intensity * frame_rms * 8) if si > 0.5 else 0

            cx = 10 + col * card_width + jitter_x + kw_jitter_x
            cy = card_y + row * (card_height + 8) + jitter_y + kw_jitter_y

            word_data = kw.get("word_data", {})
            kw_text = kw.get("text", "?")
            kw_type = kw.get("type", "noun")

            # 카드 테두리 (BPM 맥동 두께, intensity 비례)
            border_w = tts_effects.scale_pulse(
                int(1 + 3 * kw_intensity), kw_intensity, frame_idx, bpm, 0.3
            )
            # 키워드별 색상
            kw_color = tts_effects.intensity_color(accent, kw_intensity, brightness)

            draw.rectangle(
                [(cx, cy), (cx + card_width - 8, cy + card_height)],
                outline=kw_color, width=border_w
            )

            # 카드 제목: 다이나믹 폰트 크기 (20→48px, 키워드별 intensity)
            title_font, title_size = tts_effects.get_scaled_font(
                kw_intensity, 20, 48, monospace=False
            )
            draw.text((cx + 6, cy + 4), f"{kw_text} [{kw_type}]",
                      fill=kw_color, font=title_font)

            # UTF-8 hex
            hex_str = word_data.get("hex", "")
            max_hex_len = (card_width - 20) // 8
            if len(hex_str) > max_hex_len:
                hex_str = hex_str[:max_hex_len] + ".."
            y_off = cy + title_size + 8
            draw.text((cx + 6, y_off), f"UTF8: {hex_str}",
                      fill=dim_color, font=card_body_font)

            # Hash + bytes
            xor_hex = word_data.get("xor_hex", "?")
            byte_count = word_data.get("byte_count", 0)
            y_off += 18 + int(si * 8)
            draw.text((cx + 6, y_off), f"HASH:{xor_hex} B:{byte_count}",
                      fill=dim_color, font=card_body_font)

            # Freq + variance
            freq = word_data.get("freq_hz", 0)
            variance = word_data.get("byte_variance", 0)
            y_off += 18 + int(si * 8)
            draw.text((cx + 6, y_off), f"FREQ:{freq}Hz VAR:{variance:.0f}",
                      fill=dim_color, font=card_body_font)

            # Number extra data
            if kw.get("type") == "number":
                nd = kw.get("number_data", {})
                y_off += 18 + int(si * 8)
                draw.text((cx + 6, y_off),
                          f"BIN:{nd.get('binary','?')} HEX:{nd.get('hex','?')}",
                          fill=dim_color, font=card_body_font)

        # ===== 하단 (30%): 문장 구조 파싱 =====
        bottom_y = self.height - int(80 + si * 30)
        draw.line([(0, bottom_y), (self.width, bottom_y)], fill=very_dim, width=1)

        # Parse structure
        tokens = analysis.get("tokens", [])
        parse_parts = []
        for t in tokens:
            ttype = t.get("type", "?")
            ttext = t.get("text", "?")
            parse_parts.append(f"[{ttype[0].upper()}:{ttext}]")
        parse_str = " ".join(parse_parts)
        max_parse_len = int(self.width / 10)
        if len(parse_str) > max_parse_len:
            parse_str = parse_str[:max_parse_len] + "..."
        draw.text((10 + jitter_x, bottom_y + 5), f"PARSE: {parse_str}",
                  fill=dim_color, font=parse_font)

        # Sentence metadata + semantic intensity bar
        stype = analysis.get("sentence_type", "?")
        char_count = analysis.get("char_count", 0)
        token_count = analysis.get("token_count", 0)
        si_bar = "█" * int(si * 10) + "░" * (10 - int(si * 10))
        meta_str = f"TYPE:{stype.upper()} | TOKENS:{token_count} | CHARS:{char_count} | SI:[{si_bar}]"
        draw.text((10 + jitter_x, bottom_y + 24 + int(si * 6)), meta_str,
                  fill=very_dim, font=parse_font)

        # Frame counter
        draw.text((10, bottom_y + 48 + int(si * 12)), f"FRAME:{frame_idx:06d}",
                  fill=very_dim, font=parse_font)

        # ===== Post-Processing 이펙트 =====
        canvas = np.array(img)

        # 텍스트 글로우 (si > 0.3)
        if si > 0.3:
            img_glow = tts_effects.text_glow(img, reactive, glow_radius=4)
            canvas = np.array(img_glow)

        # 스캔라인 (항상, reactive_level 비례)
        canvas = tts_effects.scanlines(canvas, reactive, line_spacing=3, darkness=0.4)

        # Chromatic aberration (si > 0.4)
        if si > 0.4:
            canvas = tts_effects.chromatic_aberration(canvas, si, max_offset=10)

        # 글리치 블록 (si > 0.6)
        if si > 0.6:
            canvas = tts_effects.glitch_blocks(canvas, si, frame_idx, max_blocks=5)

        # 수직 웨이브 왜곡 (si > 0.5)
        if si > 0.5:
            canvas = tts_effects.vertical_wave_distortion(
                canvas, si, time_sec, freq=0.04, max_amp=12
            )

        # Data click 폭발
        if data_click:
            canvas = tts_effects.data_click_explosion(canvas, accent, si, frame_idx)

        return canvas
