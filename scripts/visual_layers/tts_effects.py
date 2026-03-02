"""
visual_layers/tts_effects.py
TTS 비주얼 레이어 공유 이펙트 모듈.

semantic_intensity(0-1) 기반으로 크기, 색상, 왜곡, 글리치 등을
다이나믹하게 제어하는 유틸리티 함수 모음.

사용: TextDataLayer, DataStreamLayer, BarcodeLayer 공통 임포트.
"""

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ============================================================
# Font Cache (프레임마다 재로딩 방지)
# ============================================================
_font_cache = {}


def get_scaled_font(intensity, min_size=18, max_size=48, monospace=True):
    """
    Intensity에 비례하는 폰트 크기 반환 + 캐시.
    intensity 0.0 → min_size, intensity 1.0 → max_size

    Returns:
        (ImageFont, int): (폰트 객체, 실제 크기)
    """
    if not HAS_PIL:
        return None, min_size

    size = int(min_size + (max_size - min_size) * intensity)
    cache_key = (size, monospace)

    if cache_key not in _font_cache:
        font_names = (
            ["consola.ttf", "cour.ttf"] if monospace
            else ["malgun.ttf", "gulim.ttc", "batang.ttc"]
        )
        font = None
        for name in font_names:
            try:
                font = ImageFont.truetype(name, size)
                break
            except (OSError, IOError):
                continue
        if font is None:
            font = ImageFont.load_default()
        _font_cache[cache_key] = font

    return _font_cache[cache_key], size


# ============================================================
# Color Functions
# ============================================================
def intensity_color(base_rgb, intensity, brightness=1.0):
    """
    Intensity 기반 색상 계산.
    - 저강도: 탈색(회색 쪽), 어두움
    - 고강도: 풀 채도 + white bloom
    """
    r, g, b = float(base_rgb[0]), float(base_rgb[1]), float(base_rgb[2])
    gray = (r + g + b) / 3.0

    # Saturation: 저강도=20% 채도, 고강도=100%
    sat = 0.2 + intensity * 0.8
    r2 = gray + (r - gray) * sat
    g2 = gray + (g - gray) * sat
    b2 = gray + (b - gray) * sat

    # Brightness
    r2 *= brightness
    g2 *= brightness
    b2 *= brightness

    # White bloom at high intensity
    if intensity > 0.7:
        bloom = (intensity - 0.7) / 0.3  # 0→1
        r2 = r2 + (255 - r2) * bloom * 0.3
        g2 = g2 + (255 - g2) * bloom * 0.3
        b2 = b2 + (255 - b2) * bloom * 0.3

    return (
        int(np.clip(r2, 0, 255)),
        int(np.clip(g2, 0, 255)),
        int(np.clip(b2, 0, 255)),
    )


def hue_shift_color(base_rgb, shift_amount):
    """
    색조(hue) 회전. RGB 채널 믹싱으로 구현.
    shift_amount: -1.0 ~ 1.0 (0 = 변화 없음)
    """
    r, g, b = base_rgb[0] / 255.0, base_rgb[1] / 255.0, base_rgb[2] / 255.0
    cos_a = np.cos(shift_amount * np.pi)
    sin_a = np.sin(shift_amount * np.pi)

    r2 = (r * (0.667 + cos_a * 0.333)
          + g * (0.333 - cos_a * 0.333 - sin_a * 0.577)
          + b * (0.333 - cos_a * 0.333 + sin_a * 0.577))
    g2 = (r * (0.333 - cos_a * 0.333 + sin_a * 0.577)
          + g * (0.667 + cos_a * 0.333)
          + b * (0.333 - cos_a * 0.333 - sin_a * 0.577))
    b2 = (r * (0.333 - cos_a * 0.333 - sin_a * 0.577)
          + g * (0.333 - cos_a * 0.333 + sin_a * 0.577)
          + b * (0.667 + cos_a * 0.333))

    return (
        int(np.clip(r2 * 255, 0, 255)),
        int(np.clip(g2 * 255, 0, 255)),
        int(np.clip(b2 * 255, 0, 255)),
    )


# ============================================================
# Post-Processing Effects (numpy H,W,3 uint8)
# ============================================================
def chromatic_aberration(canvas, intensity, max_offset=10):
    """
    RGB 채널 오프셋. R 왼쪽, B 오른쪽, G 고정.
    고강도일수록 오프셋 커짐.
    """
    if intensity < 0.05:
        return canvas
    offset = int(max_offset * intensity)
    if offset < 1:
        return canvas

    result = canvas.copy()
    h, w, _ = canvas.shape
    # R channel → 왼쪽
    result[:, :w - offset, 0] = canvas[:, offset:, 0]
    # B channel → 오른쪽
    result[:, offset:, 2] = canvas[:, :w - offset, 2]
    return result


