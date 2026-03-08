"""
visual_layers/ascii_background_layer.py
ASCII 텍스처 배경 — 12×12px 셀 그리드에 SI 기반 문자 밀도 렌더링.
ep_seed 결정론적, 키워드 위치 하이라이트.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# 밀도별 문자 세트 (SI 낮→높)
_DENSITY_CHARS = [
    " ",           # 0: 빈 공간
    ".",           # 1: 최소
    ". :",         # 2
    ".: -",        # 3
    ".:;-+",       # 4
    ".:;=+*",      # 5
    "+*#@%&",      # 6: 최대
]

CELL_SIZE = 12  # px


class AsciiBackgroundLayer:
    def __init__(self, width, height, palette, intensity=0.2, blend="additive"):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend
        self.cols = width // CELL_SIZE
        self.rows = height // CELL_SIZE
        self._font = self._load_font()

    def _load_font(self):
        """monospace 폰트 로드 (시스템 fallback)"""
        for name in ["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"]:
            try:
                return ImageFont.truetype(name, CELL_SIZE - 2)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame_idx = ctx.get("frame_idx", 0)
        si = ctx.get("semantic_intensity", ctx.get("si", 0.5))
        script_data = ctx.get("script_data")
        time_sec = ctx.get("time", 0)
        # ep_seed: script_data에서 추출 또는 기본값
        ep_seed = 42
        if script_data and "metadata" in script_data:
            ep_seed = script_data["metadata"].get("ep_seed", 42)

        accent = np.array(
            ctx.get("accent_color") or self.palette.get("accent", (120, 200, 120)),
            dtype=np.uint8,
        )

        # SI → 밀도 레벨 (0~6)
        density_level = int(np.clip(si * 6.9, 0, 6))
        chars = _DENSITY_CHARS[density_level]
        if not chars.strip():
            return canvas  # 밀도 0이면 빈 캔버스

        # 현재 세그먼트 키워드 추출
        highlight_words = []
        if script_data:
            for seg in script_data.get("segments", []):
                if seg["start_sec"] <= time_sec < seg["end_sec"]:
                    for kw in seg.get("analysis", {}).get("keywords", []):
                        highlight_words.append(kw.get("word", ""))
                    break

        # 결정론적 RNG (ep_seed + frame_idx 기반, 8프레임 단위 갱신)
        rng = np.random.RandomState(ep_seed * 10000 + frame_idx // 8)

        # Pillow 렌더링
        img = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 기본 색상 (accent × intensity)
        base_color = tuple(int(c * self.intensity) for c in accent)

        # 하이라이트 셀 위치 (키워드 해시 기반)
        highlight_cells = set()
        for word in highlight_words:
            if not word:
                continue
            h = hash(word) & 0xFFFFFFFF
            for i in range(3):  # 키워드당 3셀
                r = (h + i * 7) % self.rows
                c = (h * 13 + i * 31) % self.cols
                highlight_cells.add((r, c))

        for row in range(self.rows):
            for col in range(self.cols):
                ch = chars[rng.randint(0, len(chars))]
                x = col * CELL_SIZE
                y = row * CELL_SIZE

                if (row, col) in highlight_cells:
                    # 하이라이트: accent 원색 + 밝기 부스트
                    color = tuple(min(255, int(c * 0.7)) for c in accent)
                else:
                    color = base_color

                draw.text((x + 1, y), ch, fill=color, font=self._font)

        canvas = np.array(img, dtype=np.uint8)
        return canvas
