"""
ENOMETA Generative Music Engine v5 — Raw Synthesis + Genre Overhaul
대본의 감정을 읽고 1곡의 연속적 음악을 생성하는 엔진.
GPU 불필요. numpy + scipy만으로 동작.

v5 변경사항:
- 새 합성 방법론: bytebeat(수학 공식), feedback_loop(자기참조), wavefold(파형접기)
- 칩튠: chiptune_square(펄스파), chiptune_noise_drum(LFSR 노이즈)
- 유클리드 리듬: euclidean_rhythm (Bjorklund 알고리즘)
- 장르 전면 교체: techno / bytebeat / algorave / harsh_noise / chiptune
- 장르별 synthesis_overrides: 마스터링 체인에 bit_depth, wavefold 등 적용

사용법:
  python enometa_music_engine.py <music_script.json> [output.wav]
  python enometa_music_engine.py --from-visual <visual_script.json> [narration_timing.json] [output.wav] [--genre techno]
"""

import sys
import json
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter, butter
import random

SAMPLE_RATE = 44100
random.seed(42)
np.random.seed(42)


# ============================================================
# 기본 사운드 생성 함수들
# ============================================================

def sine(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def noise(duration, sr=SAMPLE_RATE):
    return np.random.uniform(-1, 1, int(sr * duration))


# ============================================================
# 이펙트
# ============================================================

def lowpass(signal, cutoff, sr=SAMPLE_RATE, order=4):
    nyq = sr / 2
    cutoff = min(max(cutoff, 1), nyq * 0.99)
    b, a = butter(order, cutoff / nyq, btype='low')
    return lfilter(b, a, signal)


def highpass(signal, cutoff, sr=SAMPLE_RATE, order=2):
    nyq = sr / 2
    cutoff = max(min(cutoff, nyq * 0.99), 1)
    b, a = butter(order, cutoff / nyq, btype='high')
    return lfilter(b, a, signal)


def bandpass(signal, low, high, sr=SAMPLE_RATE, order=2):
    nyq = sr / 2
    low = max(min(low, nyq * 0.99), 1)
    high = max(min(high, nyq * 0.99), low + 1)
    b, a = butter(order, [low / nyq, high / nyq], btype='band')
    return lfilter(b, a, signal)


def reverb(signal, decay=0.4, delay_ms=80, repeats=6, sr=SAMPLE_RATE):
    result = signal.copy()
    delay_samples = int(sr * delay_ms / 1000)
    for i in range(1, repeats + 1):
        offset = delay_samples * i
        gain = decay ** i
        padded = np.pad(signal, (offset, 0))[:len(signal)]
        result += padded * gain
    return result / (1 + decay)


def fade_in(signal, duration_sec=0.5, sr=SAMPLE_RATE):
    samples = min(int(sr * duration_sec), len(signal))
    env = np.ones(len(signal))
    env[:samples] = np.linspace(0, 1, samples)
    return signal * env


def fade_out(signal, duration_sec=0.5, sr=SAMPLE_RATE):
    samples = min(int(sr * duration_sec), len(signal))
    env = np.ones(len(signal))
    env[-samples:] = np.linspace(1, 0, samples)
    return signal * env


def envelope(signal, attack=0.1, decay=0.2, sustain=0.6, release=0.3, sr=SAMPLE_RATE):
    total = len(signal)
    a = int(sr * attack)
    d = int(sr * decay)
    r = int(sr * release)
    s = total - a - d - r
    if s < 0:
        s = 0
        r = max(0, total - a - d)
    env = np.concatenate([
        np.linspace(0, 1, max(a, 1)),
        np.linspace(1, sustain, max(d, 1)),
        np.full(max(s, 0), sustain),
        np.linspace(sustain, 0, max(r, 1)),
    ])[:total]
    if len(env) < total:
        env = np.pad(env, (0, total - len(env)))
    return signal * env


def stereo_pan(mono, pan=0.0):
    left_gain = np.sqrt((1 - pan) / 2)
    right_gain = np.sqrt((1 + pan) / 2)
    return np.column_stack([mono * left_gain, mono * right_gain])


def smooth_envelope(total_samples, sections, instrument_key, param="volume",
                    default=0.0, morph_sec=0.8, sr=SAMPLE_RATE):
    """섹션별 파라미터를 부드럽게 보간한 엔벨로프 생성 (v5: cumsum 이동평균)"""
    env = np.full(total_samples, default, dtype=np.float64)
    for section in sections:
        cfg = section.get("instruments", {}).get(instrument_key, {})
        if not cfg.get("active"):
            val = 0.0
        else:
            val = cfg.get(param, default)
        start = int(sr * section["start_sec"])
        end = min(int(sr * section["end_sec"]), total_samples)
        env[start:end] = val

    # 모핑: cumsum 기반 이동 평균 (O(n), np.convolve O(n*m) 대비 수천배 빠름)
    window = int(sr * morph_sec)
    if window > 1 and len(env) > window:
        cumsum = np.cumsum(env)
        cumsum = np.insert(cumsum, 0, 0)
        smoothed = (cumsum[window:] - cumsum[:-window]) / window
        # 앞뒤 패딩으로 원본 길이 복원
        pad_left = window // 2
        pad_right = total_samples - len(smoothed) - pad_left
        env = np.concatenate([
            np.full(pad_left, smoothed[0]),
            smoothed,
            np.full(max(pad_right, 0), smoothed[-1])
        ])[:total_samples]
    return env


# ============================================================
# 악기/사운드 디자인 — 기존 (단일 렌더링용)
# ============================================================

def deep_bass_drone(freq, duration, sr=SAMPLE_RATE):
    """딥 베이스 드론 — 존재감, 무게, 공간의 바닥"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * 0.7
    wave += np.sin(2 * np.pi * (freq * 1.002) * t) * 0.4
    wave += np.sin(2 * np.pi * (freq * 0.5) * t) * 0.3
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
    wave *= lfo
    return wave


def modular_click(sr=SAMPLE_RATE):
    """모듈러 신스 클릭 — 데이터 포인트, 시간의 틱"""
    duration = 0.08
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    freq = random.uniform(2000, 6000)
    wave = np.sin(2 * np.pi * freq * t)
    env = np.exp(-t * 80)
    wave = wave * env * 0.5
    wave += noise(duration) * np.exp(-t * 120) * 0.2
    return wave


def bit_crush(signal, bits=8, downsample=4):
    """비트 크러시 — lo-fi 디스토션 (연산 최경량)"""
    # 비트 감소
    levels = 2 ** bits
    crushed = np.round(signal * levels) / levels
    # 다운샘플링 (sample-and-hold)
    if downsample > 1:
        held = np.repeat(crushed[::downsample], downsample)[:len(crushed)]
        return held
    return crushed


def fm_bass(freq, duration, mod_ratio=2.0, mod_depth=300, sr=SAMPLE_RATE):
    """FM 합성 베이스 — 2 오실레이터로 풍부한 음색 (초경량)"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 모듈레이터
    modulator = np.sin(2 * np.pi * freq * mod_ratio * t)
    # 캐리어 (FM: 캐리어 주파수를 모듈레이터로 변조)
    # mod_depth가 시간에 따라 감소 → 어택에서만 거친 음색
    depth_env = mod_depth * np.exp(-t * 2.5)
    phase = 2 * np.pi * freq * t + depth_env * modulator
    wave = np.sin(phase) * 0.5
    # 서브 레이어
    wave += np.sin(2 * np.pi * freq * 0.5 * t) * 0.3
    return wave


def noise_burst(sr=SAMPLE_RATE):
    """노이즈 버스트 — 짧은 필터드 임팩트 (연산 최경량)"""
    duration = 0.06
    n = noise(duration, sr)
    t = np.linspace(0, duration, len(n), endpoint=False)
    env = np.exp(-t * 70) * 0.5
    n *= env
    return n


def stutter_gate(signal, bpm, gate_divisions=8, sr=SAMPLE_RATE):
    """스터터 게이트 — 리듬 볼륨 게이팅 (곱셈만, 초경량)"""
    beat_sec = 60.0 / bpm
    gate_sec = beat_sec / gate_divisions
    gate_samples = int(sr * gate_sec)
    if gate_samples < 1:
        return signal
    # 온/오프 게이트 패턴 생성
    gate_env = np.zeros(len(signal))
    for i in range(0, len(signal), gate_samples * 2):
        on_end = min(i + gate_samples, len(signal))
        # 부드러운 게이트 (짧은 어택/릴리즈)
        on_len = on_end - i
        if on_len > 0:
            ramp = min(int(sr * 0.003), on_len // 4)
            gate_env[i:on_end] = 1.0
            if ramp > 0:
                gate_env[i:i+ramp] = np.linspace(0, 1, ramp)
                gate_env[on_end-ramp:on_end] = np.linspace(1, 0, ramp)
    return signal * gate_env


def tape_stop(signal, stop_duration=0.5, sr=SAMPLE_RATE):
    """테이프 정지 — 피치 다운 + 감속 효과"""
    stop_samples = int(sr * stop_duration)
    if stop_samples > len(signal):
        stop_samples = len(signal)
    # 마지막 stop_duration 구간에 적용
    result = signal.copy()
    segment = signal[-stop_samples:]
    # 속도 감소 커브 (1.0 → 0.0)
    speed_curve = np.linspace(1.0, 0.05, stop_samples) ** 0.5
    # 리샘플링으로 피치 다운 시뮬레이션
    new_positions = np.cumsum(speed_curve)
    new_positions = new_positions / new_positions[-1] * (stop_samples - 1)
    new_positions = np.clip(new_positions.astype(int), 0, stop_samples - 1)
    result[-stop_samples:] = segment[new_positions]
    # 볼륨 감소
    result[-stop_samples:] *= np.linspace(1.0, 0.0, stop_samples) ** 0.3
    return result


# ============================================================
# v5 — 새 합성 방법론
# ============================================================

# --- Bytebeat 공식 라이브러리 ---
BYTEBEAT_FORMULAS = {
    "sierpinski":  lambda t: t & (t >> 8),
    "cascade":     lambda t: t * ((t >> 12 | t >> 8) & 63 & t >> 4),
    "industrial":  lambda t: (t >> 6 | t | t >> (t >> 16 & 0xF)) * 10 + ((t >> 11) & 7),
    "melody":      lambda t: (t * (t >> 5 | t >> 8)) >> (t >> 16 & 0xF),
    "rhythm":      lambda t: t * 5 & (t >> 7) | t * 3 & (t * 4 >> 10),
    "chaos":       lambda t: (t ^ (t >> 4)) * (t & (t >> 8)),
    "drone":       lambda t: (t | (t >> 9 | t >> 7)) * t & (t >> 11 | t >> 9),
    "glitch":      lambda t: t * (t >> ((t >> 9 & 0xF) | (t >> 14 & 0xF))) & 255,
    "arpeggiated": lambda t: (t * (1 + (t >> 14 & 3))) >> (t >> 10 & 3),
    "bassline":    lambda t: (t >> 4) * (((t >> 12) % 6 + 1) & (t >> 8 | t >> 4)),
    "chipbeat":    lambda t: (t * (t >> 8 & 7) >> (t >> 12 & 7)) | (t >> 5),
    "fractal":     lambda t: t * t // (1 + (t >> 9 & 0xFF)),
}


def bytebeat(formula_id="sierpinski", duration=1.0, sr=SAMPLE_RATE):
    """Bytebeat — 수학 공식으로 원시 파형 생성 (Viznut 방식)"""
    # 8000Hz로 생성 (lo-fi 유지) → 44100 리샘플
    bytebeat_sr = 8000
    num_samples = int(bytebeat_sr * duration)
    formula = BYTEBEAT_FORMULAS.get(formula_id, BYTEBEAT_FORMULAS["sierpinski"])

    t_arr = np.arange(num_samples, dtype=np.int64)
    # 벡터 연산으로 공식 적용
    try:
        raw = formula(t_arr) & 0xFF  # uint8 범위로 마스킹
    except Exception:
        raw = t_arr & (t_arr >> 8) & 0xFF  # fallback: sierpinski

    # uint8 [0,255] → float [-1,1]
    audio = (raw.astype(np.float64) - 128.0) / 128.0

    # 8000Hz → 44100Hz 리샘플 (nearest neighbor로 lo-fi 유지)
    target_samples = int(sr * duration)
    indices = np.linspace(0, len(audio) - 1, target_samples).astype(int)
    resampled = audio[indices]

    return resampled * 0.4


def chiptune_square(freq, duration, duty=0.5, sr=SAMPLE_RATE):
    """칩튠 스퀘어파 — 듀티사이클 조절 가능 (NES/Game Boy 스타일)"""
    total_samples = int(sr * duration)
    phase = (np.arange(total_samples) * freq / sr) % 1.0
    wave = np.where(phase < duty, 1.0, -1.0)
    # 4bit 양자화 (16레벨) → 진짜 칩튠 느낌
    levels = 16
    wave = np.round(wave * levels) / levels
    return wave * 0.35


def chiptune_noise_drum(drum_type="kick", sr=SAMPLE_RATE):
    """칩튠 노이즈 드럼 — LFSR 기반 NES 스타일 퍼커션"""
    if drum_type == "kick":
        # 스퀘어파 피치 다운 + 짧은 노이즈 어택
        duration = 0.15
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        pitch_env = 200 * np.exp(-t * 40) + 40
        phase = np.cumsum(2 * np.pi * pitch_env / sr)
        wave = np.sign(np.sin(phase))  # 스퀘어파
        vol_env = np.exp(-t * 20)
        click = noise(0.005, sr) * np.exp(-np.linspace(0, 0.005, int(sr * 0.005)) * 500)
        wave[:len(click)] += click * 0.5
        wave *= vol_env * 0.5
        # 4bit 양자화
        wave = np.round(wave * 16) / 16
        return wave
    elif drum_type == "snare":
        # 스퀘어 톤 + 노이즈 혼합
        duration = 0.1
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        tone = np.sign(np.sin(2 * np.pi * 180 * t)) * np.exp(-t * 30) * 0.3
        n = noise(duration, sr) * np.exp(-t * 25) * 0.4
        wave = tone + n
        wave = np.round(wave * 16) / 16
        return wave
    else:  # hihat
        duration = 0.03
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        # 짧은 고주파 노이즈
        n = noise(duration, sr) * np.exp(-t * 100) * 0.25
        n = np.round(n * 16) / 16
        return n


def feedback_loop(seed_signal, iterations=5, feedback_gain=0.7,
                  delay_ms=30, distortion_type="wavefold", sr=SAMPLE_RATE):
    """피드백 루프 — 자기참조 신호로 카오틱 텍스처 생성"""
    delay_samples = int(sr * delay_ms / 1000)
    buffer = seed_signal.copy()

    for _ in range(iterations):
        # 지연된 신호를 되먹임
        delayed = np.roll(buffer, delay_samples)
        mixed = buffer + delayed * feedback_gain

        # 디스토션 적용 (혼돈 증가)
        if distortion_type == "wavefold":
            mixed = wavefold(mixed, folds=2)
        elif distortion_type == "bitcrush":
            mixed = bit_crush(mixed, bits=6, downsample=2)
        elif distortion_type == "clip":
            mixed = soft_clip(mixed, drive=3.0)
        else:
            mixed = np.tanh(mixed * 2.0)

        # 에너지 폭발 방지
        peak = np.max(np.abs(mixed))
        if peak > 2.0:
            mixed = mixed / peak * 1.5
        buffer = mixed

    return buffer * 0.35


def wavefold(signal, folds=3):
    """웨이브폴딩 — 모듈러 신스 디스토션 (파형 접기)"""
    # 신호 증폭 → ±1 경계에서 반사
    s = signal * folds
    # 삼각파 접기: [-1, 1] 범위로 반복 반사
    return 4.0 * (np.abs((s - 1) % 4 - 2) - 1) / 4.0


def euclidean_rhythm(steps, pulses):
    """유클리드 리듬 — Bjorklund 알고리즘으로 비대칭 패턴 생성"""
    # E(pulses, steps): N스텝에 K펄스를 최대한 균등 배치
    # 예: E(3,8) = [1,0,0,1,0,0,1,0], E(5,8) = [1,0,1,1,0,1,1,0]
    if pulses >= steps:
        return [True] * steps
    if pulses == 0:
        return [False] * steps

    # Bjorklund 알고리즘
    groups = [[True]] * pulses + [[False]] * (steps - pulses)
    while True:
        # 뒤쪽 그룹 수
        remainder = len(groups) - pulses
        if remainder <= 1:
            break
        limit = min(pulses, remainder)
        new_groups = []
        for i in range(limit):
            new_groups.append(groups[i] + groups[len(groups) - 1 - i])
        for i in range(limit, len(groups) - limit):
            new_groups.append(groups[i])
        groups = new_groups
        pulses = limit

    # 평탄화
    pattern = []
    for g in groups:
        pattern.extend(g)
    return pattern[:steps]


def glitch_texture(duration, density=0.3, sr=SAMPLE_RATE):
    """글리치 텍스처 v5 — 6종 이벤트: sine/bitcrush/stutter/noise/feedback/wavefold"""
    total_samples = int(sr * duration)
    result = np.zeros(total_samples)
    num_events = int(duration * density * 30)
    for _ in range(num_events):
        pos = random.randint(0, max(total_samples - int(sr * 0.05), 1))
        event_type = random.random()

        if event_type < 0.30:
            # 사인 그레인
            event_len = random.randint(int(sr * 0.001), int(sr * 0.02))
            freq = random.uniform(200, 12000)
            t = np.linspace(0, event_len / sr, event_len, endpoint=False)
            grain = np.sin(2 * np.pi * freq * t) * np.exp(-t * random.uniform(80, 300))
            grain *= random.uniform(0.05, 0.2)
        elif event_type < 0.50:
            # 비트 크러시 그레인
            event_len = random.randint(int(sr * 0.005), int(sr * 0.04))
            freq = random.uniform(100, 4000)
            t = np.linspace(0, event_len / sr, event_len, endpoint=False)
            grain = np.sin(2 * np.pi * freq * t)
            grain = bit_crush(grain, bits=random.choice([3, 4, 5, 6]), downsample=random.choice([2, 4, 8]))
            grain *= np.exp(-t * random.uniform(30, 100)) * 0.3
        elif event_type < 0.65:
            # 스터터 리피트 (같은 짧은 샘플 반복)
            micro_len = random.randint(int(sr * 0.001), int(sr * 0.005))
            repeats = random.randint(3, 12)
            micro = noise(micro_len / sr, sr) * random.uniform(0.05, 0.15)
            grain = np.tile(micro, repeats)
            event_len = len(grain)
        elif event_type < 0.75:
            # 노이즈 히트
            event_len = random.randint(int(sr * 0.002), int(sr * 0.015))
            grain = np.random.uniform(-1, 1, event_len)
            t = np.linspace(0, event_len / sr, event_len, endpoint=False)
            grain *= np.exp(-t * random.uniform(100, 400)) * 0.3
        elif event_type < 0.90:
            # v5: 피드백 루프 미니 이벤트
            seed_len = random.randint(int(sr * 0.005), int(sr * 0.02))
            seed = np.random.uniform(-0.5, 0.5, seed_len)
            grain = feedback_loop(seed, iterations=random.randint(2, 5),
                                  feedback_gain=random.uniform(0.5, 0.9),
                                  delay_ms=random.uniform(5, 20),
                                  distortion_type=random.choice(["wavefold", "bitcrush", "clip"]),
                                  sr=sr)
            grain *= random.uniform(0.1, 0.25)
            event_len = len(grain)
        else:
            # v5: 웨이브폴드 그레인
            event_len = random.randint(int(sr * 0.005), int(sr * 0.03))
            freq = random.uniform(80, 2000)
            t = np.linspace(0, event_len / sr, event_len, endpoint=False)
            grain = np.sin(2 * np.pi * freq * t)
            grain = wavefold(grain, folds=random.randint(2, 6))
            grain *= np.exp(-t * random.uniform(40, 150)) * 0.25

        end = min(pos + len(grain), total_samples)
        result[pos:end] += grain[:end - pos]
    return result


def arpeggio_sequence(base_freq, duration, pattern=None, speed=0.2, sr=SAMPLE_RATE):
    """시퀀서 아르페지오 v4 — 1사이클 생성 후 타일링 (5배+ 빠름)"""
    if pattern is None:
        pattern = [1, 1.25, 1.5, 2, 1.5, 1.25]
    total_samples = int(sr * duration)
    step_samples = max(int(sr * speed), 1)

    # 1사이클(패턴 전체) 사전 렌더링
    cycle_len = step_samples * len(pattern)
    cycle = np.zeros(cycle_len)
    for idx, ratio in enumerate(pattern):
        freq = base_freq * ratio
        t = np.linspace(0, speed, step_samples, endpoint=False)
        note = np.sin(2 * np.pi * freq * t)
        note = envelope(note, attack=0.005, decay=0.05, sustain=0.3, release=0.1)
        note *= 0.35
        start = idx * step_samples
        cycle[start:start + step_samples] = note

    # 타일링으로 전체 길이 채우기
    repeats = int(np.ceil(total_samples / cycle_len))
    result = np.tile(cycle, repeats)[:total_samples]
    # 리버브 1회만 (경량)
    result = reverb(result, decay=0.2, delay_ms=80, repeats=2)
    return result


def metallic_hit(freq=440, sr=SAMPLE_RATE):
    """메탈릭 히트 — 링 모듈레이션 기반 퍼커시브 사운드"""
    duration = 0.12
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 두 오실레이터의 곱 = 링 모듈레이션
    osc1 = np.sin(2 * np.pi * freq * t)
    osc2 = np.sin(2 * np.pi * freq * 1.414 * t)  # 비정수배 = 금속성
    wave = osc1 * osc2 * 0.4
    env = np.exp(-t * 40)
    wave *= env
    return wave


def noise_sweep(duration, direction="up", speed=0.3, sr=SAMPLE_RATE):
    """노이즈 스윕 v4 — 필터 루프 제거, 볼륨 엔벨로프로 대체 (10배 빠름)"""
    total_samples = int(sr * duration)
    n = noise(duration)
    if direction == "up":
        sweep_env = np.linspace(0.05, 1.0, total_samples) ** 1.5
    else:
        sweep_env = np.linspace(1.0, 0.05, total_samples) ** 1.5
    result = n * sweep_env * 0.4
    return result


def sub_pulse(freq, duration, bpm=80, sr=SAMPLE_RATE):
    """서브 베이스 펄스 v4 — 1비트 타일링 (빠름)"""
    total_samples = int(sr * duration)
    beat_interval = 60.0 / bpm
    beat_samples = int(sr * beat_interval)

    # 1비트 엔벨로프 사전 생성
    attack_len = int(sr * 0.02)
    release_len = int(sr * beat_interval * 0.6)
    one_beat_env = np.zeros(beat_samples)
    one_beat_env[:attack_len] = np.linspace(0, 1, attack_len)
    rel_end = min(attack_len + release_len, beat_samples)
    one_beat_env[attack_len:rel_end] = np.linspace(1, 0, rel_end - attack_len)

    # 타일링
    repeats = int(np.ceil(total_samples / beat_samples))
    pulse_env = np.tile(one_beat_env, repeats)[:total_samples]

    t = np.linspace(0, duration, total_samples, endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * pulse_env
    return wave


def reverse_swell(duration, freq=330, sr=SAMPLE_RATE):
    """리버스 스웰 — 기대감, 다가오는 변화"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.zeros_like(t)
    for dt in [0.998, 1.0, 1.002]:
        wave += np.sin(2 * np.pi * freq * dt * t) * 0.2
    env = np.linspace(0, 1, len(wave)) ** 2
    wave *= env
    wave = reverb(wave, decay=0.5, delay_ms=100, repeats=6)
    return wave


# ============================================================
# 새 악기 — v2 추가
# ============================================================

def kick_drum(freq=55, sr=SAMPLE_RATE):
    """킥 드럼 v4 — lowpass 제거, 볼륨 업"""
    duration = 0.35
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    pitch_env = freq * (1 + 6 * np.exp(-t * 35))
    phase = np.cumsum(2 * np.pi * pitch_env / sr)
    wave = np.sin(phase) * 0.9
    body_env = np.exp(-t * 10)
    wave *= body_env
    wave += np.sin(2 * np.pi * freq * t) * np.exp(-t * 5) * 0.4
    click = noise(0.005, sr) * np.exp(-np.linspace(0, 0.005, int(sr * 0.005)) * 800)
    click *= 0.25
    wave[:len(click)] += click
    return wave


def hi_hat(open_hat=False, sr=SAMPLE_RATE):
    """하이햇 v4 — highpass 제거, 볼륨 업"""
    duration = 0.15 if open_hat else 0.04
    n = noise(duration, sr)
    t = np.linspace(0, duration, len(n), endpoint=False)
    if open_hat:
        env = np.exp(-t * 15) * 0.25
    else:
        env = np.exp(-t * 60) * 0.2
    n *= env
    return n


def synth_lead(freq, duration, sr=SAMPLE_RATE):
    """신스 리드 v4 — lowpass 제거, reverb 경량화, 볼륨 업"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    vib = 1 + 0.003 * np.sin(2 * np.pi * 6 * t)
    wave = np.zeros_like(t)
    for h in range(1, 5):
        wave += np.sin(2 * np.pi * freq * h * vib * t) / h * ((-1) ** (h + 1))
    wave *= 0.3
    wave = envelope(wave, attack=0.02, decay=0.08, sustain=0.6, release=0.15)
    wave = reverb(wave, decay=0.2, delay_ms=60, repeats=1)
    return wave


def soft_clip(signal, drive=2.0):
    """소프트 클리핑 디스토션"""
    driven = signal * drive
    return np.tanh(driven)


def acid_bass(freq, duration, sweep_dir="down", sr=SAMPLE_RATE):
    """애시드 베이스 v4 — 청크 필터 루프 제거, 엔벨로프 기반 밝기 변화"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.zeros_like(t)
    for h in range(1, 8, 2):
        wave += np.sin(2 * np.pi * freq * h * t) / h
    wave *= 0.4
    wave = soft_clip(wave, drive=3.0)
    # 필터 스윕 대신 하모닉 엔벨로프로 밝기 변화 시뮬레이션
    if sweep_dir == "down":
        brightness = np.linspace(1.0, 0.3, len(wave))
    else:
        brightness = np.linspace(0.3, 1.0, len(wave))
    # 고주파 성분 감쇠 (간단한 1차 IIR 한 번만)
    wave *= brightness
    wave = envelope(wave, attack=0.005, decay=0.06, sustain=0.55, release=0.12)
    return wave


# ============================================================
# EnometaMusicEngine v3 — Raw Electronic 연속 렌더링
# ============================================================

class EnometaMusicEngine:
    def __init__(self, script: dict):
        self.script = script
        meta = script.get("metadata", {})
        self.sr = meta.get("sample_rate", SAMPLE_RATE)
        self.duration = meta.get("duration", 60)
        self.bpm = meta.get("base_bpm", 80)
        self.total_samples = int(self.sr * self.duration)
        self.master_L = np.zeros(self.total_samples)
        self.master_R = np.zeros(self.total_samples)

        palette = script.get("palette", {})
        self.bass_freq = palette.get("bass_freq", 82.4)
        self.pad_root = palette.get("pad_root", 329.6)
        self.pad_fifth = palette.get("pad_fifth", 493.9)
        self.arp_root = palette.get("arp_root", 220)
        self.arp_pattern = palette.get("arp_pattern", [1, 1.25, 1.5, 2, 1.5, 1.25])

    def _add_stereo(self, signal, pan, start_sec, vol=1.0):
        start = int(self.sr * start_sec)
        s = stereo_pan(signal * vol, pan)
        end = min(start + len(signal), self.total_samples)
        length = end - start
        if length <= 0:
            return
        self.master_L[start:end] += s[:length, 0]
        self.master_R[start:end] += s[:length, 1]

    def _add_mono(self, signal, start_sec, vol=1.0):
        start = int(self.sr * start_sec)
        end = min(start + len(signal), self.total_samples)
        length = end - start
        if length <= 0:
            return
        self.master_L[start:end] += signal[:length] * vol
        self.master_R[start:end] += signal[:length] * vol

    def _get_section_at(self, time_sec):
        """특정 시간에 활성화된 섹션 반환"""
        for s in self.script.get("sections", []):
            if s["start_sec"] <= time_sec < s["end_sec"]:
                return s
        return None

    # ---- 기반 악기: 전체 길이 연속 렌더링 ----

    def _render_continuous_bass(self, sections):
        """전체 길이 베이스 드론 — 볼륨만 섹션별 모핑"""
        print("  [bass] continuous drone...", flush=True)
        drone = deep_bass_drone(self.bass_freq, self.duration, self.sr)
        vol_env = smooth_envelope(
            len(drone), sections, "bass_drone", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        drone *= vol_env * 1.2
        # 전체 시작/끝 페이드
        drone = fade_in(fade_out(drone, 3.0), 2.0)
        self._add_mono(drone, 0, 1.0)

    def _render_continuous_fm_bass(self, sections):
        """전체 길이 FM 베이스 — 패드 대체, 초경량"""
        print("  [fm] continuous fm bass...", flush=True)
        fm = fm_bass(self.pad_root * 0.5, self.duration,
                     mod_ratio=2.0, mod_depth=200, sr=self.sr)
        vol_env = smooth_envelope(
            len(fm), sections, "fm_bass", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        fm *= vol_env * 1.0
        fm = fade_in(fade_out(fm, 2.0), 1.5)
        self._add_mono(fm, 0, 1.0)

    def _render_continuous_rhythm(self, sections):
        """전체 길이 킥 + 하이햇 v5 — 4비트 사전 렌더 + 타일링 + 유클리드 모드"""
        overrides = self.script.get("metadata", {}).get("synthesis_overrides", {})
        rhythm_mode = overrides.get("rhythm_mode", "standard")
        print(f"  [rhythm] continuous drums (mode={rhythm_mode})...", flush=True)
        beat_interval = 60.0 / self.bpm
        beat_samples = int(self.sr * beat_interval)

        if rhythm_mode == "euclidean":
            # v5: 유클리드 리듬 — 비대칭 킥/하이햇 패턴
            steps = 8  # 8스텝 (2마디 = 8비트)
            kick_pattern = euclidean_rhythm(steps, 3)   # E(3,8) — 3/8 비대칭 킥
            hihat_pattern = euclidean_rhythm(steps, 5)  # E(5,8) — 5/8 비대칭 하이햇

            bar_len = beat_samples * steps
            kick_bar = np.zeros(bar_len)
            hihat_bar_L = np.zeros(bar_len)
            hihat_bar_R = np.zeros(bar_len)

            k = kick_drum(self.bass_freq * 0.5, self.sr)
            for b in range(steps):
                if kick_pattern[b]:
                    pos = b * beat_samples
                    end = min(pos + len(k), bar_len)
                    kick_bar[pos:end] += k[:end - pos]

            for b in range(steps):
                if hihat_pattern[b]:
                    is_open = random.random() > 0.6
                    h = hi_hat(open_hat=is_open, sr=self.sr)
                    pan = random.uniform(-0.2, 0.2)
                    s = stereo_pan(h, pan)
                    pos = b * beat_samples
                    end = min(pos + len(h), bar_len)
                    hihat_bar_L[pos:end] += s[:end - pos, 0]
                    hihat_bar_R[pos:end] += s[:end - pos, 1]
        else:
            # 기존: 4-on-the-floor 표준 패턴
            bar_len = beat_samples * 4
            kick_bar = np.zeros(bar_len)
            hihat_bar_L = np.zeros(bar_len)
            hihat_bar_R = np.zeros(bar_len)

            # 킥: beat 0, 2
            k = kick_drum(self.bass_freq * 0.5, self.sr)
            for b in [0, 2]:
                pos = b * beat_samples
                end = min(pos + len(k), bar_len)
                kick_bar[pos:end] += k[:end - pos]

            # 하이햇: 매 비트 (open=1,3 / closed=0,2)
            for b in range(4):
                is_open = b in [1, 3]
                h = hi_hat(open_hat=is_open, sr=self.sr)
                pan = 0.15 if is_open else -0.1
                s = stereo_pan(h, pan)
                pos = b * beat_samples
                end = min(pos + len(h), bar_len)
                hihat_bar_L[pos:end] += s[:end - pos, 0]
                hihat_bar_R[pos:end] += s[:end - pos, 1]

        # 타일링
        repeats = int(np.ceil(self.total_samples / bar_len))
        kick_full = np.tile(kick_bar, repeats)[:self.total_samples]
        hihat_full_L = np.tile(hihat_bar_L, repeats)[:self.total_samples]
        hihat_full_R = np.tile(hihat_bar_R, repeats)[:self.total_samples]

        # 볼륨 엔벨로프 적용
        kick_vol_env = smooth_envelope(
            self.total_samples, sections, "kick", "volume",
            default=0.0, morph_sec=0.5, sr=self.sr
        )
        hihat_vol_env = smooth_envelope(
            self.total_samples, sections, "hi_hat", "volume",
            default=0.0, morph_sec=0.5, sr=self.sr
        )

        self.master_L += kick_full * kick_vol_env * 1.2
        self.master_R += kick_full * kick_vol_env * 1.2
        self.master_L += hihat_full_L * hihat_vol_env * 1.0
        self.master_R += hihat_full_R * hihat_vol_env * 1.0

    def _render_continuous_sub_pulse(self, sections):
        """전체 길이 서브 펄스"""
        print("  [sub] continuous sub pulse...", flush=True)
        sub = sub_pulse(self.bass_freq * 0.5, self.duration, self.bpm, self.sr)
        vol_env = smooth_envelope(
            len(sub), sections, "sub_pulse", "volume",
            default=0.0, morph_sec=0.8, sr=self.sr
        )
        sub *= vol_env * 0.7
        self._add_mono(sub, 0, 1.0)

    def _render_continuous_arpeggio(self, sections):
        """전체 길이 아르페지오 — 속도/볼륨 섹션별 변화"""
        print("  [arp] continuous arpeggio...", flush=True)
        # 평균 속도 계산
        speeds = []
        for s in sections:
            arp_cfg = s.get("instruments", {}).get("arpeggio", {})
            if arp_cfg.get("active"):
                speeds.append(arp_cfg.get("speed", 0.2))
        avg_speed = np.mean(speeds) if speeds else 0.2

        arp = arpeggio_sequence(
            self.arp_root, self.duration, self.arp_pattern,
            speed=avg_speed, sr=self.sr
        )
        vol_env = smooth_envelope(
            len(arp), sections, "arpeggio", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        arp *= vol_env * 1.2

        # 디튠 스테레오 쌍
        arp2 = arpeggio_sequence(
            self.arp_root + 1, self.duration,
            [p * 1.01 for p in self.arp_pattern],
            speed=avg_speed * 1.02, sr=self.sr
        )
        arp2 *= vol_env * 0.7

        self._add_stereo(arp, -0.3, 0, 1.0)
        self._add_stereo(arp2, 0.3, 0.05, 1.0)

    # ---- 텍스처 악기: 섹션 단위 (자연스럽게 등장/퇴장) ----

    def _render_section_textures(self, section):
        """섹션별 텍스처 악기 렌더링 (클릭, 글리치, 쉬머, 스윕, 리드, 애시드)"""
        start = section["start_sec"]
        dur = section["end_sec"] - section["start_sec"]
        if dur <= 0:
            return
        instruments = section.get("instruments", {})
        effects = section.get("effects", {})
        stereo_width = effects.get("stereo_width", 0.5)

        # Clicks
        clicks_cfg = instruments.get("clicks", {})
        if clicks_cfg.get("active"):
            density = clicks_cfg.get("density", 0.3)
            pan_spread = clicks_cfg.get("pan_spread", 0.5)
            t_click = 0.0
            interval = max(0.05, 0.5 / max(density, 0.01))
            while t_click < dur:
                click = modular_click(self.sr)
                pan = random.uniform(-pan_spread, pan_spread)
                vol = random.uniform(0.3, 0.7) * density
                self._add_stereo(click, pan, start + t_click, vol)
                t_click += random.uniform(interval * 0.5, interval * 1.5)

        # Glitch
        glitch_cfg = instruments.get("glitch", {})
        if glitch_cfg.get("active"):
            density = glitch_cfg.get("density", 0.3)
            glitch_signal = glitch_texture(dur, density, self.sr)
            glitch_signal = fade_in(fade_out(glitch_signal, min(dur * 0.3, 1.0)), min(dur * 0.2, 0.5))
            self._add_stereo(glitch_signal, 0.4 * stereo_width, start, 0.5)

        # Noise Burst
        burst_cfg = instruments.get("noise_burst", {})
        if burst_cfg.get("active"):
            density = burst_cfg.get("density", 0.3)
            interval = max(0.1, 0.6 / max(density, 0.01))
            t_burst = 0.0
            while t_burst < dur:
                burst = noise_burst(self.sr)
                pan = random.uniform(-0.6, 0.6)
                self._add_stereo(burst, pan, start + t_burst, density * 0.8)
                t_burst += random.uniform(interval * 0.5, interval * 1.5)

        # Metallic Hit
        metal_cfg = instruments.get("metallic_hit", {})
        if metal_cfg.get("active"):
            vol = metal_cfg.get("volume", 0.2)
            density = metal_cfg.get("density", 0.2)
            interval = max(0.15, 0.8 / max(density, 0.01))
            t_hit = 0.0
            while t_hit < dur:
                freq = random.uniform(300, 2000)
                hit = metallic_hit(freq, self.sr)
                pan = random.uniform(-0.5, 0.5)
                self._add_stereo(hit, pan, start + t_hit, vol)
                t_hit += random.uniform(interval * 0.5, interval * 1.5)

        # Noise Sweep
        sweep_cfg = instruments.get("noise_sweep", {})
        if sweep_cfg.get("active"):
            direction = sweep_cfg.get("direction", "up")
            speed = sweep_cfg.get("speed", 0.3)
            sweep = noise_sweep(dur, direction, speed, self.sr)
            self._add_stereo(sweep, 0.0, start, 0.6)

        # Synth Lead (새 악기)
        lead_cfg = instruments.get("synth_lead", {})
        if lead_cfg.get("active"):
            vol = lead_cfg.get("volume", 0.3)
            # 리드 멜로디: 아르페지오 패턴 기반으로 느린 멜로딕 라인
            lead_pattern = lead_cfg.get("pattern", [1, 1.5, 1.333, 2])
            note_dur = lead_cfg.get("note_duration", 0.8)
            t_note = 0.0
            note_idx = 0
            while t_note < dur:
                freq = self.pad_root * lead_pattern[note_idx % len(lead_pattern)]
                actual_dur = min(note_dur, dur - t_note)
                if actual_dur > 0.1:
                    note = synth_lead(freq, actual_dur, self.sr)
                    self._add_stereo(note, -0.15, start + t_note, vol)
                t_note += note_dur * 1.1  # 약간의 갭
                note_idx += 1

        # Acid Bass (새 악기)
        acid_cfg = instruments.get("acid_bass", {})
        if acid_cfg.get("active"):
            vol = acid_cfg.get("volume", 0.4)
            sweep_dir = acid_cfg.get("sweep_dir", "down")
            # BPM 동기화 베이스라인
            beat_interval = 60.0 / self.bpm
            note_dur = beat_interval * 0.8
            t_note = 0.0
            bass_pattern = acid_cfg.get("pattern", [1, 1, 1.5, 0.75, 1, 1.333])
            note_idx = 0
            while t_note < dur:
                freq = self.bass_freq * bass_pattern[note_idx % len(bass_pattern)]
                actual_dur = min(note_dur, dur - t_note)
                if actual_dur > 0.05:
                    ab = acid_bass(freq, actual_dur, sweep_dir, self.sr)
                    self._add_mono(ab, start + t_note, vol)
                t_note += beat_interval
                note_idx += 1

        # Stutter Gate (전체 섹션 오디오에 게이팅 효과)
        gate_cfg = instruments.get("stutter_gate", {})
        if gate_cfg.get("active"):
            divisions = gate_cfg.get("divisions", 8)
            start_sample = int(self.sr * start)
            end_sample = min(int(self.sr * section["end_sec"]), self.total_samples)
            seg_len = end_sample - start_sample
            if seg_len > 0:
                # 해당 구간의 마스터에 게이트 적용
                gate_signal = np.ones(seg_len)
                gate_signal = stutter_gate(gate_signal, self.bpm, divisions, self.sr)
                gate_blend = gate_cfg.get("blend", 0.5)  # 0=원본, 1=풀게이트
                blend = 1.0 - gate_blend + gate_blend * gate_signal
                self.master_L[start_sample:end_sample] *= blend
                self.master_R[start_sample:end_sample] *= blend

        # Tape Stop (섹션 끝부분에 테이프 정지 효과)
        tape_cfg = instruments.get("tape_stop", {})
        if tape_cfg.get("active"):
            stop_dur = tape_cfg.get("duration", 0.5)
            start_sample = int(self.sr * start)
            end_sample = min(int(self.sr * section["end_sec"]), self.total_samples)
            seg_len = end_sample - start_sample
            if seg_len > 0:
                seg_L = self.master_L[start_sample:end_sample].copy()
                seg_R = self.master_R[start_sample:end_sample].copy()
                self.master_L[start_sample:end_sample] = tape_stop(seg_L, stop_dur, self.sr)
                self.master_R[start_sample:end_sample] = tape_stop(seg_R, stop_dur, self.sr)

        # === v5 새 악기 ===

        # Bytebeat (수학 공식 오디오)
        bb_cfg = instruments.get("bytebeat", {})
        if bb_cfg.get("active"):
            vol = bb_cfg.get("volume", 0.4)
            formula_id = bb_cfg.get("formula", random.choice(list(BYTEBEAT_FORMULAS.keys())))
            bb_signal = bytebeat(formula_id, dur, self.sr)
            bb_signal = fade_in(fade_out(bb_signal, min(dur * 0.2, 0.5)), min(dur * 0.15, 0.3))
            self._add_stereo(bb_signal, random.uniform(-0.3, 0.3), start, vol)

        # Feedback Loop (자기참조 노이즈)
        fb_cfg = instruments.get("feedback", {})
        if fb_cfg.get("active"):
            vol = fb_cfg.get("volume", 0.3)
            iterations = fb_cfg.get("iterations", 6)
            # 짧은 시드 신호 생성 후 피드백
            seed_dur = min(dur, 2.0)
            seed = noise(seed_dur, self.sr) * 0.3
            fb_signal = feedback_loop(seed, iterations=iterations,
                                      feedback_gain=fb_cfg.get("gain", 0.7),
                                      delay_ms=fb_cfg.get("delay_ms", 30),
                                      distortion_type="wavefold", sr=self.sr)
            # 전체 섹션 길이로 확장 (타일링)
            total_sec_samples = int(dur * self.sr)
            if len(fb_signal) < total_sec_samples:
                repeats = int(np.ceil(total_sec_samples / len(fb_signal)))
                fb_signal = np.tile(fb_signal, repeats)[:total_sec_samples]
            else:
                fb_signal = fb_signal[:total_sec_samples]
            fb_signal = fade_in(fade_out(fb_signal, min(dur * 0.3, 1.0)), min(dur * 0.2, 0.5))
            self._add_stereo(fb_signal, 0.3, start, vol)

        # Chiptune Lead (칩튠 스퀘어파 리드)
        chip_lead_cfg = instruments.get("chiptune_lead", {})
        if chip_lead_cfg.get("active"):
            vol = chip_lead_cfg.get("volume", 0.35)
            duty = chip_lead_cfg.get("duty", 0.25)
            lead_pattern = chip_lead_cfg.get("pattern", [1, 1.25, 1.5, 2, 1.5, 1.25])
            note_dur = chip_lead_cfg.get("note_duration", 0.3)
            t_note = 0.0
            note_idx = 0
            while t_note < dur:
                freq = self.pad_root * lead_pattern[note_idx % len(lead_pattern)]
                actual_dur = min(note_dur, dur - t_note)
                if actual_dur > 0.05:
                    note = chiptune_square(freq, actual_dur, duty, self.sr)
                    env_samples = len(note)
                    env = np.exp(-np.linspace(0, 3, env_samples))
                    note = note * env
                    self._add_stereo(note, -0.2, start + t_note, vol)
                t_note += note_dur * 1.1
                note_idx += 1

        # Chiptune Drum (칩튠 노이즈 퍼커션)
        chip_drum_cfg = instruments.get("chiptune_drum", {})
        if chip_drum_cfg.get("active"):
            vol = chip_drum_cfg.get("volume", 0.4)
            beat_interval = 60.0 / self.bpm
            t_beat = 0.0
            beat_idx = 0
            while t_beat < dur:
                # 패턴: kick, hihat, snare, hihat
                drum_types = ["kick", "hihat", "snare", "hihat"]
                dtype = drum_types[beat_idx % 4]
                drum = chiptune_noise_drum(dtype, self.sr)
                pan = 0.0 if dtype == "kick" else random.uniform(-0.3, 0.3)
                self._add_stereo(drum, pan, start + t_beat, vol)
                t_beat += beat_interval
                beat_idx += 1

    def generate(self) -> np.ndarray:
        """music_script.json의 모든 섹션을 1곡으로 렌더링"""
        sections = self.script.get("sections", [])
        total = len(sections)
        print(f"  Rendering {total} sections as one continuous track...", flush=True)

        # Phase 1: 기반 악기 — 전체 길이 연속 렌더링
        self._render_continuous_bass(sections)
        self._render_continuous_fm_bass(sections)
        self._render_continuous_sub_pulse(sections)
        self._render_continuous_arpeggio(sections)
        self._render_continuous_rhythm(sections)

        # Phase 2: 텍스처 악기 — 섹션 단위 (자연스러운 등장/퇴장)
        for i, section in enumerate(sections):
            sid = section.get("id", f"sec_{i}")
            emotion = section.get("emotion", "?")
            print(f"  [{i+1}/{total}] textures: {sid} ({emotion})", flush=True)
            self._render_section_textures(section)

        return self._master()

    def _master(self) -> np.ndarray:
        """마스터링 v5: synthesis_overrides + soft_clip + RMS 노멀라이즈 + 페이드"""
        print("  Mastering v5 (synthesis_overrides + saturation + RMS normalize)...", flush=True)
        stereo = np.column_stack([self.master_L, self.master_R])

        # 0) synthesis_overrides 적용 (장르별 마스터 체인 변형)
        overrides = self.script.get("metadata", {}).get("synthesis_overrides", {})

        # 웨이브폴딩 (harsh_noise 장르)
        if "wavefold_master" in overrides:
            folds = overrides["wavefold_master"]
            for ch in range(2):
                stereo[:, ch] = wavefold(stereo[:, ch], folds)

        # 비트 양자화 (bytebeat/chiptune 장르)
        if "bit_depth" in overrides:
            bits = overrides["bit_depth"]
            for ch in range(2):
                stereo[:, ch] = bit_crush(stereo[:, ch], bits=bits, downsample=1)

        # 1) soft_clip 새츄레이션 — 피크를 자연스럽게 눌러 체감 음량 증가
        peak = np.max(np.abs(stereo))
        if peak > 0:
            stereo = stereo / peak  # normalize to [-1, 1] first
        stereo = np.tanh(stereo * 1.8)  # soft saturation (drive=1.8)

        # 2) RMS 노멀라이즈 — 타겟 -14dB (0.2 linear)
        rms = np.sqrt(np.mean(stereo ** 2))
        target_rms = 0.2  # -14dB
        if rms > 0:
            gain = target_rms / rms
            stereo *= gain
        # 피크 리미팅 (클리핑 방지)
        peak2 = np.max(np.abs(stereo))
        if peak2 > 0.95:
            stereo *= 0.95 / peak2

        # 3) 전체 페이드
        fade_in_samples = int(self.sr * 2)
        fade_out_samples = int(self.sr * 3)
        for ch in range(2):
            stereo[:fade_in_samples, ch] *= np.linspace(0, 1, fade_in_samples)
            stereo[-fade_out_samples:, ch] *= np.linspace(1, 0, fade_out_samples)

        # 4) 16bit WAV
        audio_16bit = (stereo * 32767).astype(np.int16)
        return audio_16bit


# ============================================================
# 감정 → 악기 매핑 테이블 v5: bytebeat/feedback/chiptune_lead/chiptune_drum 추가
# 장르 프리셋이 force_active/force_inactive로 최종 결정하므로 기본값만 배치
# ============================================================

EMOTION_MAP = {
    # === 뉴트럴 계열: 미니멀, 관찰적 ===
    "neutral": {
        "energy": 0.35,
        "bass_drone": {"active": True, "volume": 0.6},
        "clicks": {"active": True, "density": 0.3, "pan_spread": 0.4},
        "fm_bass": {"active": True, "volume": 0.25},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.35},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "neutral_curious": {
        "energy": 0.4,
        "bass_drone": {"active": True, "volume": 0.65},
        "clicks": {"active": True, "density": 0.5, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.35},
        "arpeggio": {"active": True, "speed": 0.35, "volume": 0.25},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.25},
        "hi_hat": {"active": True, "volume": 0.15},
        "sub_pulse": {"active": True, "volume": 0.4},
        "noise_burst": {"active": True, "density": 0.15},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.2, "duty": 0.25},
        "chiptune_drum": {"active": False},
    },
    "neutral_analytical": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.7},
        "clicks": {"active": True, "density": 0.6, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.4},
        "arpeggio": {"active": True, "speed": 0.25, "volume": 0.35},
        "glitch": {"active": True, "density": 0.25},
        "kick": {"active": True, "volume": 0.35},
        "hi_hat": {"active": True, "volume": 0.2},
        "sub_pulse": {"active": True, "volume": 0.45},
        "metallic_hit": {"active": True, "volume": 0.2, "density": 0.2},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.2},
    },
    "curious": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.7},
        "clicks": {"active": True, "density": 0.5, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.35},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.35},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.3},
        "hi_hat": {"active": True, "volume": 0.18},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.15, "duty": 0.5},
        "chiptune_drum": {"active": False},
    },
    # === 솜버 계열: 어둡고 무거운 ===
    "somber": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.85},
        "clicks": {"active": True, "density": 0.2, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.45},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "somber_reflective": {
        "energy": 0.5,
        "bass_drone": {"active": True, "volume": 0.8},
        "clicks": {"active": True, "density": 0.15, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.45},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "somber_repetitive": {
        "energy": 0.55,
        "bass_drone": {"active": True, "volume": 0.85},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.4},
        "fm_bass": {"active": True, "volume": 0.45},
        "arpeggio": {"active": True, "speed": 0.22, "volume": 0.6},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.25},
        "hi_hat": {"active": True, "volume": 0.15},
        "sub_pulse": {"active": True, "volume": 0.5},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.15},
    },
    "somber_analytical": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.9},
        "clicks": {"active": True, "density": 0.45, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.2, "volume": 0.65},
        "glitch": {"active": True, "density": 0.3},
        "kick": {"active": True, "volume": 0.35},
        "hi_hat": {"active": True, "volume": 0.18},
        "sub_pulse": {"active": True, "volume": 0.55},
        "noise_burst": {"active": True, "density": 0.2},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "somber_warning": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.9},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.45},
        "arpeggio": {"active": True, "speed": 0.2, "volume": 0.55},
        "glitch": {"active": True, "density": 0.25},
        "noise_sweep": {"active": True, "direction": "down", "speed": 0.3},
        "kick": {"active": True, "volume": 0.4},
        "hi_hat": {"active": True, "volume": 0.2},
        "sub_pulse": {"active": True, "volume": 0.6},
        "bytebeat": {"active": True, "volume": 0.15, "formula": "drone"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    # === 텐션 계열: 강렬, 공격적 ===
    "tension": {
        "energy": 0.75,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 1.2, "pan_spread": 0.8},
        "fm_bass": {"active": True, "volume": 0.6},
        "arpeggio": {"active": True, "speed": 0.15, "volume": 0.8},
        "glitch": {"active": True, "density": 0.7},
        "noise_sweep": {"active": True, "direction": "up", "speed": 0.3},
        "kick": {"active": True, "volume": 0.65},
        "hi_hat": {"active": True, "volume": 0.35},
        "acid_bass": {"active": True, "volume": 0.5, "sweep_dir": "down"},
        "sub_pulse": {"active": True, "volume": 0.8},
        "noise_burst": {"active": True, "density": 0.5},
        "bytebeat": {"active": True, "volume": 0.2, "formula": "industrial"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.25},
    },
    "tension_reveal": {
        "energy": 0.7,
        "bass_drone": {"active": True, "volume": 0.95},
        "clicks": {"active": True, "density": 1.0, "pan_spread": 0.7},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.18, "volume": 0.7},
        "glitch": {"active": True, "density": 0.55},
        "kick": {"active": True, "volume": 0.5},
        "hi_hat": {"active": True, "volume": 0.3},
        "sub_pulse": {"active": True, "volume": 0.7},
        "noise_burst": {"active": True, "density": 0.4},
        "metallic_hit": {"active": True, "volume": 0.25, "density": 0.25},
        "bytebeat": {"active": True, "volume": 0.15, "formula": "glitch"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "tension_transformative": {
        "energy": 0.8,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 1.1, "pan_spread": 0.8},
        "fm_bass": {"active": True, "volume": 0.6},
        "arpeggio": {"active": True, "speed": 0.12, "volume": 0.85},
        "glitch": {"active": True, "density": 0.7},
        "kick": {"active": True, "volume": 0.65},
        "hi_hat": {"active": True, "volume": 0.35},
        "acid_bass": {"active": True, "volume": 0.6, "sweep_dir": "up"},
        "sub_pulse": {"active": True, "volume": 0.8},
        "stutter_gate": {"active": True, "divisions": 8, "blend": 0.3},
        "bytebeat": {"active": True, "volume": 0.2, "formula": "chaos"},
        "feedback": {"active": True, "volume": 0.2, "iterations": 4},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "tension_redefine": {
        "energy": 0.78,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 1.0, "pan_spread": 0.75},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.14, "volume": 0.75},
        "glitch": {"active": True, "density": 0.6},
        "kick": {"active": True, "volume": 0.6},
        "hi_hat": {"active": True, "volume": 0.32},
        "synth_lead": {"active": True, "volume": 0.35, "note_duration": 1.0},
        "sub_pulse": {"active": True, "volume": 0.75},
        "noise_burst": {"active": True, "density": 0.35},
        "bytebeat": {"active": False},
        "feedback": {"active": True, "volume": 0.15, "iterations": 3},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.2},
    },
    "tension_frustrated": {
        "energy": 0.85,
        "bass_drone": {"active": True, "volume": 1.1},
        "clicks": {"active": True, "density": 1.4, "pan_spread": 0.9},
        "fm_bass": {"active": True, "volume": 0.65},
        "arpeggio": {"active": True, "speed": 0.1, "volume": 0.9},
        "glitch": {"active": True, "density": 0.85},
        "kick": {"active": True, "volume": 0.7},
        "hi_hat": {"active": True, "volume": 0.4},
        "acid_bass": {"active": True, "volume": 0.65, "sweep_dir": "down"},
        "sub_pulse": {"active": True, "volume": 0.9},
        "stutter_gate": {"active": True, "divisions": 16, "blend": 0.4},
        "bytebeat": {"active": True, "volume": 0.25, "formula": "industrial"},
        "feedback": {"active": True, "volume": 0.3, "iterations": 6},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "tension_peak": {
        "energy": 0.95,
        "bass_drone": {"active": True, "volume": 1.2},
        "clicks": {"active": True, "density": 1.8, "pan_spread": 1.0},
        "fm_bass": {"active": True, "volume": 0.7},
        "arpeggio": {"active": True, "speed": 0.1, "volume": 1.0},
        "glitch": {"active": True, "density": 1.0},
        "noise_sweep": {"active": True, "direction": "up", "speed": 0.3},
        "kick": {"active": True, "volume": 0.8},
        "hi_hat": {"active": True, "volume": 0.45},
        "acid_bass": {"active": True, "volume": 0.7, "sweep_dir": "down"},
        "sub_pulse": {"active": True, "volume": 1.0},
        "stutter_gate": {"active": True, "divisions": 16, "blend": 0.5},
        "noise_burst": {"active": True, "density": 0.6},
        "bytebeat": {"active": True, "volume": 0.3, "formula": "chaos"},
        "feedback": {"active": True, "volume": 0.35, "iterations": 8},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    # === 각성 계열: 에너지 상승, 해방 ===
    "awakening_spark": {
        "energy": 0.8,
        "bass_drone": {"active": True, "volume": 0.95},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.5},
        "fm_bass": {"active": True, "volume": 0.7},
        "arpeggio": {"active": True, "speed": 0.25, "volume": 0.45},
        "glitch": {"active": True, "density": 0.15},
        "kick": {"active": True, "volume": 0.45},
        "hi_hat": {"active": True, "volume": 0.25},
        "synth_lead": {"active": True, "volume": 0.4, "note_duration": 0.6},
        "sub_pulse": {"active": True, "volume": 0.6},
        "metallic_hit": {"active": True, "volume": 0.25, "density": 0.2},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.25, "duty": 0.125},
        "chiptune_drum": {"active": True, "volume": 0.2},
    },
    "awakening_climax": {
        "energy": 1.0,
        "bass_drone": {"active": True, "volume": 1.2},
        "clicks": {"active": True, "density": 0.5, "pan_spread": 0.6},
        "fm_bass": {"active": True, "volume": 0.8},
        "arpeggio": {"active": True, "speed": 0.18, "volume": 0.6},
        "glitch": {"active": True, "density": 0.25},
        "kick": {"active": True, "volume": 0.75},
        "hi_hat": {"active": True, "volume": 0.4},
        "synth_lead": {"active": True, "volume": 0.5, "note_duration": 0.5},
        "acid_bass": {"active": True, "volume": 0.5, "sweep_dir": "up"},
        "sub_pulse": {"active": True, "volume": 0.7},
        "stutter_gate": {"active": True, "divisions": 8, "blend": 0.25},
        "bytebeat": {"active": True, "volume": 0.15, "formula": "cascade"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.3, "duty": 0.25},
        "chiptune_drum": {"active": True, "volume": 0.25},
    },
    "awakening": {
        "energy": 0.85,
        "bass_drone": {"active": True, "volume": 1.0},
        "clicks": {"active": True, "density": 0.3, "pan_spread": 0.4},
        "fm_bass": {"active": True, "volume": 0.7},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.35},
        "glitch": {"active": True, "density": 0.12},
        "kick": {"active": True, "volume": 0.5},
        "hi_hat": {"active": True, "volume": 0.25},
        "synth_lead": {"active": True, "volume": 0.45, "note_duration": 0.7},
        "sub_pulse": {"active": True, "volume": 0.6},
        "metallic_hit": {"active": True, "volume": 0.2, "density": 0.15},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.2, "duty": 0.5},
        "chiptune_drum": {"active": True, "volume": 0.2},
    },
    # === 희망/초월 계열 ===
    "hopeful": {
        "energy": 0.7,
        "bass_drone": {"active": True, "volume": 0.85},
        "clicks": {"active": True, "density": 0.2, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.6},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.4},
        "glitch": {"active": False},
        "kick": {"active": True, "volume": 0.4},
        "hi_hat": {"active": True, "volume": 0.2},
        "synth_lead": {"active": True, "volume": 0.4, "note_duration": 0.9},
        "sub_pulse": {"active": True, "volume": 0.45},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": True, "volume": 0.2, "duty": 0.5},
        "chiptune_drum": {"active": False},
    },
    "transcendent": {
        "energy": 0.65,
        "bass_drone": {"active": True, "volume": 0.75},
        "clicks": {"active": True, "density": 0.1, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.55},
        "arpeggio": {"active": True, "speed": 0.35, "volume": 0.25},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "synth_lead": {"active": True, "volume": 0.35, "note_duration": 1.2},
        "sub_pulse": {"active": True, "volume": 0.4},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    "transcendent_open": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.7},
        "clicks": {"active": True, "density": 0.08, "pan_spread": 0.3},
        "fm_bass": {"active": True, "volume": 0.5},
        "arpeggio": {"active": True, "speed": 0.4, "volume": 0.2},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "synth_lead": {"active": True, "volume": 0.3, "note_duration": 1.5},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
    # === 페이드 아웃 ===
    "fade": {
        "energy": 0.1,
        "bass_drone": {"active": True, "volume": 0.25},
        "clicks": {"active": False},
        "fm_bass": {"active": True, "volume": 0.15},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "kick": {"active": False},
        "hi_hat": {"active": False},
        "bytebeat": {"active": False},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
    },
}


# ============================================================
# 장르 프리셋 v5 — Raw Synthesis + Genre Overhaul
# techno(유지) / bytebeat(수학공식) / algorave(불규칙리듬) / harsh_noise(피드백) / chiptune(8bit)
# ============================================================

GENRE_PRESETS = {
    "techno": {
        "bpm_override": 128,
        "volume_scale": {
            "kick": 1.5, "hi_hat": 1.3, "acid_bass": 1.4,
            "bass_drone": 1.2, "arpeggio": 0.8, "synth_lead": 0.5,
            "sub_pulse": 1.3, "stutter_gate": 1.2,
        },
        "force_active": ["kick", "hi_hat", "sub_pulse"],
        "force_inactive": [],
        "synthesis_overrides": {},
        "description": "4-on-the-floor, 강렬한 킥, 하이햇 드라이브",
    },
    "bytebeat": {
        "bpm_override": 100,
        "volume_scale": {
            "bytebeat": 1.5, "arpeggio": 0.6, "bass_drone": 0.5,
            "kick": 0.4, "hi_hat": 0.3, "glitch": 1.2, "clicks": 1.3,
            "fm_bass": 0.4, "sub_pulse": 0.5,
        },
        "force_active": ["bytebeat", "clicks"],
        "force_inactive": ["acid_bass", "synth_lead", "noise_sweep"],
        "synthesis_overrides": {
            "bit_depth": 8,
        },
        "description": "Viznut 수학 공식 오디오, 8bit 양자화, 비트연산 멜로디",
    },
    "algorave": {
        "bpm_override": 140,
        "volume_scale": {
            "kick": 1.3, "hi_hat": 1.2, "glitch": 1.5, "arpeggio": 1.4,
            "noise_burst": 1.3, "metallic_hit": 1.2, "stutter_gate": 1.3,
            "clicks": 1.3, "bass_drone": 0.8, "fm_bass": 0.7,
        },
        "force_active": ["kick", "hi_hat", "glitch", "arpeggio"],
        "force_inactive": [],
        "synthesis_overrides": {
            "rhythm_mode": "euclidean",
        },
        "description": "빠른 BPM, 유클리드 리듬, 브레이크비트, 글리치 패턴",
    },
    "harsh_noise": {
        "bpm_override": 80,
        "volume_scale": {
            "feedback": 1.8, "glitch": 1.5, "noise_burst": 2.0,
            "bass_drone": 1.3, "metallic_hit": 1.5,
            "kick": 0.5, "hi_hat": 0.3, "arpeggio": 0.3,
            "fm_bass": 0.6, "sub_pulse": 0.8,
        },
        "force_active": ["feedback", "glitch", "noise_burst", "bass_drone"],
        "force_inactive": ["synth_lead"],
        "synthesis_overrides": {
            "wavefold_master": 2,
        },
        "description": "피드백 루프, 웨이브폴딩, 카오틱 노이즈, 산업적 텍스처",
    },
    "chiptune": {
        "bpm_override": 120,
        "volume_scale": {
            "chiptune_lead": 1.5, "arpeggio": 1.3, "chiptune_drum": 1.4,
            "bass_drone": 0.4, "fm_bass": 0.5,
            "kick": 0.3, "hi_hat": 0.3, "glitch": 0.5,
            "clicks": 1.0, "sub_pulse": 0.4,
        },
        "force_active": ["chiptune_lead", "chiptune_drum", "arpeggio"],
        "force_inactive": ["acid_bass", "noise_sweep", "synth_lead"],
        "synthesis_overrides": {
            "bit_depth": 4,
        },
        "description": "NES/Game Boy 스퀘어파, 4bit 양자화, 펄스 아르페지오",
    },
}


def _get_transition(prev_emotion, curr_emotion):
    """두 감정 사이의 전환 방식 결정"""
    dramatic_pairs = {
        ("tension", "awakening"), ("tension_frustrated", "awakening_climax"),
        ("tension_peak", "awakening"), ("somber_analytical", "awakening_climax"),
        ("tension", "awakening_climax"), ("tension_reveal", "awakening_spark"),
        ("tension_transformative", "awakening"), ("tension_redefine", "awakening_climax"),
    }
    pair = (prev_emotion, curr_emotion)
    if pair in dramatic_pairs:
        return {"type": "silence_break", "silence_sec": 0.3,
                "then": "fade_in", "duration_sec": 1.5}

    if prev_emotion.split("_")[0] == curr_emotion.split("_")[0]:
        return {"type": "crossfade", "duration_sec": 1.0}

    return {"type": "crossfade", "duration_sec": 2.0}


def generate_music_script(visual_script: dict, narration_timing: dict = None,
                          genre: str = None) -> dict:
    """
    visual_script.json + narration_timing.json → music_script.json
    대본의 씬별 감정을 읽어서 악기 배치를 자동 결정.
    genre: techno, bytebeat, algorave, harsh_noise, chiptune (선택사항)
    """
    scenes = visual_script.get("scenes", [])
    title = visual_script.get("title", "ENOMETA")

    total_duration = max(s["end_sec"] for s in scenes) if scenes else 60
    total_duration = total_duration + 5

    # 장르 프리셋 적용
    genre_preset = GENRE_PRESETS.get(genre) if genre else None
    base_bpm = genre_preset["bpm_override"] if genre_preset else 80

    sections = []
    prev_emotion = None

    for i, scene in enumerate(scenes):
        emotion_key = scene.get("emotion", "neutral")

        if emotion_key in EMOTION_MAP:
            mapping = EMOTION_MAP[emotion_key]
        else:
            base = emotion_key.split("_")[0]
            mapping = EMOTION_MAP.get(base, EMOTION_MAP["neutral"])

        if prev_emotion:
            transition = _get_transition(prev_emotion, emotion_key)
        elif i == 0:
            transition = {"type": "fade_in", "duration_sec": 1.0}
        else:
            transition = {"type": "crossfade", "duration_sec": 1.0}

        energy = mapping.get("energy", 0.3)
        effects = {
            "reverb_decay": 0.3 + energy * 0.3,
            "filter_cutoff": int(200 + energy * 3000),
            "stereo_width": 0.3 + energy * 0.5,
        }

        instruments = {}
        for key in ["bass_drone", "clicks", "fm_bass", "arpeggio", "glitch",
                     "noise_sweep", "sub_pulse", "noise_burst", "metallic_hit",
                     "kick", "hi_hat", "synth_lead", "acid_bass",
                     "stutter_gate", "tape_stop",
                     "bytebeat", "feedback", "chiptune_lead", "chiptune_drum"]:
            if key in mapping:
                instruments[key] = dict(mapping[key])

        # 장르 프리셋으로 볼륨/활성 상태 조정
        if genre_preset:
            vol_scale = genre_preset.get("volume_scale", {})
            for inst_key, scale in vol_scale.items():
                if inst_key in instruments and "volume" in instruments[inst_key]:
                    instruments[inst_key]["volume"] *= scale
            for inst_key in genre_preset.get("force_active", []):
                if inst_key in instruments:
                    instruments[inst_key]["active"] = True
                else:
                    instruments[inst_key] = {"active": True, "volume": 0.3}
            for inst_key in genre_preset.get("force_inactive", []):
                if inst_key in instruments:
                    instruments[inst_key]["active"] = False

        section = {
            "id": scene.get("id", f"sec_{i+1:02d}"),
            "text": scene.get("sentence", ""),
            "start_sec": scene["start_sec"],
            "end_sec": scene["end_sec"],
            "emotion": emotion_key,
            "energy": energy,
            "instruments": instruments,
            "effects": effects,
            "transition_in": transition,
        }
        sections.append(section)
        prev_emotion = emotion_key

    if scenes:
        last_end = scenes[-1]["end_sec"]
        outro = {
            "id": "outro",
            "text": "",
            "start_sec": last_end,
            "end_sec": total_duration,
            "emotion": "fade",
            "energy": 0.1,
            "instruments": {
                "bass_drone": {"active": True, "volume": 0.25},
                "fm_bass": {"active": True, "volume": 0.15},
            },
            "effects": {
                "reverb_decay": 0.7,
                "filter_cutoff": 500,
                "stereo_width": 0.3,
            },
            "transition_in": {"type": "crossfade", "duration_sec": 3.0},
        }
        sections.append(outro)

    genre_label = genre if genre else "default"
    synthesis_overrides = genre_preset.get("synthesis_overrides", {}) if genre_preset else {}
    music_script = {
        "metadata": {
            "title": title,
            "duration": total_duration,
            "sample_rate": SAMPLE_RATE,
            "key": "E_minor",
            "base_bpm": base_bpm,
            "genre": genre_label,
            "synthesis_overrides": synthesis_overrides,
        },
        "palette": {
            "bass_freq": 82.4,
            "pad_root": 329.6,
            "pad_fifth": 493.9,
            "arp_root": 220,
            "arp_pattern": [1, 1.25, 1.5, 2, 1.5, 1.25],
        },
        "sections": sections,
    }

    return music_script


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ENOMETA Generative Music Engine v5")
    parser.add_argument("input", help="music_script.json 또는 --from-visual 모드")
    parser.add_argument("extra", nargs="*", help="추가 인자")
    parser.add_argument("--from-visual", action="store_true", dest="from_visual",
                        help="visual_script.json에서 자동 생성")
    parser.add_argument("--genre", choices=list(GENRE_PRESETS.keys()),
                        help=f"장르 프리셋: {', '.join(GENRE_PRESETS.keys())}")
    args, unknown = parser.parse_known_args()

    import os

    # --from-visual 모드 감지 (argparse + legacy 방식 모두 지원)
    if args.from_visual or args.input == "--from-visual":
        if args.input == "--from-visual":
            # legacy 방식: python engine.py --from-visual visual.json [timing.json] [out.wav]
            remaining = args.extra
            visual_path = remaining[0] if remaining else None
            remaining = remaining[1:] if len(remaining) > 1 else []
        else:
            visual_path = args.input
            remaining = args.extra

        if not visual_path:
            print("Error: visual_script.json 경로가 필요합니다")
            sys.exit(1)

        narration_path = None
        output_path = None
        for r in remaining:
            if r.endswith(".wav"):
                output_path = r
            elif r.endswith(".json"):
                narration_path = r

        if not output_path:
            output_path = os.path.join(os.path.dirname(visual_path), "bgm.wav")

        # --genre 플래그 체크 (unknown args에서)
        genre = args.genre
        if not genre:
            for i, u in enumerate(unknown):
                if u == "--genre" and i + 1 < len(unknown):
                    genre = unknown[i + 1]

        with open(visual_path, 'r', encoding='utf-8') as f:
            visual_script = json.load(f)

        narration_timing = None
        if narration_path:
            with open(narration_path, 'r', encoding='utf-8') as f:
                narration_timing = json.load(f)

        print("=== ENOMETA Music Script Generator ===")
        print(f"Visual script: {visual_path}")
        if genre:
            print(f"Genre: {genre} - {GENRE_PRESETS[genre]['description']}")
        music_script = generate_music_script(visual_script, narration_timing, genre=genre)

        ms_path = os.path.join(os.path.dirname(output_path), "music_script.json")
        with open(ms_path, 'w', encoding='utf-8') as f:
            json.dump(music_script, f, ensure_ascii=False, indent=2)
        print(f"Music script saved: {ms_path}")

    else:
        script_path = args.input
        output_path = args.extra[0] if args.extra else "bgm.wav"

        with open(script_path, 'r', encoding='utf-8') as f:
            music_script = json.load(f)

    print()
    genre_label = music_script['metadata'].get('genre', 'default')
    print(f"=== ENOMETA Generative Music Engine v5 ===")
    print(f"Duration: {music_script['metadata']['duration']:.1f}s")
    print(f"Sections: {len(music_script['sections'])}")
    print(f"Key: {music_script['metadata'].get('key', 'E_minor')}")
    print(f"BPM: {music_script['metadata'].get('base_bpm', 80)}")
    print(f"Genre: {genre_label}")
    print()

    engine = EnometaMusicEngine(music_script)
    audio = engine.generate()

    wavfile.write(output_path, SAMPLE_RATE, audio)
    print()
    print(f"Output: {output_path}")
    print(f"Format: {SAMPLE_RATE}Hz, 16bit, Stereo")
    print("Done!")


if __name__ == "__main__":
    main()