def scanlines(canvas, intensity, line_spacing=3, darkness=0.5):
    """
    CRT 스캔라인 효과.
    intensity가 높을수록 더 어둡고 촘촘한 라인.
    """
    if intensity < 0.03:
        return canvas

    result = canvas.astype(np.float32)
    spacing = max(2, line_spacing - int(intensity * 2))
    dark = 1.0 - darkness * intensity

    for y in range(0, canvas.shape[0], spacing):
        result[y, :, :] *= dark

    return np.clip(result, 0, 255).astype(np.uint8)


def glitch_blocks(canvas, intensity, frame_idx, max_blocks=6):
    """
    랜덤 직사각형 변위 + 색 반전.
    블록 수와 크기가 intensity에 비례.
    """
    if intensity < 0.2:
        return canvas

    result = canvas.copy()
    h, w, _ = canvas.shape
    rng = np.random.RandomState(frame_idx)

    n_blocks = max(1, int(max_blocks * intensity))
    for _ in range(n_blocks):
        bh = rng.randint(4, int(30 * intensity) + 5)
        bw = rng.randint(20, int(200 * intensity) + 30)
        y = rng.randint(0, max(1, h - bh))
        x = rng.randint(0, max(1, w - bw))

        dx = rng.randint(-int(20 * intensity), int(20 * intensity) + 1)
        src_x = max(0, min(w - bw, x + dx))

        if rng.random() < 0.5:
            # 색 반전
            result[y:y + bh, x:x + bw] = 255 - canvas[y:y + bh, x:x + bw]
        else:
            # 수평 변위
            result[y:y + bh, x:x + bw] = canvas[y:y + bh, src_x:src_x + bw]

    return result


def text_glow(img_pil, intensity, glow_radius=4):
    """
    텍스트 주변 가우시안 블러 후광.
    PIL Image 입력/출력.
    """
    if not HAS_PIL or intensity < 0.2:
        return img_pil

    radius = max(1, int(glow_radius * intensity))
    blurred = img_pil.filter(ImageFilter.GaussianBlur(radius=radius))

    glow_alpha = min(0.6, intensity * 0.5)
    orig_arr = np.array(img_pil, dtype=np.float32)
    blur_arr = np.array(blurred, dtype=np.float32)
    result = orig_arr + blur_arr * glow_alpha
    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))


def vertical_wave_distortion(canvas, intensity, time_sec, freq=0.04, max_amp=15):
    """
    사인파 기반 행별 수평 변위. 물결치는 텍스트 효과.
    """
    if intensity < 0.1:
        return canvas

    result = np.zeros_like(canvas)
    h, w, _ = canvas.shape
    amplitude = int(max_amp * intensity)

    for y in range(h):
        dx = int(amplitude * np.sin(y * freq + time_sec * 3.0))
        if dx > 0:
            result[y, dx:, :] = canvas[y, :w - dx, :]
        elif dx < 0:
            result[y, :w + dx, :] = canvas[y, -dx:, :]
        else:
            result[y] = canvas[y]

    return result


def scale_pulse(base_size, intensity, frame_idx, bpm=128, pulse_range=0.2):
    """
    BPM 동기 크기 맥동.
    Returns: 맥동 적용된 정수 크기.
    """
    if intensity < 0.05:
        return base_size
    beat_freq = bpm / 60.0
    phase = (frame_idx / 30.0) * beat_freq * 2 * np.pi
    pulse = 1.0 + np.sin(phase) * pulse_range * intensity
    return max(1, int(base_size * pulse))


def data_click_explosion(canvas, accent_color, intensity, frame_idx):
    """
    Data click 이벤트 시 드라마틱 폭발 효과.
    - 전체 밝기 서지
    - 중심에서 퍼지는 리플 링
    """
    result = canvas.astype(np.float32)
    h, w, _ = canvas.shape

    # 전체 밝기 서지
    flash_strength = 0.5 + intensity * 0.5
    result += flash_strength * 80

    # 리플 링
    cy, cx = h // 2, w // 2
    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    ring_phase = (frame_idx % 8) / 8.0
    ring = np.sin(dist * 0.1 - ring_phase * np.pi * 4) * 0.5 + 0.5
    ring = (ring * 60 * intensity).astype(np.float32)

    accent = (
        accent_color if isinstance(accent_color, (list, tuple))
        else (255, 255, 255)
    )
    for c in range(3):
        result[:, :, c] += ring * (accent[c] / 255.0)

    return np.clip(result, 0, 255).astype(np.uint8)
