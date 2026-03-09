"""
ENOMETA Generative Music Engine v11 — Pattern Engine
대본의 감정을 읽고 1곡의 연속적 음악을 생성하는 엔진.
GPU 불필요. numpy + scipy만으로 동작.

v9 변경사항 (Matrix 스타일 확장):
- sawtooth() + sawtooth_distorted(): 쏘우파 원초적 전자음 파형 추가
- saw_sequence(): 게이트된 쏘우파 시퀀서 — '뚜두두 뚜두 뚜 뚜 뚜~' 패턴
- _render_continuous_saw_sequence(): enometa 분기의 핵심 리듬 레이어
- enometa generate() 분기: rhythm + arpeggio + saw_sequence 모두 활성화 (10레이어)
- BPM 60 → 120: Matrix 스타일 강렬한 리듬
- kick/hihat volume 0.1~0.2 → 0.5~0.8: 드럼 리듬 실체 복원
- random.seed(42) 제거: 에피소드 해시 기반 시드 (매번 다른 텍스처)
- SINE_MELODY_SEQUENCES: 하드코딩 220Hz → key_palette pad_root 기반 동적 생성
- EMOTION_MAP: tension/awakening 계열에 saw_sequence 활성화

v8 변경사항:
- 6장르 → enometa 단일 장르 통합
- TEXTURE_MODULES: 에피소드 간 텍스처 조합 다양화 시스템
- 마스터링 통합: tanh(1.5) + RMS -6dB (enometa 전용)
- EMOTION_MAP: 고에너지 상태에 feedback 텍스처 활성화

사용법:
  python enometa_music_engine.py --script-data <script_data.json> [--visual-script <visual_script.json>] [output.wav]
"""

import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter, butter, sosfilt
import random
import math

SAMPLE_RATE = 44100
# v9: 고정 시드 제거 — 에피소드마다 다른 랜덤 패턴 생성
# (generate_music_script()에서 episode 해시 기반 시드 설정)


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


# ── v14: 고급 합성/이펙트 유틸리티 ──────────────────────────

def resonant_lowpass(audio, cutoff_hz, sr=SAMPLE_RATE, order=4):
    """레조넌트 로우패스 필터 (sosfilt 기반, 수치 안정)."""
    nyq = sr / 2
    norm = min(max(cutoff_hz / nyq, 0.001), 0.99)
    sos = butter(order, norm, btype='low', output='sos')
    return sosfilt(sos, audio)


def resonant_bandpass(audio, low_hz, high_hz, sr=SAMPLE_RATE, order=2):
    """밴드패스 필터 (sosfilt 기반)."""
    nyq = sr / 2
    lo = min(max(low_hz / nyq, 0.001), 0.99)
    hi = min(max(high_hz / nyq, lo + 0.001), 0.99)
    sos = butter(order, [lo, hi], btype='band', output='sos')
    return sosfilt(sos, audio)


def make_wavetable(harmonics: dict, size: int = 2048) -> np.ndarray:
    """배음 딕셔너리 → 1주기 웨이브테이블.
    harmonics: {배음번호: 진폭}  예: {1: 1.0, 3: 0.5, 5: 0.2}
    """
    wt = np.zeros(size)
    t = np.linspace(0, 2 * np.pi, size, endpoint=False)
    for h, amp in harmonics.items():
        wt += amp * np.sin(int(h) * t)
    peak = np.max(np.abs(wt))
    return wt / peak if peak > 0 else wt


def wavetable_osc(wavetable: np.ndarray, freq: float, duration: float,
                  sr: int = SAMPLE_RATE) -> np.ndarray:
    """웨이브테이블 오실레이터 (벡터화 선형 보간)."""
    n = int(sr * duration)
    wt_len = len(wavetable)
    phase_inc = wt_len * freq / sr
    phase = np.cumsum(np.full(n, phase_inc)) % wt_len
    idx_int = phase.astype(int) % wt_len
    idx_frac = phase - phase.astype(int)
    return wavetable[idx_int] * (1 - idx_frac) + wavetable[(idx_int + 1) % wt_len] * idx_frac


def chorus(audio, sr=SAMPLE_RATE, lfo_rate=1.5, delay_ms=20.0, depth_ms=3.0):
    """코러스 이펙트 (벡터화). LFO 변조 딜레이 → 디튜닝 풍부함."""
    n = len(audio)
    t = np.arange(n) / sr
    # LFO → 딜레이 변조 (샘플 단위)
    lfo = np.sin(2 * np.pi * lfo_rate * t)
    delay_samples = (delay_ms + depth_ms * lfo) * sr / 1000.0
    # 읽기 인덱스 (보간)
    read_idx = np.arange(n) - delay_samples
    read_idx = np.clip(read_idx, 0, n - 1)
    idx_int = read_idx.astype(int)
    idx_frac = read_idx - idx_int
    idx_next = np.minimum(idx_int + 1, n - 1)
    delayed = audio[idx_int] * (1 - idx_frac) + audio[idx_next] * idx_frac
    return audio * 0.6 + delayed * 0.4


def sidechain_pump(main, kick_env, depth=0.5, release_ms=80, sr=SAMPLE_RATE):
    """사이드체인 펌핑: 킥 엔벨로프로 메인 볼륨 덕킹.
    kick_env: 킥 타이밍의 진폭 엔벨로프 (같은 길이).
    depth: 0~1 (1이면 킥 때 완전 무음).
    """
    if len(kick_env) != len(main):
        # 길이 맞춤
        kick_env = np.interp(np.linspace(0, 1, len(main)),
                             np.linspace(0, 1, len(kick_env)), kick_env)
    # 킥 엔벨로프 → 스무딩 (release)
    release_samples = int(sr * release_ms / 1000)
    smoothed = np.zeros_like(kick_env)
    env_val = 0.0
    release_coeff = np.exp(-1.0 / max(release_samples, 1))
    for i in range(len(kick_env)):
        if kick_env[i] > env_val:
            env_val = kick_env[i]
        else:
            env_val *= release_coeff
        smoothed[i] = env_val
    # 덕킹 게인: 킥 활성 → (1-depth), 비활성 → 1.0
    gain = 1.0 - depth * smoothed / (np.max(smoothed) + 1e-10)
    return main * gain


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

def deep_bass_drone(freq, duration, sr=SAMPLE_RATE, detune=0.002):
    """딥 베이스 드론 v14 — 동적 디튜닝 (시드 기반)
    detune: 0.001~0.008 — 클수록 두꺼운 유니즌
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * 0.7
    wave += np.sin(2 * np.pi * (freq * (1 + detune)) * t) * 0.4
    wave += np.sin(2 * np.pi * (freq * (1 - detune * 0.5)) * t) * 0.25
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


def fm_bass(freq, duration, mod_ratio=2.0, mod_depth=300, sr=SAMPLE_RATE, detune=0.002):
    """FM 합성 베이스 v14 — 동적 mod_ratio + 디튠 레이어
    mod_ratio: 시드 기반 (1.5~3.5), detune: 시드 기반 (0.001~0.008)
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    modulator = np.sin(2 * np.pi * freq * mod_ratio * t)
    depth_env = mod_depth * np.exp(-t * 2.5)
    phase = 2 * np.pi * freq * t + depth_env * modulator
    wave = np.sin(phase) * 0.5
    # 서브 레이어
    wave += np.sin(2 * np.pi * freq * 0.5 * t) * 0.3
    # v14: 디튠 레이어 (두꺼운 음색)
    phase2 = 2 * np.pi * freq * (1 + detune) * t + depth_env * 0.7 * modulator
    wave += np.sin(phase2) * 0.2
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


def bytebeat(formula_id="sierpinski", duration=1.0, sr=SAMPLE_RATE, return_raw=False):
    """Bytebeat — 수학 공식으로 원시 파형 생성 (Viznut 방식)

    return_raw=True이면 (audio, raw_values) 튜플 반환 (클리핑 전 원본 보존)
    """
    # 8000Hz로 생성 (lo-fi 유지) → 44100 리샘플
    bytebeat_sr = 8000
    num_samples = int(bytebeat_sr * duration)
    formula = BYTEBEAT_FORMULAS.get(formula_id, BYTEBEAT_FORMULAS["sierpinski"])

    t_arr = np.arange(num_samples, dtype=np.int64)
    # 벡터 연산으로 공식 적용
    try:
        raw_unmasked = formula(t_arr)  # 클리핑 전 원본
        raw = raw_unmasked & 0xFF  # uint8 범위로 마스킹
    except Exception:
        raw_unmasked = t_arr & (t_arr >> 8)
        raw = raw_unmasked & 0xFF  # fallback: sierpinski

    # uint8 [0,255] → float [-1,1]
    audio = (raw.astype(np.float64) - 128.0) / 128.0

    # 8000Hz → 44100Hz 리샘플 (nearest neighbor로 lo-fi 유지)
    target_samples = int(sr * duration)
    indices = np.linspace(0, len(audio) - 1, target_samples).astype(int)
    resampled = audio[indices]

    if return_raw:
        # 원본도 동일하게 리샘플
        raw_resampled = raw_unmasked[indices]
        return resampled * 0.4, raw_resampled
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


def arpeggio_sequence(base_freq, duration, pattern=None, speed=0.2, sr=SAMPLE_RATE,
                      bpm=0, division=4, apply_chorus=False, chorus_depth_ms=2.5):
    """시퀀서 아르페지오 v19 — BPM 동기 + division 변주 + 코러스 옵션
    bpm>0이면 speed를 BPM 기반으로 자동 동기화.
    division: 2=8분음표, 3=3연음, 4=16분음표
    """
    if pattern is None:
        pattern = [1, 1.25, 1.5, 2, 1.5, 1.25]
    total_samples = int(sr * duration)

    # v19: BPM 동기화 (division 기반)
    if bpm > 0:
        speed = 60.0 / bpm / division  # division에 따른 노트 길이

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
    # v14: 코러스 적용
    if apply_chorus:
        result = chorus(result, sr=sr, depth_ms=chorus_depth_ms)
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

def kick_drum(freq=55, sr=SAMPLE_RATE, character=0):
    """킥 드럼 v14 — 3종 캐릭터 (시드 기반 선택)
    character: 0=tight (짧고 단단), 1=boomy (길고 울림), 2=punchy (어택 강조)
    """
    if character == 1:  # boomy: 길고 울림
        duration = 0.45
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        pitch_env = freq * (1 + 4 * np.exp(-t * 20))  # 느린 피치 스윕
        phase = np.cumsum(2 * np.pi * pitch_env / sr)
        wave = np.sin(phase) * 0.85
        body_env = np.exp(-t * 6)  # 느린 감쇠 → 울림
        wave *= body_env
        wave += np.sin(2 * np.pi * freq * 0.5 * t) * np.exp(-t * 3) * 0.5  # 서브 강조
        click = noise(0.004, sr) * np.exp(-np.linspace(0, 0.004, int(sr * 0.004)) * 600)
        click *= 0.15
        wave[:len(click)] += click
    elif character == 2:  # punchy: 어택 강조
        duration = 0.3
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        pitch_env = freq * (1 + 10 * np.exp(-t * 50))  # 빠르고 넓은 피치 스윕
        phase = np.cumsum(2 * np.pi * pitch_env / sr)
        wave = np.sin(phase) * 0.95
        body_env = np.exp(-t * 14)  # 빠른 감쇠
        wave *= body_env
        wave += np.sin(2 * np.pi * freq * t) * np.exp(-t * 8) * 0.3
        # 강한 클릭 어택
        click = noise(0.008, sr) * np.exp(-np.linspace(0, 0.008, int(sr * 0.008)) * 500)
        click *= 0.4
        wave[:len(click)] += click
    else:  # tight (기본): 짧고 단단
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


def snare_drum(freq=200, sr=SAMPLE_RATE):
    """스네어 드럼 v12 — 짧고 건조한 노이즈 버스트. raw 전자음악 스타일.
    촌스러운 톤 바디 제거, 순수 노이즈 히트 + 어택 클릭만.
    """
    duration = 0.08  # 0.18 → 0.08 (훨씬 짧게)
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 노이즈 히트: 빠르게 감쇠하는 짧은 버스트
    n = noise(duration, sr) * np.exp(-t * 45) * 0.35
    # 어택 클릭 (디지털 느낌)
    click_dur = 0.002
    click_samples = int(sr * click_dur)
    click = noise(click_dur, sr) * np.exp(-np.linspace(0, click_dur, click_samples) * 1500)
    n[:click_samples] += click * 0.25
    return n


def downbeat_crash(sr=SAMPLE_RATE):
    """v16: 신스 크래시 심벌 — 노이즈 → 레조네이터 뱅크 + 스틱 어택.
    Sound on Sound / mcld.co.uk cymbal synthesis 기법 기반.
    매 4~8마디 첫박 배치용 (0.8초).
    """
    duration = 0.8
    samples = int(sr * duration)
    t = np.linspace(0, duration, samples, endpoint=False)

    # 드라이버 1: LP 필터드 노이즈 (메인 바디)
    n = noise(duration, sr)
    # LP 엔벨로프: 빠른 어택 → 느린 감쇠
    lp_env = np.exp(-t / 0.4) * 0.8
    body = n * lp_env

    # 드라이버 2: HP 필터드 노이즈 (심벌 쉬머)
    shimmer = n.copy()
    # 간단한 1차 HP: 차분 반복 2회
    for _ in range(2):
        shimmer[1:] = shimmer[1:] - shimmer[:-1] * 0.7
    shimmer *= np.exp(-t / 0.3) * 0.4

    # 드라이버 3: 스틱 임팩트 (1ms 클릭)
    thwack = np.zeros(samples)
    click_len = max(1, int(sr * 0.001))
    thwack[:click_len] = noise(0.001, sr)[:click_len] * 1.5

    # 레조네이터 뱅크: 지수 분포 300~16kHz, 16개 (가벼운 버전)
    n_res = 16
    freqs = np.exp(np.linspace(np.log(300), np.log(16000), n_res))
    driver = body + shimmer + thwack
    resonated = np.zeros(samples)
    for freq in freqs:
        # 고주파일수록 빠른 감쇠
        decay = 0.5 / (1 + freq / 3000)
        damping = np.exp(-t / decay)
        resonated += np.sin(2 * np.pi * freq * t) * damping

    # 레조네이터 * 드라이버 (링 모듈레이션 효과)
    out = resonated / n_res * driver + body * 0.5 + thwack
    # 노멀라이즈
    peak = np.max(np.abs(out))
    if peak > 0:
        out = out / peak * 0.6
    return out


def downbeat_noise_hit(sr=SAMPLE_RATE):
    """v16: 디지털 노이즈 임팩트 — enometa 시그니처.
    날카로운 노이즈 버스트 + 중역대 레조넌스 + 빠른 감쇠.
    매 마디 첫박 배치용 (0.15초).
    """
    duration = 0.15
    samples = int(sr * duration)
    t = np.linspace(0, duration, samples, endpoint=False)

    # 날카로운 노이즈 버스트
    n = noise(duration, sr) * np.exp(-t * 30) * 0.7
    # 중역대 강조 (밴드패스 근사: HP + LP)
    n[1:] = n[1:] - n[:-1] * 0.4  # HP
    # 사인 레이어: 임팩트감을 위한 짧은 톤
    tone = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 50) * 0.3
    # 스틱 클릭
    click_len = max(1, int(sr * 0.0005))
    click = np.zeros(samples)
    click[:click_len] = noise(0.0005, sr)[:click_len] * 0.5

    out = n + tone + click
    peak = np.max(np.abs(out))
    if peak > 0:
        out = out / peak * 0.5
    return out


def downbeat_reverse_crash(sr=SAMPLE_RATE):
    """v16: 리버스 크래시 → 포워드 히트.
    크래시를 뒤집어서 당김 효과 + 끝에 정방향 노이즈 히트.
    매 8~16마디 첫박 0.5초 전에 시작, 첫박에서 피크.
    """
    # 포워드 크래시 생성 후 뒤집기
    fwd = downbeat_crash(sr)
    rev = fwd[::-1].copy()
    # 뒤집힌 크래시: 점점 커지는 효과 (0.8초)
    # 끝부분 살짝 자르고 페이드
    rev_len = len(rev)
    fade = np.linspace(0.0, 1.0, rev_len) ** 2  # 제곱 커브로 후반부 강조
    rev *= fade * 0.7
    return rev


def downbeat_sine_pop(sr=SAMPLE_RATE):
    """v16: Ikeda 스타일 사인 팝 — 초단 사인 버스트 (1~3ms).
    다양한 주파수의 극초단 사인파로 디지털 텍스처. 매 2마디 배치용.
    """
    duration = 0.005
    samples = int(sr * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    # 랜덤하지 않은 결정론적 주파수: 2kHz (날카로운 클릭감)
    freq = 2000.0
    pop = np.sin(2 * np.pi * freq * t)
    # 극초단 엔벨로프: 1ms 어택 → 즉시 감쇠
    env = np.exp(-t * 800)
    pop *= env * 0.7
    # 비선형 클리핑으로 Ikeda 특유의 날카로움
    pop = np.tanh(pop * 3.0) * 0.5
    return pop


def downbeat_sub_boom(sr=SAMPLE_RATE):
    """v16: 서브 붐 — 저주파 사인 스윕 (80→40Hz) + 빠른 감쇠.
    4마디 경계에서 무게감 추가. 킥과 레이어링.
    """
    duration = 0.25
    samples = int(sr * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    # 피치 스윕: 80Hz → 40Hz (exponential)
    freq = 80.0 * np.exp(-t * 3.0)  # 빠른 하강
    phase = np.cumsum(2 * np.pi * freq / sr)
    boom = np.sin(phase)
    # 엔벨로프: 즉시 어택 → 0.2초 감쇠
    env = np.exp(-t * 12) * 0.8
    boom *= env
    # 서브 강조: 약간의 하모닉 디스토션
    boom = np.tanh(boom * 2.0) * 0.6
    return boom


def downbeat_open_hat(sr=SAMPLE_RATE):
    """v16: 오픈 하이햇 — 긴 감쇠 노이즈 + 메탈릭 레조넌스.
    2마디 또는 4마디 첫박에서 그루브 강조용 (0.3초).
    """
    duration = 0.3
    samples = int(sr * duration)
    t = np.linspace(0, duration, samples, endpoint=False)
    # 메탈릭 노이즈 (HP 필터링)
    n = noise(duration, sr)
    # 2차 HP: 고주파 강조
    for _ in range(3):
        n[1:] = n[1:] - n[:-1] * 0.6
    # 메탈릭 레조넌스: 6kHz + 10kHz
    res1 = np.sin(2 * np.pi * 6200 * t) * np.exp(-t * 8)
    res2 = np.sin(2 * np.pi * 10500 * t) * np.exp(-t * 10)
    # 엔벨로프: 빠른 어택, 중간 감쇠
    env = np.exp(-t * 6)
    out = (n * 0.5 + res1 * 0.3 + res2 * 0.2) * env
    peak = np.max(np.abs(out))
    if peak > 0:
        out = out / peak * 0.45
    return out


def downbeat_ping_pong(sr=SAMPLE_RATE):
    """v16: Ikeda 스타일 핑퐁 트랜지언트 — L/R 교대 클릭.
    2~5ms 딜레이로 스테레오 공간감. 반환: (L, R) 튜플.
    매 마디 배치, noise_hit와 교대 사용.
    """
    duration = 0.02
    samples = int(sr * duration)
    # 극초단 클릭 (0.5ms)
    click_len = max(1, int(sr * 0.0005))
    click = noise(0.001, sr)[:click_len] * 0.6
    # 딜레이: 3ms
    delay_samples = int(sr * 0.003)
    L = np.zeros(samples)
    R = np.zeros(samples)
    # L: 즉시
    L[:click_len] = click
    # R: 3ms 딜레이
    r_start = delay_samples
    r_end = min(r_start + click_len, samples)
    actual = r_end - r_start
    R[r_start:r_end] = click[:actual]
    # 두 번째 바운스: L 6ms
    l2_start = delay_samples * 2
    l2_end = min(l2_start + click_len, samples)
    actual2 = l2_end - l2_start
    if actual2 > 0:
        L[l2_start:l2_end] = click[:actual2] * 0.4  # 감쇠
    return L, R


# 하위 호환: 기존 코드에서 transition_impact 호출하는 곳
def transition_impact(sr=SAMPLE_RATE):
    """v16: downbeat_noise_hit으로 리다이렉트"""
    return downbeat_noise_hit(sr)


def synth_lead(freq, duration, sr=SAMPLE_RATE, wt=None, vibrato_depth=0.003, cutoff_hz=0):
    """신스 리드 v14 — 웨이브테이블 + 동적 비브라토 + LP 필터
    wt: 웨이브테이블 (None이면 기존 가산합성)
    vibrato_depth: 0.003~0.02 (시드/emotion 기반)
    cutoff_hz: LP 필터 컷오프 (0이면 미적용)
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    vib = 1 + vibrato_depth * np.sin(2 * np.pi * 6 * t)
    if wt is not None:
        wave = wavetable_osc(wt, freq * vib[0], duration, sr=sr)
        # 비브라토: 피치 LFO 근사 (전체 적용은 무거우므로 볼륨 트레몰로로 대체)
        wave *= (1 + vibrato_depth * 2 * np.sin(2 * np.pi * 5.5 * t[:len(wave)]))
    else:
        wave = np.zeros_like(t)
        for h in range(1, 5):
            wave += np.sin(2 * np.pi * freq * h * vib * t) / h * ((-1) ** (h + 1))
    wave *= 0.3
    wave = envelope(wave, attack=0.02, decay=0.08, sustain=0.6, release=0.15)
    if cutoff_hz > 0 and len(wave) > 20:
        wave = resonant_lowpass(wave, cutoff_hz, sr=sr, order=3)
    wave = reverb(wave, decay=0.2, delay_ms=60, repeats=1)
    return wave


def tape_delay(signal, delay_ms=300, feedback=0.6, sr=SAMPLE_RATE):
    """테이프 딜레이 — dub techno 핵심 이펙트.
    Basic Channel / Rhythm & Sound 스타일: 반복될수록 LP 필터로 고주파 손실,
    아날로그 테이프 특유의 따뜻한 감쇠.
    feedback: 0.0~0.95 (0.7 이상 = 긴 꼬리, dub 특유의 공간감)
    """
    delay_samples = int(sr * delay_ms / 1000)
    if delay_samples <= 0 or len(signal) == 0:
        return signal.copy()
    out = signal.copy().astype(np.float64)
    buf = np.zeros(delay_samples, dtype=np.float64)
    write_idx = 0
    # LP 필터 상태 (1차 IIR: 테이프 헤드 고주파 손실)
    lp_state = 0.0
    lp_coeff = 0.7  # 높을수록 더 어두운 반복
    for i in range(len(out)):
        delayed = buf[write_idx]
        # 1차 LP 필터: 반복마다 고주파 잘림
        lp_state = lp_coeff * lp_state + (1 - lp_coeff) * delayed
        out[i] += lp_state
        buf[write_idx] = out[i] * feedback
        write_idx = (write_idx + 1) % delay_samples
    # 노멀라이즈 (피크 초과 방지)
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out /= peak
    return out


def distorted_kick(freq=50, sr=SAMPLE_RATE, drive=3.0):
    """디스토션 킥 — industrial techno 킥.
    Perc / Ansome / Surgeon 레퍼런스: punchy 킥 + np.tanh waveshaping + 비트크러시.
    drive: 2.0~6.0 (높을수록 더 거친 디스토션)
    """
    # punchy 킥 기반
    base = kick_drum(freq, sr, character=2)
    # 웨이브쉐이핑 디스토션 (tanh 다단계)
    driven = np.tanh(base * drive)
    # 비트크러시: 8bit → 거친 디지털 텍스처
    bit_depth = 8
    levels = 2 ** bit_depth
    driven = np.round(driven * levels) / levels
    # 추가 드라이브로 펌핑감
    driven = np.tanh(driven * 1.5)
    # 클릭 어택 강화
    click_len = int(sr * 0.003)
    if click_len < len(driven):
        click = noise(0.003, sr)[:click_len] * 0.3
        driven[:click_len] += click
    # 노멀라이즈
    peak = np.max(np.abs(driven))
    if peak > 0:
        driven = driven / peak * 0.9
    return driven


def chord_stab(root_freq=130.8, duration=2.0, sr=SAMPLE_RATE):
    """코드 스탭 — dub techno 딥 코드.
    Basic Channel 스타일: 마이너 코드(root + m3 + 5th) + LP 필터 + 느린 감쇠.
    tape_delay()와 조합하면 dub techno 특유의 공간감 형성.
    """
    total_samples = int(sr * duration)
    t = np.linspace(0, duration, total_samples, endpoint=False)
    # 마이너 코드: root, minor 3rd (1.189), perfect 5th (1.498)
    ratios = [1.0, 1.189, 1.498]
    chord = np.zeros(total_samples)
    for ratio in ratios:
        freq = root_freq * ratio
        # 쏘우파 기반 (풍부한 하모닉)
        phase = (np.arange(total_samples) * freq / sr) % 1.0
        chord += (2.0 * phase - 1.0)
    chord /= len(ratios)
    # ADSR: 빠른 어택, 긴 릴리스 (패드 느낌)
    attack_s = int(sr * 0.01)
    decay_s = int(sr * 0.1)
    sustain_level = 0.6
    release_s = int(sr * max(0, duration - 0.5))
    env = np.ones(total_samples) * sustain_level
    # 어택
    if attack_s > 0:
        env[:attack_s] = np.linspace(0, 1, attack_s)
    # 디케이
    if decay_s > 0 and attack_s + decay_s < total_samples:
        env[attack_s:attack_s + decay_s] = np.linspace(1, sustain_level, decay_s)
    # 릴리스: 후반 50%에서 페이드아웃
    fade_start = total_samples // 2
    env[fade_start:] *= np.linspace(1, 0, total_samples - fade_start) ** 1.5
    chord *= env * 0.35
    # LP 필터: 따뜻한 톤 (dub 특유의 머핀 사운드)
    if len(chord) > 20:
        chord = resonant_lowpass(chord, 800, sr=sr, order=4)
    return chord


def rhodes_pad(root_freq=120.0, duration=2.0, sr=SAMPLE_RATE, brightness=0.5):
    """로즈 스타일 패드 — Deep House 코드 사운드.
    Minor 9 배음 구조 (root+m3+5th+m7+9th) additive 합성 + 느린 어택 + LP 필터.
    brightness: 0.0=어두운 따뜻함 / 1.0=밝은 샤이닝 (filter_cutoff 제어)
    """
    total_samples = int(sr * duration)
    if total_samples < 2:
        return np.zeros(total_samples)
    t = np.linspace(0, duration, total_samples, endpoint=False)
    # Minor 9 코드 배음: root, m3(×1.189), 5th(×1.498), m7(×1.782), 9th(×2.245)
    ratios     = [1.0,  1.189, 1.498, 1.782, 2.245]
    amplitudes = [1.0,  0.70,  0.50,  0.30,  0.15]
    pad = np.zeros(total_samples)
    for ratio, amp in zip(ratios, amplitudes):
        freq = root_freq * ratio
        # 미세 detune — 로즈 특유의 두꺼운 유니즌 느낌
        detune = 1.0 + (ratio - 1.0) * 0.0012
        pad += amp * np.sin(2 * np.pi * freq * detune * t)
    pad /= sum(amplitudes)
    # 느린 어택 엔벨로프 (250ms 페이드인 — 로즈 공명 느낌)
    attack_s   = min(int(sr * 0.25), total_samples)
    release_s  = min(int(sr * 0.50), total_samples)
    env = np.ones(total_samples)
    if attack_s > 0:
        env[:attack_s] = np.linspace(0, 1, attack_s)
    fade_start = max(total_samples - release_s, attack_s)
    if fade_start < total_samples:
        env[fade_start:] = np.linspace(1, 0, total_samples - fade_start)
    pad *= env * 0.40
    # LP 필터 — brightness로 밝기 제어 (400~2500 Hz)
    cutoff = 400 + brightness * 2100
    if len(pad) > 20:
        pad = resonant_lowpass(pad, cutoff, sr=sr, order=4)
    return pad


def soft_clip(signal, drive=2.0):
    """소프트 클리핑 디스토션"""
    driven = signal * drive
    return np.tanh(driven)


def sawtooth(freq, duration, sr=SAMPLE_RATE):
    """쏘우파(Sawtooth) — 모든 하모닉 포함, 전자음악 리드/베이스의 기본
    phase ramp: 0→1 반복, [-1, 1] 범위
    """
    total_samples = int(sr * duration)
    phase = (np.arange(total_samples) * freq / sr) % 1.0
    return (2.0 * phase - 1.0) * 0.4


def sawtooth_distorted(freq, duration, drive=3.0, sr=SAMPLE_RATE):
    """디스토션 쏘우파 — tanh 드라이브로 하드한 전자음
    drive 값이 클수록 더 거칠고 사각파에 가까워짐
    """
    wave = sawtooth(freq, duration, sr)
    return np.tanh(wave * drive) * 0.4


def saw_sequence(base_freq, duration, pattern_ratios, gate_div=8,
                 note_len_ratio=0.7, bpm=120, distort=True, sr=SAMPLE_RATE,
                 wt=None, drive=2.5, cutoff_hz=0):
    """v14 게이트된 시퀀서 — 웨이브테이블 + LP 필터 + 동적 drive.
    pattern_ratios: 음정 비율 리스트
    gate_div: 16(16분), 8(8분), 4(4분) 단위
    wt: 웨이브테이블 (None이면 기존 sawtooth 사용)
    drive: 디스토션 강도 (1.0=클린, 5.0=거침)
    cutoff_hz: LP 필터 컷오프 (0이면 필터 없음)
    """
    total_samples = int(sr * duration)
    result = np.zeros(total_samples)
    beat_sec = 60.0 / bpm
    note_sec = beat_sec * 4 / gate_div
    note_samples = int(sr * note_sec)
    sound_samples = max(int(note_samples * note_len_ratio), 1)

    pos = 0
    pat_idx = 0
    while pos < total_samples:
        ratio = pattern_ratios[pat_idx % len(pattern_ratios)]
        freq = base_freq * ratio
        actual_len = min(sound_samples, total_samples - pos)
        if actual_len > 4 and ratio > 0:
            # v14: 웨이브테이블 우선, 없으면 기존 sawtooth
            if wt is not None:
                note = wavetable_osc(wt, freq, actual_len / sr, sr=sr)
                if distort:
                    note = np.tanh(note * drive) * 0.4
                else:
                    note *= 0.4
            else:
                if distort:
                    note = sawtooth_distorted(freq, actual_len / sr, drive=drive, sr=sr)
                else:
                    note = sawtooth(freq, actual_len / sr, sr)
            # 빠른 어택 + 짧은 릴리즈 엔벨로프
            atk = min(int(sr * 0.005), actual_len // 4)
            rel = min(int(sr * 0.02), actual_len // 3)
            env = np.ones(actual_len)
            if atk > 0:
                env[:atk] = np.linspace(0, 1, atk)
            if rel > 0:
                env[-rel:] = np.linspace(1, 0, rel)
            trim = min(len(note), actual_len)
            note = note[:trim] * env[:trim]
            result[pos:pos + trim] += note
        pos += note_samples
        pat_idx += 1
    # v14: LP 필터 적용
    if cutoff_hz > 0:
        result = resonant_lowpass(result, cutoff_hz, sr=sr)
    return result


def numbers_to_euclidean(numbers: list, steps: int = 16) -> list:
    """대본 숫자 리스트 → 유클리드 리듬 패턴
    numbers 중 적절한 값을 pulses로 사용.
    e.g. [70, 3, 5] → E(3, 16) = [1,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0]
    반환: bool 리스트 (True=hit, False=rest)
    """
    # 숫자를 2~steps//2 범위로 클램프해서 pulses 추출
    candidates = [int(abs(n)) % (steps // 2) for n in numbers if abs(n) > 0]
    candidates = [c for c in candidates if 2 <= c <= steps // 2]
    pulses = candidates[0] if candidates else max(2, steps // 4)
    return euclidean_rhythm(steps, pulses)


def gate_pattern_from_si(si: float, bpm: float, duration: float,
                          sr: int = SAMPLE_RATE) -> np.ndarray:
    """semantic_intensity → 게이트 엔벨로프 배열
    si=0.0~0.25 → 4분음표  (느긋, 숨쉬는 느낌)
    si=0.25~0.5 → 8분음표  (중간, 기본 비트)
    si=0.5~0.75 → 16분음표 (촘촘, 긴장)
    si=0.75~1.0 → 32분음표 (초고속, 뚜뚜뚜뚜)
    duty cycle도 si에 따라 감소 → 높을수록 더 끊기는 느낌
    """
    beat_sec = 60.0 / bpm
    if si < 0.25:
        div = 4
        duty = 0.75
    elif si < 0.5:
        div = 8
        duty = 0.65
    elif si < 0.75:
        div = 16
        duty = 0.5
    else:
        div = 32   # 32분음표 — 초고속 뚜뚜뚜뚜
        duty = 0.4

    note_sec = beat_sec * 4 / div
    note_samples = max(int(sr * note_sec), 1)
    on_samples = max(int(note_samples * duty), 1)
    total_samples = int(sr * duration)
    gate = np.zeros(total_samples)

    for i in range(0, total_samples, note_samples):
        end = min(i + on_samples, total_samples)
        gate[i:end] = 1.0

    # 부드러운 on/off (클릭 방지, 32분음표는 ramp 더 짧게)
    ramp_ms = 1.0 if div >= 32 else 3.0
    ramp = min(int(sr * ramp_ms / 1000), on_samples // 4)
    if ramp > 0:
        for i in range(0, total_samples, note_samples):
            end = min(i + on_samples, total_samples)
            r = min(ramp, end - i)
            gate[i:i + r] = np.linspace(0, 1, r)
            off_start = end - ramp
            if off_start > i:
                gate[off_start:end] = np.linspace(1, 0, end - off_start)
    return gate


def stutter_from_data(signal: np.ndarray, data_density: float,
                       numbers: list, sr: int = SAMPLE_RATE) -> np.ndarray:
    """data_density + numbers → 스터터 효과
    data_density: 0~1 (높을수록 조각이 짧고 반복 많음)
    numbers: 대본 숫자 → 조각 길이(ms) 및 반복 횟수에 영향
    """
    total = len(signal)
    result = signal.copy()

    # 스터터 파라미터 결정
    base_chunk_ms = max(5.0, 100.0 * (1.0 - data_density))  # 5ms~100ms
    # 숫자로 청크 길이 미세조정 (숫자가 클수록 조각 더 짧게)
    if numbers:
        scale = 1.0 / max(1, min(abs(numbers[0]) / 50.0, 5.0))
        base_chunk_ms *= scale
    base_chunk_ms = max(5.0, min(base_chunk_ms, 120.0))
    chunk_samples = int(sr * base_chunk_ms / 1000)

    repeats = int(2 + data_density * 10)  # 2~12회

    # data_density 높은 구간에만 스터터 적용 (전체 신호에 랜덤 배치)
    stutter_probability = data_density * 0.4  # 최대 40% 구간에 스터터
    pos = 0
    while pos < total - chunk_samples * repeats:
        seg_len = random.randint(int(total * 0.05), int(total * 0.15))
        if random.random() < stutter_probability:
            # 스터터 적용: chunk를 반복 배치
            chunk_start = pos
            chunk = signal[chunk_start:chunk_start + chunk_samples].copy()
            if len(chunk) < chunk_samples:
                pos += seg_len
                continue
            # 윈도우 적용 (클릭 방지)
            w = np.hanning(len(chunk))
            chunk *= w
            for r in range(repeats):
                dst = chunk_start + r * chunk_samples
                if dst + chunk_samples > total:
                    break
                result[dst:dst + chunk_samples] = chunk
        pos += seg_len
    return result


# ============================================================
# Ikeda 합성 함수 — 순수 사인파 간섭, 데이터 클릭, 초고주파 텍스처
# ============================================================

def sine_interference(freq1, freq2, duration, sr=SAMPLE_RATE):
    """순수 사인파 2개의 간섭 → 비팅(beating) 패턴 자동 생성
    sin(2π·f1·t) + sin(2π·f2·t) → |f1-f2| Hz 맥놀이
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq1 * t) + np.sin(2 * np.pi * freq2 * t)
    wave *= 0.5  # normalize sum
    return wave


def data_click(freq, sr=SAMPLE_RATE):
    """극초단 (0.003s) 정밀 클릭 — 1사이클 사인파 버스트
    주파수가 대본 숫자를 인코딩 (70Hz, 120Hz, 83.3Hz...)
    """
    duration = max(1.0 / max(freq, 20), 0.003)  # 최소 1사이클 또는 3ms
    n_samples = int(sr * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    click = np.sin(2 * np.pi * freq * t)
    # 급격한 엔벨로프 — 즉시 시작, 급감쇠
    env = np.exp(-np.linspace(0, 8, n_samples))
    return click * env


def pulse_train(click_freq, repeat_rate, duration, rate_curve=None, sr=SAMPLE_RATE):
    """v7-P9: Ikeda 스타일 펄스 트레인 — 극초단 클릭을 고속 반복
    click_freq: 클릭 자체의 주파수 (음색, Hz)
    repeat_rate: 초당 반복 횟수 (Hz) — 10~200
    duration: 전체 길이 (초)
    rate_curve: 시간별 반복 속도 배열 (np.array, optional) — si 연동 시 가속/감속
    반환: 모노 numpy 배열
    """
    total_samples = int(sr * duration)
    result = np.zeros(total_samples)
    # 단일 클릭 템플릿 생성
    click = data_click(click_freq, sr)
    click_len = len(click)

    # rate_curve가 있으면 시간별 반복 속도 변화
    if rate_curve is not None and len(rate_curve) > 0:
        # rate_curve를 total_samples 길이로 리샘플
        curve = np.interp(
            np.linspace(0, 1, total_samples),
            np.linspace(0, 1, len(rate_curve)),
            rate_curve
        )
    else:
        curve = np.full(total_samples, float(repeat_rate))

    # 가변 간격으로 클릭 배치
    pos = 0
    while pos < total_samples:
        end = min(pos + click_len, total_samples)
        result[pos:end] += click[:end - pos]
        # 현재 위치의 반복 속도에서 다음 간격 계산
        current_rate = max(curve[min(pos, total_samples - 1)], 1.0)
        interval = int(sr / current_rate)
        pos += max(interval, click_len + 1)  # 클릭 겹침 방지

    return result


def granular_cloud(source_signal, grain_size_ms, density, scatter=0.0,
                   duration=None, sr=SAMPLE_RATE):
    """v7-P9: Microsound 그래뉼러 클라우드 — 소리를 grain으로 쪼개서 재배열
    source_signal: 원본 오디오 (사인파, 노이즈 등)
    grain_size_ms: grain 크기 (1~50ms)
    density: 초당 grain 수
    scatter: grain 배치 랜덤성 (0=균일, 1=완전 랜덤)
    duration: 출력 길이 (None이면 source_signal 길이)
    반환: 모노 numpy 배열
    """
    grain_samples = max(int(sr * grain_size_ms / 1000), 4)
    source_len = len(source_signal)
    out_len = int(sr * duration) if duration else source_len
    result = np.zeros(out_len)

    # Hanning window for grain
    window = np.hanning(grain_samples)

    num_grains = int((out_len / sr) * density)
    for i in range(num_grains):
        # grain 추출 위치 (원본에서)
        src_pos = random.randint(0, max(source_len - grain_samples, 0))
        grain = source_signal[src_pos:src_pos + grain_samples].copy()
        if len(grain) < grain_samples:
            grain = np.pad(grain, (0, grain_samples - len(grain)))
        grain *= window

        # grain 배치 위치 (출력에서)
        if scatter <= 0:
            # 균일 배치
            out_pos = int(i * out_len / max(num_grains, 1))
        else:
            # 균일 + 랜덤 혼합
            base_pos = int(i * out_len / max(num_grains, 1))
            jitter = int(scatter * out_len / max(num_grains, 1) * random.uniform(-0.5, 0.5))
            out_pos = max(0, min(base_pos + jitter, out_len - grain_samples))

        end = min(out_pos + grain_samples, out_len)
        result[out_pos:end] += grain[:end - out_pos]

    return result


def ultrahigh_texture(duration, center_freq=12000, bandwidth=4000, sr=SAMPLE_RATE):
    """8-20kHz 초고주파 텍스처 — 대역통과 필터링된 노이즈, '디지털 공기'
    매우 조용 (0.05-0.15 진폭)
    """
    n_samples = int(sr * duration)
    raw = np.random.uniform(-1, 1, n_samples)
    low = max(center_freq - bandwidth // 2, 100)
    high = min(center_freq + bandwidth // 2, sr // 2 - 100)
    filtered = bandpass(raw, low, high, sr=sr, order=2)
    # 진폭 정규화 후 극소 볼륨
    peak = np.max(np.abs(filtered))
    if peak > 0:
        filtered = filtered / peak * 0.1
    return filtered


def acid_bass(freq, duration, sweep_dir="down", sr=SAMPLE_RATE, cutoff_hz=2000):
    """애시드 베이스 v14 — 실제 레조넌트 LP 필터 스윕
    cutoff_hz: 기본 컷오프 (역할/에피소드별 다르게 전달)
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.zeros_like(t)
    for h in range(1, 8, 2):
        wave += np.sin(2 * np.pi * freq * h * t) / h
    wave *= 0.4
    wave = soft_clip(wave, drive=3.0)
    # v14: 실제 LP 필터 스윕 (시간 분할)
    n_chunks = 8
    chunk_size = len(wave) // n_chunks
    if sweep_dir == "down":
        cutoffs = np.linspace(cutoff_hz * 2.5, cutoff_hz * 0.3, n_chunks)
    else:
        cutoffs = np.linspace(cutoff_hz * 0.3, cutoff_hz * 2.5, n_chunks)
    filtered = np.zeros_like(wave)
    for i in range(n_chunks):
        s = i * chunk_size
        e = s + chunk_size if i < n_chunks - 1 else len(wave)
        chunk = wave[s:e]
        if len(chunk) > 20:
            filtered[s:e] = resonant_lowpass(chunk, cutoffs[i], sr=sr, order=4)
        else:
            filtered[s:e] = chunk
    filtered = envelope(filtered, attack=0.005, decay=0.06, sustain=0.55, release=0.12)
    return filtered


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

        # Hybrid Visual Architecture: 비주얼 엔진용 원본 데이터 수집 버퍼
        self._bytebeat_raw = np.zeros(self.total_samples)  # bytebeat 클리핑 전 원본
        self._section_instruments = {}  # 섹션별 활성 악기 목록

        # Ikeda: 사인파 간섭 + 데이터 클릭 비주얼 데이터
        self._sine_interference_raw = np.zeros(self.total_samples)
        self._data_click_positions = np.zeros(self.total_samples)  # boolean-like
        self._script_data = None  # script_data.json 로딩 시 사용
        self._si_env = None       # semantic_intensity 시간 도메인 엔벨로프
        self._si_modulation = None  # si → 볼륨 변조 배열 (0.7~1.3)
        # F-6: highlight_words → accent times
        self._highlight_words = meta.get("highlight_words", [])
        self._accent_times = []  # load_script_data() 후 빌드

        # v19: ep_seed 저장 (Vertical Remixing용)
        import hashlib as _hl
        _ep_id = str(meta.get("episode", "ep000"))
        self._ep_seed = int(_hl.md5(_ep_id.encode()).hexdigest(), 16) % (2**32)
        self._mood_layers_cache = None  # _generate_mood_layers 결과 캐시

        # v13+v14: 시퀀스+음색 설정 로드
        from sequence_generators import EpisodeSequenceConfig, derive_episode_sequences
        sc = meta.get("seq_config", {})
        if sc:
            self.seq_config = EpisodeSequenceConfig(
                drum_seq_type=sc.get("drum_seq_type", 0),
                drum_rotation=sc.get("drum_rotation", 0),
                pitch_rotation=sc.get("pitch_rotation", 0),
                pitch_length=sc.get("pitch_length", 6),
                bpm=self.bpm,
                # v14 음색 파라미터 (없으면 기본값)
                saw_harmonics=sc.get("saw_harmonics", {1: 1.0, 3: 0.5, 5: 0.2}),
                filter_cutoff_base=sc.get("filter_cutoff_base", 4000),
                chorus_depth_ms=sc.get("chorus_depth_ms", 2.5),
                fm_mod_ratio=sc.get("fm_mod_ratio", 2.0),
                bass_detune=sc.get("bass_detune", 0.002),
                kick_character=sc.get("kick_character", 0),
                arp_pattern=sc.get("arp_pattern", [1, 1.25, 1.5, 2, 1.5, 1.25]),
                arp_division=sc.get("arp_division", 4),
                # v21 멜로디 다양화
                melody_scale_offset=sc.get("melody_scale_offset", 0),
                melody_beat_base=sc.get("melody_beat_base", 3.0),
                melody_norgard_offset=sc.get("melody_norgard_offset", 0),
            )
        else:
            # fallback: episode_id 해시 기반 시드 (고정 시드 42 방지)
            import hashlib as _hl
            _fb_seed = int(_hl.md5(str(meta.get("episode", "ep000")).encode()).hexdigest(), 16) % (2**32)
            self.seq_config = derive_episode_sequences(_fb_seed)

        palette = script.get("palette", {})
        self.bass_freq = palette.get("bass_freq", 82.4)
        self.pad_root = palette.get("pad_root", 329.6)

        # v21: ep_seed 기반 멜로디 시퀀스 rebuild
        global SINE_MELODY_SEQUENCES
        SINE_MELODY_SEQUENCES = build_sine_melody_sequences(
            self.pad_root,
            scale_offset=self.seq_config.melody_scale_offset,
            beat_base=self.seq_config.melody_beat_base,
        )
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

    def _build_si_gate(self) -> np.ndarray:
        """v7-P8 → v11: si 기반 연속 악기 게이트 — 조용한 구간에서 연속 악기 볼륨 감쇠
        v11 변경: 계단 함수 → 연속 함수, 최소 0.45 (이전: 0.1)
        si=0.0 → 0.45 (최소 45%)
        si=0.5 → 1.0 (풀 볼륨)
        si=1.0 → 1.0
        1.0초 스무딩으로 갑작스러운 전환 방지 (이전: 0.3초)
        """
        if self._si_env is None:
            return np.ones(self.total_samples)

        si = self._si_env

        # 연속 게이트: np.clip(0.25 + si * 0.75, 0.25, 1.0)
        # B-3: si=0→0.25(침묵 아닌 미니멀), si=0.5→0.625, si=1.0→1.0
        gate = np.clip(0.25 + si * 0.75, 0.25, 1.0)

        # 1.0초 cumsum 스무딩 (급변 방지)
        window = int(1.0 * self.sr)
        if window > 1 and len(gate) > window:
            cumsum = np.cumsum(gate)
            cumsum = np.insert(cumsum, 0, 0)
            smoothed = (cumsum[window:] - cumsum[:-window]) / window
            pad_left = window // 2
            pad_right = self.total_samples - len(smoothed) - pad_left
            gate = np.concatenate([
                np.full(pad_left, smoothed[0]),
                smoothed,
                np.full(max(0, pad_right), smoothed[-1])
            ])[:self.total_samples]

        return gate

    def _compute_tempo_curve(self) -> np.ndarray:
        """v12: 에피소드 전체 고정 BPM — 한 곡으로 들리게.
        가변 BPM은 섹션 경계에서 리듬이 끊기는 원인이었으므로 제거.
        최소 BPM: 무드별 하한 (ambient/ikeda/chill=70, 나머지=95)
        """
        music_mood = self.script.get("metadata", {}).get("music_mood", "acid")
        min_bpm = 60 if music_mood in ("ambient", "dub") else 85 if music_mood == "microsound" else 95
        fixed_bpm = max(float(self.bpm), min_bpm)
        return np.full(self.total_samples, fixed_bpm)

    def _section_bpm(self, section) -> float:
        """v7-P6: 섹션의 평균 BPM (가변 BPM 곡선에서 추출)"""
        if not hasattr(self, '_tempo_curve') or self._tempo_curve is None:
            return float(self.bpm)
        start = int(section["start_sec"] * self.sr)
        end = min(int(section["end_sec"] * self.sr), self.total_samples)
        if start >= end:
            return float(self.bpm)
        return float(np.mean(self._tempo_curve[start:end]))

    # ---- 기반 악기: 전체 길이 연속 렌더링 ----

    # ── v19: 미구현이었던 dub/industrial 전용 악기 연속 렌더 ──────────────

    def _render_continuous_chord_stab(self, sections):
        """dub techno 코드 스탭 — 2초 주기로 반복, tape_delay와 조합"""
        print("  [chord_stab] continuous dub chord stab...", flush=True)
        vol_env = smooth_envelope(
            self.total_samples, sections, "chord_stab", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        # BPM 기반 스탭 주기: 2바마다 1회
        bar_sec = (60.0 / self.bpm) * 4
        stab_interval = bar_sec * 2  # 2바마다
        stab_dur = min(stab_interval * 0.8, 2.0)  # 최대 2초
        pos = 0.0
        while pos < self.duration:
            stab = chord_stab(self.pad_root * 0.5, stab_dur, self.sr)
            start_sample = int(pos * self.sr)
            end_sample = min(start_sample + len(stab), self.total_samples)
            length = end_sample - start_sample
            if length > 0:
                local_vol = vol_env[start_sample:end_sample]
                self.master_L[start_sample:end_sample] += stab[:length] * local_vol
                self.master_R[start_sample:end_sample] += stab[:length] * local_vol
            pos += stab_interval

    def _render_continuous_rhodes_pad(self, sections):
        """Deep House 로즈 패드 — 2바마다 minor 9 코드 반복.
        느린 어택 + LP 필터로 따뜻한 house 질감. 스테레오 미세 와이드닝 포함.
        """
        print("  [rhodes_pad] continuous Deep House rhodes pad...", flush=True)
        vol_env = smooth_envelope(
            self.total_samples, sections, "rhodes_pad", "volume",
            default=0.0, morph_sec=1.5, sr=self.sr
        )
        bar_sec = (60.0 / self.bpm) * 4
        pad_interval = bar_sec * 2          # 2바마다 새 코드
        pad_dur = min(pad_interval * 1.05, 4.0)  # 약간 겹치게 — 음이 끊기지 않음
        pos = 0.0
        while pos < self.duration:
            pad = rhodes_pad(self.pad_root * 0.5, pad_dur, self.sr, brightness=0.5)
            start_sample = int(pos * self.sr)
            end_sample = min(start_sample + len(pad), self.total_samples)
            length = end_sample - start_sample
            if length > 0:
                local_vol = vol_env[start_sample:end_sample]
                # 스테레오 와이드닝 (L/R 미세 비율 차)
                self.master_L[start_sample:end_sample] += pad[:length] * local_vol * 1.04
                self.master_R[start_sample:end_sample] += pad[:length] * local_vol * 0.96
            pos += pad_interval

    def _render_continuous_distorted_kick(self, sections):
        """industrial 디스토션 킥 — 정규 킥과 교대 배치"""
        print("  [distorted_kick] continuous industrial kick...", flush=True)
        vol_env = smooth_envelope(
            self.total_samples, sections, "distorted_kick", "volume",
            default=0.0, morph_sec=0.5, sr=self.sr
        )
        # 매 2바의 2번째 바 첫 박에 배치 (정규 킥과 교대)
        bar_sec = (60.0 / self.bpm) * 4
        pos = bar_sec  # 2번째 바부터 시작
        dk = distorted_kick(50, self.sr, drive=3.5)
        while pos < self.duration:
            start_sample = int(pos * self.sr)
            end_sample = min(start_sample + len(dk), self.total_samples)
            length = end_sample - start_sample
            if length > 0:
                local_vol = vol_env[start_sample:end_sample]
                self.master_L[start_sample:end_sample] += dk[:length] * local_vol
                self.master_R[start_sample:end_sample] += dk[:length] * local_vol
            pos += bar_sec * 2  # 2바마다

    def _apply_tape_delay_to_master(self):
        """dub techno 테이프 딜레이 — 마스터 전체에 적용"""
        print("  [tape_delay] applying dub tape delay to master...", flush=True)
        cfg = (self._mood_layers_cache or {}).get("tape_delay", {})
        feedback = cfg.get("feedback", 0.6)
        # BPM 동기 딜레이: 3/16 노트 (dub 스타일)
        delay_ms = (60000.0 / self.bpm) * (3.0 / 4.0)  # dotted 8th
        self.master_L[:] = tape_delay(self.master_L, delay_ms=delay_ms, feedback=feedback, sr=self.sr)
        self.master_R[:] = tape_delay(self.master_R, delay_ms=delay_ms, feedback=feedback * 0.9, sr=self.sr)

    def _render_continuous_bass(self, sections):
        """전체 길이 베이스 드론 — 볼륨만 섹션별 모핑"""
        print("  [bass] continuous drone...", flush=True)
        drone = deep_bass_drone(self.bass_freq, self.duration, self.sr,
                                detune=self.seq_config.bass_detune)
        vol_env = smooth_envelope(
            len(drone), sections, "bass_drone", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        drone *= vol_env * 1.2  # v16: si_gate 제거, 페이드 제거
        self._add_mono(drone, 0, 1.0)

    def _render_continuous_fm_bass(self, sections):
        """전체 길이 FM 베이스 v14 — 동적 mod_ratio + detune"""
        print("  [fm] continuous fm bass (v14)...", flush=True)
        fm = fm_bass(self.pad_root * 0.5, self.duration,
                     mod_ratio=self.seq_config.fm_mod_ratio, mod_depth=200,
                     sr=self.sr, detune=self.seq_config.bass_detune)
        vol_env = smooth_envelope(
            len(fm), sections, "fm_bass", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        fm *= vol_env * 1.0  # v16: si_gate 제거, 페이드 제거

        # v22: wavefold — 모듈러 디스토션 (industrial/IDM)
        music_mood = self.script.get("metadata", {}).get("music_mood", "acid")
        if music_mood in ("industrial", "IDM"):
            import random as _rng
            folds = 2 + (_rng.Random(self._ep_seed + 5555).randint(0, 2))  # 2~4
            fm = wavefold(fm, folds=folds) * 0.8
            print(f"  [fm] v22 wavefold: folds={folds}", flush=True)

        self._add_mono(fm, 0, 1.0)

    def _render_continuous_rhythm(self, sections):
        """v11 패턴 엔진: 바 카운팅 + 섹션별 패턴 선택 + 필/드롭

        F-3: 단일 패턴 → 16-step 패턴 라이브러리 + 바 단위 렌더링
        - SI + emotion → 시퀀스 기반 드럼 패턴 생성 (v13)
        - 8바마다 fill_buildup, 16바마다 fill_snare_roll (v12: 필인 빈도 감소)
        - SI 급상승 섹션 경계에서 drop_silence → drop_impact
        - snare_drum() 배치 추가
        """
        has_tempo = hasattr(self, '_tempo_curve') and self._tempo_curve is not None
        bpm_info = ""
        if has_tempo:
            bpm_min, bpm_max = float(self._tempo_curve.min()), float(self._tempo_curve.max())
            if abs(bpm_max - bpm_min) > 0.5:
                bpm_info = f", bpm={bpm_min:.1f}~{bpm_max:.1f}"
        print(f"  [rhythm] v11 pattern engine (bars+fills+drops{bpm_info})...", flush=True)

        # BPM 조회 함수
        def bpm_at(t_sec):
            if has_tempo:
                idx = max(0, min(int(t_sec * self.sr), self.total_samples - 1))
                return float(self._tempo_curve[idx])
            return float(self.bpm)

        # 원샷 사운드 사전 렌더 (v14: kick character)
        k = kick_drum(self.bass_freq * 0.5, self.sr, character=self.seq_config.kick_character)
        sn = snare_drum(self.bass_freq * 1.5, self.sr)
        t_impact = transition_impact(self.sr)  # v12: 섹션 전환 임팩트

        # 이벤트 버퍼
        kick_full = np.zeros(self.total_samples)
        snare_full = np.zeros(self.total_samples)
        hihat_full_L = np.zeros(self.total_samples)
        hihat_full_R = np.zeros(self.total_samples)
        impact_full = np.zeros(self.total_samples)  # v12: 전환 임팩트 버퍼

        # v13: 섹션별 SI 평균 + 시퀀스 기반 드럼 패턴 사전 계산
        from sequence_generators import generate_drum_pattern, generate_fill_pattern
        section_si = {}
        section_drum_pat = {}  # v13: dict{"kick","snare","hihat"} per section
        drum_mode = getattr(self, '_drum_mode', 'default')
        music_mood = self.script.get("metadata", {}).get("music_mood", "acid")
        for sec in sections:
            sid = sec.get("id", "?")
            s_start = int(sec["start_sec"] * self.sr)
            s_end = min(int(sec["end_sec"] * self.sr), self.total_samples)
            if self._si_env is not None and s_start < s_end:
                si_avg = float(np.mean(self._si_env[s_start:s_end]))
            else:
                si_avg = sec.get("energy", 0.5)
            section_si[sid] = si_avg
            role = sec.get("_role", sec.get("emotion", "drop"))

            if drum_mode == "simple":
                # 베이직 테크노 루프: 4-on-the-floor 킥 + 8분음표 클로즈드 하이햇 + 스네어 2,4박
                # 생성 패턴이 아닌 고정 패턴 — 필인/변주 없음
                base_pat = {
                    "kick":  [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
                    "snare": [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],
                    "hihat": [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
                }
            else:
                # dynamic=조밀, default=si_avg
                effective_si = 1.0 if drum_mode == "dynamic" else si_avg
                base_pat = generate_drum_pattern(self.seq_config, role, effective_si)

                # v17: 무드별 유클리드 패턴 오버라이드 (MOOD_RHYTHM_PRESETS)
                rhythm_preset = self.MOOD_RHYTHM_PRESETS.get(music_mood)
                if rhythm_preset is not None:
                    for part in ("kick", "snare", "hihat"):
                        euclid_spec = rhythm_preset.get(part)
                        if euclid_spec is not None:
                            pulses, steps = euclid_spec
                            raw_pat = list(euclidean_rhythm(steps, pulses))
                            base_pat[part] = [raw_pat[i % len(raw_pat)] for i in range(16)]

            section_drum_pat[sid] = base_pat

        # v12: 드롭 감지 — role 기반 (drop/drop2 섹션의 시작 시점)
        drop_boundaries = set()
        for sec in sections:
            role = sec.get("_role", sec.get("emotion", ""))
            if role in ("drop", "drop2"):
                drop_boundaries.add(sec["start_sec"])

        # 현재 섹션 조회 헬퍼
        def section_at(t_sec):
            for sec in sections:
                if sec["start_sec"] <= t_sec < sec["end_sec"]:
                    return sec
            return sections[-1] if sections else None

        # 에피소드 시드 기반 결정론적 랜덤
        rng = random.Random(self.seed if hasattr(self, 'seed') else 42)

        # ── 바 단위 렌더링 루프 ──
        t = 0.0
        bar_idx = 0
        drop_state = 0  # 0=normal, 1=pre_drop(silence), 2=post_drop(impact)
        prev_role = None  # v12: 섹션 전환 감지용

        while t < self.duration:
            cur_bpm = bpm_at(t)
            step_interval = (60.0 / cur_bpm) / 4  # 16th note interval
            bar_duration = step_interval * 16      # 4/4 1바 = 16 sixteenths

            sec = section_at(t)
            if sec is None:
                t += bar_duration
                bar_idx += 1
                continue

            sid = sec.get("id", "?")
            cur_role = sec.get("_role", sec.get("emotion", ""))

            # ── 드롭 메커닉 ──
            bar_end_t = t + bar_duration

            # 다음 바 시작이 드롭 경계에 가까운지 체크
            is_near_drop = False
            for db in drop_boundaries:
                if abs(bar_end_t - db) < bar_duration * 1.5:
                    is_near_drop = True
                    break

            # v16: 패턴 결정 — drum_mode별 필인 빈도 차별화
            if drum_mode == "simple":
                # simple: 베이직 테크노 루프 — 필인 없이 고정 패턴 반복
                pat = section_drum_pat.get(sid, base_pat)
            elif drop_state == 1:
                pat = generate_fill_pattern(self.seq_config, "drop_impact")
                drop_state = 0
            elif is_near_drop and drop_state == 0:
                pat = generate_fill_pattern(self.seq_config, "drop_silence")
                drop_state = 1
            elif cur_role == "buildup" and is_near_drop:
                pat = generate_fill_pattern(self.seq_config, "fill_snare_roll")
            elif drum_mode == "dynamic":
                # dynamic: 필인 빈도 2배 (8바→4바, 16바→8바)
                if bar_idx % 8 == 7:
                    pat = generate_fill_pattern(self.seq_config, "fill_snare_roll")
                elif bar_idx % 4 == 3:
                    pat = generate_fill_pattern(self.seq_config, "fill_buildup")
                else:
                    pat = section_drum_pat.get(sid, generate_drum_pattern(self.seq_config, cur_role, 0.5))
            elif bar_idx % 16 == 15:
                pat = generate_fill_pattern(self.seq_config, "fill_snare_roll")
            elif bar_idx % 8 == 7:
                pat = generate_fill_pattern(self.seq_config, "fill_buildup")
            else:
                pat = section_drum_pat.get(sid, generate_drum_pattern(self.seq_config, cur_role, 0.5))

            # v12: 섹션 전환 감지 — 첫 바의 step-0 킥을 임팩트로 대체
            is_transition_bar = (prev_role is not None and prev_role != cur_role)

            # ── 16-step 렌더링 ──
            for step in range(16):
                step_t = t + step * step_interval
                pos = int(step_t * self.sr)
                if pos >= self.total_samples:
                    break

                # 킥 (v12: breakdown에서 킥 제거, 전환 바 step-0 킥 제거)
                if pat["kick"][step] and cur_role != "breakdown":
                    if is_transition_bar and step == 0:
                        # 전환점: 킥 대신 임팩트
                        end = min(pos + len(t_impact), self.total_samples)
                        impact_full[pos:end] += t_impact[:end - pos]
                    else:
                        end = min(pos + len(k), self.total_samples)
                        kick_full[pos:end] += k[:end - pos]

                # 스네어
                if pat["snare"][step]:
                    end = min(pos + len(sn), self.total_samples)
                    snare_full[pos:end] += sn[:end - pos]

                # 하이햇
                if pat["hihat"][step]:
                    is_open = rng.random() > 0.65
                    h = hi_hat(open_hat=is_open, sr=self.sr)
                    pan = rng.uniform(-0.2, 0.2)
                    s = stereo_pan(h, pan)
                    end = min(pos + len(h), self.total_samples)
                    hihat_full_L[pos:end] += s[:end - pos, 0]
                    hihat_full_R[pos:end] += s[:end - pos, 1]

            prev_role = cur_role
            t += bar_duration
            bar_idx += 1

        total_bars = bar_idx
        print(f"    → {total_bars} bars rendered", flush=True)

        # F-6: highlight_words accent — 킥+스네어 동시 히트
        accent_count = 0
        for at in self._accent_times:
            pos = int(at * self.sr)
            if 0 <= pos < self.total_samples:
                end_k = min(pos + len(k), self.total_samples)
                kick_full[pos:end_k] += k[:end_k - pos] * 1.5  # 강조 볼륨
                end_s = min(pos + len(sn), self.total_samples)
                snare_full[pos:end_s] += sn[:end_s - pos] * 1.2
                accent_count += 1
        if accent_count:
            print(f"    → {accent_count} accent hits placed", flush=True)

        # 볼륨 엔벨로프 적용
        kick_vol_env = smooth_envelope(
            self.total_samples, sections, "kick", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr  # v12: 0.5→1.0 전환 부드럽게
        )
        hihat_vol_env = smooth_envelope(
            self.total_samples, sections, "hi_hat", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr  # v12: 0.5→1.0 전환 부드럽게
        )
        # 스네어는 킥 볼륨 엔벨로프를 공유 (별도 악기 키 없으면)
        snare_vol_env = kick_vol_env

        # v16: si_gate 제거 — 드럼은 ARRANGEMENT_TABLE 볼륨으로만 제어
        # F-7: 콜앤리스폰스 드럼 엔벨로프
        cr_d = self._cr_drum_env[:self.total_samples] if hasattr(self, '_cr_drum_env') else 1.0
        self.master_L += kick_full * kick_vol_env * cr_d * 2.5
        self.master_R += kick_full * kick_vol_env * cr_d * 2.5
        self.master_L += snare_full * snare_vol_env * cr_d * 1.2
        self.master_R += snare_full * snare_vol_env * cr_d * 1.2
        self.master_L += hihat_full_L * hihat_vol_env * cr_d * 2.2
        self.master_R += hihat_full_R * hihat_vol_env * cr_d * 2.2
        # v12: 전환 임팩트
        self.master_L += impact_full * kick_vol_env * 3.0
        self.master_R += impact_full * kick_vol_env * 3.0

        # v16: 마디 첫박 다운비트 사운드 — 7종 계층 배치
        # 댄스 뮤직 관용: 마디 경계에 임팩트/크래시로 구조 표현 (페이드 대신)
        # 계층 (작은 단위 → 큰 단위):
        # - 매 마디(홀수): noise hit / 매 마디(짝수): ping pong
        # - 매 2마디: sine pop (Ikeda 디지털 텍스처)
        # - 매 4마디: crash + sub boom + open hat
        # - 매 16마디: reverse crash (당김 → 히트)
        d_noise = downbeat_noise_hit(self.sr)
        d_crash = downbeat_crash(self.sr)
        d_rev = downbeat_reverse_crash(self.sr)
        d_sine = downbeat_sine_pop(self.sr)
        d_boom = downbeat_sub_boom(self.sr)
        d_ohat = downbeat_open_hat(self.sr)
        d_ping_L, d_ping_R = downbeat_ping_pong(self.sr)

        downbeat_L = np.zeros(self.total_samples)
        downbeat_R = np.zeros(self.total_samples)
        bar_dur = 60.0 / self.bpm * 4
        bar_count = 0
        t_bar = 0.0
        crash_count = 0
        rev_count = 0
        while t_bar < self.duration:
            pos = int(t_bar * self.sr)
            if pos >= self.total_samples:
                break

            # 매 마디: noise hit(홀수) / ping pong(짝수) 교대
            if bar_count % 2 == 0:
                end_n = min(pos + len(d_noise), self.total_samples)
                downbeat_L[pos:end_n] += d_noise[:end_n - pos] * 0.8
                downbeat_R[pos:end_n] += d_noise[:end_n - pos] * 0.7
            else:
                end_pl = min(pos + len(d_ping_L), self.total_samples)
                downbeat_L[pos:end_pl] += d_ping_L[:end_pl - pos] * 0.9
                end_pr = min(pos + len(d_ping_R), self.total_samples)
                downbeat_R[pos:end_pr] += d_ping_R[:end_pr - pos] * 0.9

            # 매 2마디: sine pop (날카로운 디지털 클릭)
            if bar_count % 2 == 0:
                end_s = min(pos + len(d_sine), self.total_samples)
                downbeat_L[pos:end_s] += d_sine[:end_s - pos] * 0.6
                downbeat_R[pos:end_s] += d_sine[:end_s - pos] * 0.6

            # 매 4마디: crash + sub boom + open hat
            if bar_count % 4 == 0:
                end_c = min(pos + len(d_crash), self.total_samples)
                downbeat_L[pos:end_c] += d_crash[:end_c - pos] * 1.2
                downbeat_R[pos:end_c] += d_crash[:end_c - pos] * 1.0
                # sub boom: 무게감
                end_b = min(pos + len(d_boom), self.total_samples)
                downbeat_L[pos:end_b] += d_boom[:end_b - pos] * 0.7
                downbeat_R[pos:end_b] += d_boom[:end_b - pos] * 0.7
                # open hat: 그루브
                end_oh = min(pos + len(d_ohat), self.total_samples)
                downbeat_L[pos:end_oh] += d_ohat[:end_oh - pos] * 0.5
                downbeat_R[pos:end_oh] += d_ohat[:end_oh - pos] * 0.5
                crash_count += 1

            # 매 16마디: reverse crash (첫박 0.8초 전에 시작)
            if bar_count % 16 == 0 and bar_count > 0:
                rev_start = max(0, pos - len(d_rev))
                rev_end = min(rev_start + len(d_rev), self.total_samples)
                actual_len = rev_end - rev_start
                if actual_len > 0:
                    downbeat_L[rev_start:rev_end] += d_rev[:actual_len] * 0.9
                    downbeat_R[rev_start:rev_end] += d_rev[:actual_len] * 0.8
                    rev_count += 1

            bar_count += 1
            t_bar += bar_dur

        self.master_L += downbeat_L * kick_vol_env
        self.master_R += downbeat_R * kick_vol_env
        print(f"    -> {bar_count} bars: noise/ping-pong hits, {crash_count} crash+boom+ohat, {rev_count} reverse crashes", flush=True)

    def _render_continuous_sub_pulse(self, sections):
        """전체 길이 서브 펄스"""
        print("  [sub] continuous sub pulse...", flush=True)
        sub = sub_pulse(self.bass_freq * 0.5, self.duration, self.bpm, self.sr)
        vol_env = smooth_envelope(
            len(sub), sections, "sub_pulse", "volume",
            default=0.0, morph_sec=0.8, sr=self.sr
        )
        sub *= vol_env * 0.7  # v16: si_gate 제거
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

        # v19: seq_config에서 아르페지오 패턴/분할 가져오기
        arp_pat = self.seq_config.arp_pattern
        arp_div = self.seq_config.arp_division
        print(f"  [arp] pattern={arp_pat}, division={arp_div} ({'16th' if arp_div==4 else '8th' if arp_div==2 else 'triplet'})", flush=True)

        arp = arpeggio_sequence(
            self.arp_root, self.duration, arp_pat,
            speed=avg_speed, sr=self.sr, bpm=self.bpm, division=arp_div,
            apply_chorus=True, chorus_depth_ms=self.seq_config.chorus_depth_ms
        )
        vol_env = smooth_envelope(
            len(arp), sections, "arpeggio", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        arp *= vol_env * 1.2  # v16: si_gate 제거

        # 디튠 스테레오 쌍
        arp2 = arpeggio_sequence(
            self.arp_root + 1, self.duration,
            [p * 1.01 for p in arp_pat],
            speed=avg_speed * 1.02, sr=self.sr, division=arp_div
        )
        arp2 *= vol_env * 0.7  # v16: si_gate 제거

        self._add_stereo(arp, -0.3, 0, 1.0)
        self._add_stereo(arp2, 0.3, 0.05, 1.0)

    # ---- Ikeda 전용 연속 렌더러 ----

    def _render_continuous_sine_interference(self, sections):
        """v21: ep_seed 기반 멜로디 변주 + Norgard pitch modulation"""
        print("  [sine_interference] v21 seed-varied melodic drone...", flush=True)
        bpm = self.script.get("metadata", {}).get("base_bpm", 60)
        bar_duration = (60.0 / bpm) * 4  # 4/4 박자 1마디
        fade_sec = 0.1  # 주파수 쌍 전환 크로스페이드

        # Norgard pitch modulation 준비 (ep_seed 기반)
        norgard_offset = self.seq_config.melody_norgard_offset
        from sequence_generators import norgard as norgard_seq, rotate
        norgard_raw = norgard_seq(64)
        norgard_rotated = rotate(norgard_raw, norgard_offset)
        # Norgard 값을 0.95~1.05 범위의 미세 음고 변조 비율로 매핑
        n_min, n_max = min(norgard_rotated[:32]), max(norgard_rotated[:32])
        n_range = max(1, n_max - n_min)
        norgard_ratios = [0.97 + 0.06 * (v - n_min) / n_range for v in norgard_rotated]

        total = np.zeros(self.total_samples)
        t = np.linspace(0, self.duration, self.total_samples, endpoint=False)
        fade_samples = int(fade_sec * self.sr)

        for sec in sections:
            sec_start = sec.get("start_sec", 0)
            sec_end = sec.get("end_sec", self.duration)
            s0 = int(sec_start * self.sr)
            s1 = min(int(sec_end * self.sr), self.total_samples)
            if s0 >= s1:
                continue

            # 감정에서 멜로디 시퀀스 결정
            emotion = sec.get("emotion", "neutral")
            melody_key = EMOTION_TO_MELODY.get(emotion, "neutral")
            melody_seq = SINE_MELODY_SEQUENCES.get(melody_key, SINE_MELODY_SEQUENCES["neutral"])

            # 섹션 내에서 4마디 단위로 주파수 쌍 순환
            chunk_bars = 4  # 4마디마다 전환

            local_pos = 0
            chunk_idx = 0
            while local_pos < (s1 - s0):
                # 현재 chunk의 주파수 쌍
                pair_idx = chunk_idx % len(melody_seq)
                f1, f2 = melody_seq[pair_idx]

                # Norgard pitch modulation: 매 4바 chunk마다 미세 음고 이동
                norgard_idx = chunk_idx % len(norgard_ratios)
                pitch_mod = norgard_ratios[norgard_idx]
                f1 *= pitch_mod
                f2 *= pitch_mod

                chunk_samples = int(chunk_bars * bar_duration * self.sr)
                chunk_end = min(local_pos + chunk_samples, s1 - s0)

                # 사인파 간섭 생성
                chunk_t = t[s0 + local_pos: s0 + chunk_end]
                interference = np.sin(2 * np.pi * f1 * chunk_t) + np.sin(2 * np.pi * f2 * chunk_t)
                interference *= 0.2  # 기본 볼륨

                # 크로스페이드: chunk 시작/끝에 fade 적용
                chunk_len = len(interference)
                if chunk_len > fade_samples * 2:
                    fade_in_env = np.linspace(0, 1, fade_samples)
                    fade_out_env = np.linspace(1, 0, fade_samples)
                    interference[:fade_samples] *= fade_in_env
                    interference[-fade_samples:] *= fade_out_env

                total[s0 + local_pos: s0 + local_pos + chunk_len] += interference

                local_pos = chunk_end
                chunk_idx += 1

        # 섹션별 볼륨 모핑 (data_density 기반)
        vol_env = smooth_envelope(
            self.total_samples, sections, "sine_interference", "volume",
            default=0.3, morph_sec=1.5, sr=self.sr
        )
        total *= vol_env  # v16: si_gate 제거

        # 비주얼 데이터 수집
        self._sine_interference_raw[:len(total)] = total

        # 스테레오: L/R에 미세하게 다른 디튠
        total_L = total.copy()
        total_R = total.copy()
        detune = np.sin(2 * np.pi * 220.5 * t) * 0.05
        total_R += detune[:self.total_samples]

        # v16: 페이드 제거
        self.master_L += total_L
        self.master_R += total_R

    def _render_continuous_ultrahigh(self, sections):
        """전체 길이 초고주파 텍스처 — data_density에 따라 center_freq 변조"""
        print("  [ultrahigh] continuous ultrahigh texture...", flush=True)
        texture = ultrahigh_texture(self.duration, center_freq=12000, bandwidth=4000, sr=self.sr)
        vol_env = smooth_envelope(
            len(texture), sections, "ultrahigh_texture", "volume",
            default=0.05, morph_sec=2.0, sr=self.sr
        )
        texture *= vol_env  # v16: si_gate 제거, 페이드 제거
        self._add_mono(texture, 0, 1.0)

    def _render_continuous_pulse_train(self, sections):
        """v7-P9: 전체 길이 펄스 트레인 — si 연동 반복 속도, 대본 숫자 → 클릭 주파수
        si=0 → 20Hz 느린 클릭 / si=0.5 → 100Hz 연속 버즈 / si=1 → 200Hz 급속 버즈
        """
        print("  [pulse_train] continuous pulse train...", flush=True)

        # si 기반 rate_curve 생성 (20~200Hz)
        if self._si_env is not None:
            rate_curve = 20.0 + self._si_env * 180.0  # si=0→20Hz, si=1→200Hz
        else:
            rate_curve = np.full(self.total_samples, 60.0)  # 기본 60Hz

        # 대본 숫자에서 대표 주파수 추출
        click_freq = 440.0  # 기본값
        if self._script_data:
            all_numbers = []
            for seg in self._script_data.get("segments", []):
                nums = seg.get("analysis", {}).get("numbers", [])
                all_numbers.extend([abs(n) for n in nums if abs(n) > 20])
            if all_numbers:
                click_freq = float(np.median(all_numbers))
                click_freq = max(40, min(click_freq, 2000))

        # 펄스 트레인 생성
        pt = pulse_train(click_freq, 60.0, self.duration, rate_curve=rate_curve, sr=self.sr)

        # 섹션별 볼륨 모핑
        vol_env = smooth_envelope(
            len(pt), sections, "pulse_train", "volume",
            default=0.0, morph_sec=1.5, sr=self.sr
        )
        pt *= vol_env * 0.4  # 전체 볼륨 스케일

        # 그래뉼러 레이어 추가 (밀도 변화하는 노이즈 그레인)
        if self._si_env is not None:
            # si 높은 구간에만 그래뉼러 활성화
            si_mean = float(np.mean(self._si_env))
            if si_mean > 0.3:
                source = noise(self.duration, self.sr)
                gc = granular_cloud(source, grain_size_ms=5.0, density=si_mean * 80,
                                    scatter=0.3, duration=self.duration, sr=self.sr)
                gc *= vol_env * 0.15  # 서브 레이어
                pt += gc

        # v16: 페이드 제거
        # 좌우 약간 다른 위치에 배치 (스테레오 width)
        self._add_stereo(pt, random.uniform(-0.3, 0.3), 0, 1.0)

    def _render_continuous_modular_clicks(self, sections):
        """v22: 모듈러 클릭 텍스처 — 키워드/이벤트 시점에 임팩트 클릭 배치.

        대본 키워드 타이밍에 맞춰 2~6kHz 전자 클릭을 배치하여
        데이터 포인트를 청각적으로 표현. ep_seed 기반 결정론적.
        """
        print("  [modular_clicks] v22 keyword-event clicks...", flush=True)
        sd_segments = self._script_data.get("segments", []) if self._script_data else []

        clicks_buf = np.zeros(self.total_samples)

        # 키워드 타이밍에서 클릭 이벤트 수집
        import random as _rng
        click_rng = _rng.Random(self._ep_seed + 8888)
        event_times = []

        for seg in sd_segments:
            start_sec = seg.get("start_sec", 0)
            end_sec = seg.get("end_sec", 0)
            analysis = seg.get("analysis", {})
            keywords = analysis.get("keywords", [])
            numbers = analysis.get("numbers", [])

            # 키워드마다 클릭 배치 (세그먼트 시작~끝 사이에 분산)
            n_events = len(keywords) + len(numbers)
            if n_events > 0:
                seg_dur = max(0.1, end_sec - start_sec)
                for i in range(min(n_events, 6)):  # 세그먼트당 최대 6클릭
                    t = start_sec + click_rng.uniform(0, seg_dur)
                    event_times.append(t)

        # 클릭 생성 및 배치
        for t in event_times:
            idx = int(t * self.sr)
            click = modular_click(self.sr)
            end_idx = min(idx + len(click), self.total_samples)
            actual_len = end_idx - idx
            if actual_len > 0 and idx >= 0:
                clicks_buf[idx:end_idx] += click[:actual_len]

        # 섹션별 볼륨 모핑
        vol_env = smooth_envelope(
            self.total_samples, sections, "modular_clicks", "volume",
            default=0.0, morph_sec=0.5, sr=self.sr
        )
        clicks_buf *= vol_env * 0.6

        # 스테레오 배치 (랜덤 패닝)
        self._add_stereo(clicks_buf, click_rng.uniform(-0.5, 0.5), 0, 1.0)

    def _render_continuous_saw_sequence(self, sections):
        """v12: 전체 길이 쏘우파 게이트 시퀀서 — enometa 리듬의 핵심 뼈대
        에피소드 전체에서 하나의 패턴 키를 고정하여 "한 곡"으로 들리게 함.
        에너지 차이는 볼륨(smooth_envelope)과 si_gate로만 표현.
        """
        print("  [saw_seq] continuous sawtooth gate sequencer...", flush=True)
        bpm = self.script.get("metadata", {}).get("base_bpm", 120)

        # v13: 시퀀스 기반 피치 패턴 (SAW_PATTERNS 하드코딩 대체)
        from sequence_generators import generate_pitch_pattern, rotate as seq_rotate
        GATE_DIV = {
            "high": 16, "mid": 8, "low": 4, "tension": 16
        }

        # 메인 쏘우 시퀀스 (L 채널, 베이스 음역)
        saw_L = np.zeros(self.total_samples)
        # 디튠된 쏘우 시퀀스 (R 채널, 약간 높은 음역)
        saw_R = np.zeros(self.total_samples)

        # 에너지 레벨 결정 (GATE_DIV 선택용)
        avg_energy = np.mean([sec.get("energy", 0.3) for sec in sections]) if sections else 0.3
        has_tension = any("tension" in sec.get("emotion", "") or "frustrated" in sec.get("emotion", "")
                         for sec in sections)
        if has_tension and avg_energy >= 0.5:
            fixed_pat_key = "tension"
        elif avg_energy >= 0.6:
            fixed_pat_key = "high"
        elif avg_energy >= 0.35:
            fixed_pat_key = "mid"
        else:
            fixed_pat_key = "mid"

        # v14+: seed 기반 gate_div 미세 변동 (같은 energy라도 에피소드마다 다른 gate 밀도)
        import random as _rng
        _gate_options = {
            "mid":     [8, 8, 16],
            "high":    [16, 16, 32],
            "tension": [16, 32],
            "low":     [4, 8],
        }
        _gate_rng = _rng.Random(self._ep_seed + 3333)
        fixed_gate_div = _gate_rng.choice(_gate_options.get(fixed_pat_key, [8]))
        fixed_note_len = 0.85 if fixed_pat_key in ["low", "mid"] else 0.6

        # v14+: seed 기반 동적 pat_list 생성 (3~5개 변형, 에피소드마다 다른 rotation 오프셋)
        base_pitch_pat = generate_pitch_pattern(self.seq_config, fixed_pat_key)
        _pat_rng = _rng.Random(self._ep_seed + 7777)
        num_variations = 3 + self.seq_config.pitch_rotation % 3  # 3~5개
        pat_len = len(base_pitch_pat)
        _max_offset = pat_len * 2
        rotation_offsets = sorted(_pat_rng.sample(range(1, _max_offset), min(num_variations - 1, _max_offset - 1)))
        pat_list = [base_pitch_pat] + [seq_rotate(base_pitch_pat, off) for off in rotation_offsets]
        print(f"  [saw_seq] v14+ seed={self._ep_seed}: {fixed_pat_key}, gate_div={fixed_gate_div}, pat_variants={len(pat_list)}, offsets={rotation_offsets}", flush=True)

        # 전체 길이를 4~8바 청크로 연속 렌더링 (seed 기반 변동)
        bar_dur = (60.0 / bpm) * 4  # 4/4 1바 길이
        chunk_bars = 4 + (self._ep_seed % 3) * 2  # 4, 6, 8 중 하나 (최소 4바 보장)
        chunk_dur = bar_dur * chunk_bars
        bar_counter = 0
        t = 0.0

        # v14: 웨이브테이블 + 필터 + 동적 drive
        _wt = make_wavetable(self.seq_config.saw_harmonics)
        _cutoff = self.seq_config.filter_cutoff_base
        # SI 기반 drive: si 낮으면 1.5(클린), si 높으면 4.5(거침)
        _drive_base = 1.5

        while t < self.duration:
            pat_idx = (bar_counter // chunk_bars) % len(pat_list)
            pattern = pat_list[pat_idx]

            this_chunk_dur = min(chunk_dur, self.duration - t)
            if this_chunk_dur < 0.05:
                break

            # v14: SI 기반 drive 동적 조절
            t_mid = t + this_chunk_dur / 2
            _si_idx = max(0, min(int(t_mid * self.sr), self.total_samples - 1))
            _si_val = float(self._si_env[_si_idx]) if self._si_env is not None else 0.5
            _drive = _drive_base + _si_val * 3.0  # 1.5 ~ 4.5

            chunk_L = saw_sequence(self.bass_freq, this_chunk_dur, pattern,
                                   gate_div=fixed_gate_div, note_len_ratio=fixed_note_len,
                                   bpm=bpm, distort=True, sr=self.sr,
                                   wt=_wt, drive=_drive, cutoff_hz=_cutoff)
            chunk_R = saw_sequence(self.bass_freq * 1.003, this_chunk_dur, pattern,
                                   gate_div=fixed_gate_div, note_len_ratio=fixed_note_len,
                                   bpm=bpm, distort=True, sr=self.sr,
                                   wt=_wt, drive=_drive, cutoff_hz=_cutoff)

            # 청크 페이드 (크로스페이드)
            fade_s = min(int(0.03 * self.sr), len(chunk_L) // 4)
            if fade_s > 0:
                chunk_L[:fade_s] *= np.linspace(0, 1, fade_s)
                chunk_R[:fade_s] *= np.linspace(0, 1, fade_s)
                chunk_L[-fade_s:] *= np.linspace(1, 0, fade_s)
                chunk_R[-fade_s:] *= np.linspace(1, 0, fade_s)

            abs_start = int(t * self.sr)
            abs_end = min(abs_start + len(chunk_L), self.total_samples)
            chunk_len = abs_end - abs_start
            if chunk_len > 0:
                saw_L[abs_start:abs_end] += chunk_L[:chunk_len]
                saw_R[abs_start:abs_end] += chunk_R[:chunk_len]

            t += this_chunk_dur
            bar_counter += chunk_bars

        # 섹션별 볼륨 모핑
        vol_env = smooth_envelope(
            self.total_samples, sections, "saw_sequence", "volume",
            default=0.7, morph_sec=1.5, sr=self.sr  # v12: 0.8→1.5 (섹션 전환 부드럽게)
        )
        # F-7: 콜앤리스폰스 멜로디 엔벨로프
        cr_m = self._cr_melody_env[:self.total_samples] if hasattr(self, '_cr_melody_env') else 1.0
        saw_L *= vol_env * cr_m  # v16: si_gate 제거
        saw_R *= vol_env * cr_m

        # v14: 코러스로 스테레오 풍부함 추가
        saw_L = chorus(saw_L, sr=self.sr, depth_ms=self.seq_config.chorus_depth_ms)
        saw_R = chorus(saw_R, sr=self.sr, depth_ms=self.seq_config.chorus_depth_ms, lfo_rate=1.7)

        # v22: bit_crush — lo-fi 이펙트 (acid/IDM/glitch)
        music_mood = self.script.get("metadata", {}).get("music_mood", "acid")
        if music_mood in ("acid", "IDM", "glitch"):
            avg_si = float(np.mean(self._si_env)) if self._si_env is not None else 0.5
            bits = max(6, int(12 - avg_si * 6))  # si=0→12bit(클린), si=1→6bit(거침)
            saw_L = bit_crush(saw_L, bits=bits, downsample=2)
            saw_R = bit_crush(saw_R, bits=bits, downsample=2)
            print(f"  [saw_seq] v22 bit_crush: {bits}bit (si={avg_si:.2f})", flush=True)

        # v16: 페이드 제거
        self.master_L += saw_L
        self.master_R += saw_R

    def _render_continuous_gate_stutter(self, sections):
        """v9: 게이트 + 유클리드 리듬 + 스터터 — 대본 데이터 직접 연동

        대본 데이터 매핑:
          semantic_intensity → 게이트 분할 속도 (4/8/16분음표)
          data_density       → 스터터 밀도 + 조각 길이
          numbers            → 유클리드 리듬 패턴 선택

        결과: 같은 감정(tension)이라도 대본마다 리듬 패턴이 달라짐
        """
        print("  [gate_stutter] continuous gate+euclidean+stutter...", flush=True)
        bpm = self.script.get("metadata", {}).get("base_bpm", 120)
        sd_segments = self._script_data.get("segments", []) if self._script_data else []

        gate_L = np.zeros(self.total_samples)
        gate_R = np.zeros(self.total_samples)

        for sec in sections:
            start_s = int(sec["start_sec"] * self.sr)
            end_s = min(int(sec["end_sec"] * self.sr), self.total_samples)
            dur = (end_s - start_s) / self.sr
            if dur < 0.1:
                continue

            seg_idx = sec.get("_segment_index")
            # 대본 데이터에서 파라미터 추출
            si = 0.5
            data_density = 0.3
            numbers = []
            if sd_segments and seg_idx is not None and seg_idx < len(sd_segments):
                seg = sd_segments[seg_idx]
                analysis = seg.get("analysis", {})
                si = analysis.get("semantic_intensity", 0.5)
                data_density = analysis.get("data_density", 0.3)
                numbers = [abs(n) for n in analysis.get("numbers", []) if abs(n) > 0]
            else:
                # script_data 없으면 감정/에너지에서 추정
                si = sec.get("energy", 0.5)
                data_density = si * 0.6

            # ── 게이트 엔벨로프 (si 기반 속도) ──
            gate_env = gate_pattern_from_si(si, bpm, dur, self.sr)

            # ── 유클리드 리듬으로 게이트 마스킹 (numbers 기반) ──
            if numbers:
                euclid = numbers_to_euclidean(numbers, steps=16)
                beat_sec = 60.0 / bpm
                step_samples = int(self.sr * beat_sec * 4 / 16)
                if step_samples > 0:
                    euclid_env = np.zeros(end_s - start_s)
                    for i, hit in enumerate(euclid * (len(gate_env) // (step_samples * len(euclid)) + 1)):
                        s_pos = i * step_samples
                        if s_pos >= len(euclid_env):
                            break
                        e_pos = min(s_pos + step_samples, len(euclid_env))
                        euclid_env[s_pos:e_pos] = 1.0 if hit else 0.2
                    gate_env = gate_env[:len(euclid_env)] * euclid_env

            # ── 파형 혼합 소스 생성 (si + data_density 기반) ──
            # si 낮음: sine(clean) → saw → distorted saw → si 높음: saw+square(brutal)
            gate_len = len(gate_env)
            freq_L = self.bass_freq * 2
            freq_R = self.bass_freq * 2 * 1.004
            dur_sec = gate_len / self.sr

            if si < 0.3:
                # 낮은 긴장감: 사인파 베이스 (clean, 부드러운 펄스)
                src_L = sine(freq_L, dur_sec, self.sr) * 0.5
                src_R = sine(freq_R, dur_sec, self.sr) * 0.5
            elif si < 0.55:
                # 중간: 쏘우파 (raw, 날카로움)
                src_L = sawtooth(freq_L, dur_sec, self.sr)
                src_R = sawtooth(freq_R, dur_sec, self.sr)
            elif si < 0.75:
                # 긴장: 쏘우파 + 중간 디스토션
                drive = 2.5 + data_density * 3.0  # 2.5~5.5
                src_L = sawtooth_distorted(freq_L, dur_sec, drive=drive, sr=self.sr)
                src_R = sawtooth_distorted(freq_R, dur_sec, drive=drive, sr=self.sr)
            else:
                # 고강도: 쏘우파 + 스퀘어파 혼합 + 강한 디스토션
                drive = 4.5 + data_density * 4.0  # 4.5~8.5 (brutal)
                saw_L = sawtooth_distorted(freq_L, dur_sec, drive=drive, sr=self.sr)
                saw_R = sawtooth_distorted(freq_R, dur_sec, drive=drive, sr=self.sr)
                sq_duty = 0.25 + data_density * 0.25  # 0.25~0.5 (날카로울수록 좁은 듀티)
                sq_L = chiptune_square(freq_L * 0.5, dur_sec, duty=sq_duty, sr=self.sr) * 0.4
                sq_R = chiptune_square(freq_R * 0.5, dur_sec, duty=sq_duty, sr=self.sr) * 0.4
                blend = (si - 0.75) / 0.25  # 0→1 as si goes 0.75→1.0
                src_L = saw_L + sq_L * blend
                src_R = saw_R + sq_R * blend

            # 배열 길이 맞추기
            min_len = min(len(src_L), gate_len)
            gated_L = src_L[:min_len] * gate_env[:min_len]
            gated_R = src_R[:min_len] * gate_env[:min_len]

            # ── 스터터 (data_density 기반 조각 반복) ──
            if data_density > 0.2:
                gated_L = stutter_from_data(gated_L, data_density, numbers, self.sr)
                gated_R = stutter_from_data(gated_R, data_density, numbers, self.sr)

            chunk_len = end_s - start_s
            actual_len = min(chunk_len, len(gated_L), len(gated_R))
            gate_L[start_s:start_s + actual_len] += gated_L[:actual_len]
            gate_R[start_s:start_s + actual_len] += gated_R[:actual_len]

        # 섹션별 볼륨 + si 게이트
        vol_env = smooth_envelope(
            self.total_samples, sections, "gate_stutter", "volume",
            default=0.35, morph_sec=0.5, sr=self.sr
        )
        gate_L *= vol_env  # v16: si_gate 제거
        gate_R *= vol_env

        # v16: 페이드 제거
        self.master_L += gate_L
        self.master_R += gate_R

    def _render_gap_stutter_burst(self):
        """무음 구간(나레이션 세그먼트 사이)에 쏘우 스터터 버스트 삽입 (v9)

        나레이션이 없는 짧은 gap에서 오히려 자극적인 쏘우+스퀘어 버스트를 발사.
        대비 효과: 나레이션 있을 때는 음악 흐름, gap에서는 날카로운 임팩트.

        조건:
          - gap_dur >= 30ms (너무 짧으면 스킵)
          - 에너지: 이전+다음 세그먼트 SI 평균 → drive 결정
          - 파형: 쏘우 + 스퀘어 혼합, drive=5.0~10.0 (항상 brutal)
          - 게이트: si=1.0 기준 32분음표 (최대 스터터)
        """
        if not self._script_data:
            return

        segments = self._script_data.get("segments", [])
        if len(segments) < 2:
            return

        bpm = self.script.get("metadata", {}).get("base_bpm", 120)
        burst_L = np.zeros(self.total_samples)
        burst_R = np.zeros(self.total_samples)
        gap_count = 0

        for i in range(len(segments) - 1):
            gap_start_sec = segments[i].get("end_sec", 0)
            gap_end_sec = segments[i + 1].get("start_sec", 0)
            gap_dur = gap_end_sec - gap_start_sec

            if gap_dur < 0.03:  # 30ms 미만 스킵
                continue

            gap_start = int(gap_start_sec * self.sr)
            gap_end = min(int(gap_end_sec * self.sr), self.total_samples)
            actual_gap = gap_end - gap_start
            if actual_gap <= 0:
                continue

            # 에너지: 이전+다음 세그먼트 SI 평균
            prev_si = segments[i].get("analysis", {}).get("semantic_intensity", 0.5)
            next_si = segments[i + 1].get("analysis", {}).get("semantic_intensity", 0.5)
            burst_energy = (prev_si + next_si) / 2

            # 쏘우파 + 디스토션 (v10.1: drive 완화, 5~10→2~3.5)
            drive = 2.0 + burst_energy * 1.5  # 2.0~3.5 (이전: 5.0~10.0)
            freq_L = self.bass_freq * 2
            freq_R = self.bass_freq * 2 * 1.006  # 약간 detuned (stereo width)

            saw_L = sawtooth_distorted(freq_L, gap_dur, drive=drive, sr=self.sr)
            saw_R = sawtooth_distorted(freq_R, gap_dur, drive=drive, sr=self.sr)

            # 스퀘어파 혼합 (gap에서는 항상 추가)
            sq_duty = 0.3 + burst_energy * 0.2  # 0.3~0.5
            sq_L = chiptune_square(freq_L * 0.5, gap_dur, duty=sq_duty, sr=self.sr) * 0.5
            sq_R = chiptune_square(freq_R * 0.5, gap_dur, duty=sq_duty, sr=self.sr) * 0.5

            src_L = saw_L + sq_L
            src_R = saw_R + sq_R

            # 32분음표 게이트 (si=1.0 → 최대 스터터 속도)
            gate_env = gate_pattern_from_si(1.0, bpm, gap_dur, self.sr)

            min_len = min(len(src_L), len(gate_env), actual_gap)
            gated_L = src_L[:min_len] * gate_env[:min_len]
            gated_R = src_R[:min_len] * gate_env[:min_len]

            # 5ms 빠른 fade in/out (클릭 방지)
            fade_len = min(int(0.005 * self.sr), min_len // 4)
            if fade_len > 1:
                gated_L[:fade_len] *= np.linspace(0, 1, fade_len)
                gated_R[:fade_len] *= np.linspace(0, 1, fade_len)
                gated_L[-fade_len:] *= np.linspace(1, 0, fade_len)
                gated_R[-fade_len:] *= np.linspace(1, 0, fade_len)

            # 볼륨: 에너지 비례 (v10.1: 0.25~0.45, 이전: 0.5~0.85)
            vol = 0.25 + burst_energy * 0.2

            burst_L[gap_start:gap_start + min_len] = gated_L * vol
            burst_R[gap_start:gap_start + min_len] = gated_R * vol
            gap_count += 1

        if gap_count:
            print(f"  [gap_burst] {gap_count} gaps filled with saw+stutter", flush=True)

        self.master_L += burst_L
        self.master_R += burst_R

    # ---- 텍스처 악기: 섹션 단위 (자연스럽게 등장/퇴장) ----

    def _render_section_textures(self, section):
        """섹션별 텍스처 악기 렌더링 (클릭, 글리치, 쉬머, 스윕, 리드, 애시드)

        v7-P5 + F-8: 텍스처 기여분에 fade-in/fade-out 적용 → 섹션 간 크로스페이드
        F-8: fade duration을 늘리고 raised cosine 블렌드로 더 부드러운 전환
        """
        start = section["start_sec"]
        dur = section["end_sec"] - section["start_sec"]
        if dur <= 0:
            return
        instruments = section.get("instruments", {})
        effects = section.get("effects", {})
        stereo_width = effects.get("stereo_width", 0.5)

        # F-8: 크로스페이드 영역 확장 — 텍스처 렌더 전 마스터 버퍼 스냅샷
        sec_start_sample = int(self.sr * start)
        sec_end_sample = min(int(self.sr * section["end_sec"]), self.total_samples)
        snapshot_L = self.master_L[sec_start_sample:sec_end_sample].copy()
        snapshot_R = self.master_R[sec_start_sample:sec_end_sample].copy()

        # si 기반 밀도 변조 (Problem 1): 텍스처 악기의 density를 si에 비례 조정
        seg_idx = section.get("_segment_index")
        si_density_mod = 1.0
        if self._script_data and seg_idx is not None:
            segments = self._script_data.get("segments", [])
            if seg_idx < len(segments):
                si = segments[seg_idx].get("semantic_intensity", 0.5)
                si_density_mod = 0.5 + si  # si=0→0.5배, si=0.5→1.0배, si=1→1.5배

        # Clicks
        clicks_cfg = instruments.get("clicks", {})
        if clicks_cfg.get("active"):
            density = clicks_cfg.get("density", 0.3) * si_density_mod
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
            density = glitch_cfg.get("density", 0.3) * si_density_mod
            glitch_signal = glitch_texture(dur, density, self.sr)
            glitch_signal = fade_in(fade_out(glitch_signal, min(dur * 0.3, 1.0)), min(dur * 0.2, 0.5))
            self._add_stereo(glitch_signal, 0.4 * stereo_width, start, 0.5)

        # Noise Burst
        burst_cfg = instruments.get("noise_burst", {})
        if burst_cfg.get("active"):
            density = burst_cfg.get("density", 0.3) * si_density_mod
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
            density = metal_cfg.get("density", 0.2) * si_density_mod
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

        # Saw Sequence (v9: 쏘우파 게이트 시퀀서 — 섹션별 텍스처 레이어)
        # _render_continuous_saw_sequence()가 전체 버퍼를 채우지만,
        # EMOTION_MAP에서 활성화된 섹션에 추가 레이어(고음역 카운터멜로디)를 덧씌움
        saw_cfg = instruments.get("saw_sequence", {})
        if saw_cfg.get("active"):
            vol = saw_cfg.get("volume", 0.5)
            bpm_sec = self._section_bpm(section)
            # 고음역 카운터멜로디 패턴 (메인보다 1옥타브 위)
            hi_pattern = [2, 2, 3, 1.5, 2, 2.667, 2, 1.5]
            energy = section.get("energy", 0.5)
            gate_div = 16 if energy >= 0.7 else 8
            hi_saw = saw_sequence(self.bass_freq * 2, dur, hi_pattern,
                                  gate_div=gate_div, note_len_ratio=0.55,
                                  bpm=bpm_sec, distort=True, sr=self.sr)
            hi_saw = fade_in(fade_out(hi_saw, min(dur * 0.2, 0.3)), min(dur * 0.1, 0.1))
            self._add_stereo(hi_saw, 0.3, start, vol * 0.6)

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
                    # v14: 웨이브테이블 + 동적 vibrato
                    _lead_wt = make_wavetable(self.seq_config.saw_harmonics)
                    note = synth_lead(freq, actual_dur, self.sr,
                                      wt=_lead_wt, vibrato_depth=0.008,
                                      cutoff_hz=self.seq_config.filter_cutoff_base * 1.5)
                    self._add_stereo(note, -0.15, start + t_note, vol)
                t_note += note_dur * 1.1  # 약간의 갭
                note_idx += 1

        # Acid Bass (새 악기)
        acid_cfg = instruments.get("acid_bass", {})
        if acid_cfg.get("active"):
            vol = acid_cfg.get("volume", 0.4)
            sweep_dir = acid_cfg.get("sweep_dir", "down")
            # BPM 동기화 베이스라인 (v7-P6: 섹션별 가변 BPM)
            beat_interval = 60.0 / self._section_bpm(section)
            note_dur = beat_interval * 0.8
            t_note = 0.0
            bass_pattern = acid_cfg.get("pattern", [1, 1, 1.5, 0.75, 1, 1.333])
            note_idx = 0
            while t_note < dur:
                freq = self.bass_freq * bass_pattern[note_idx % len(bass_pattern)]
                actual_dur = min(note_dur, dur - t_note)
                if actual_dur > 0.05:
                    ab = acid_bass(freq, actual_dur, sweep_dir, self.sr,
                                   cutoff_hz=self.seq_config.filter_cutoff_base)
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
                gate_signal = stutter_gate(gate_signal, self._section_bpm(section), divisions, self.sr)  # v7-P6
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
            bb_signal, bb_raw = bytebeat(formula_id, dur, self.sr, return_raw=True)
            bb_signal = fade_in(fade_out(bb_signal, min(dur * 0.2, 0.5)), min(dur * 0.15, 0.3))
            self._add_stereo(bb_signal, random.uniform(-0.3, 0.3), start, vol)
            # 원본 값 수집 (비주얼 엔진용)
            s = int(self.sr * start)
            e = min(s + len(bb_raw), self.total_samples)
            self._bytebeat_raw[s:e] = bb_raw[:e - s]

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
            beat_interval = 60.0 / self._section_bpm(section)  # v7-P6
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

        # === Ikeda: Data Click (대본 숫자 기반 정밀 클릭) ===
        dc_cfg = instruments.get("data_click", {})
        if dc_cfg.get("active"):
            vol = dc_cfg.get("volume", 0.5)
            # script_data에서 현재 세그먼트의 숫자 추출
            click_freqs = dc_cfg.get("frequencies", [440])
            density = dc_cfg.get("density", 0.5)

            # script_data가 로딩되어 있으면 세그먼트 데이터 사용
            seg_idx = section.get("_segment_index")
            if self._script_data and seg_idx is not None:
                segments = self._script_data.get("segments", [])
                if seg_idx < len(segments):
                    seg_data = segments[seg_idx]
                    numbers = seg_data.get("analysis", {}).get("numbers", [])
                    if numbers:
                        click_freqs = []
                        for n in numbers:
                            if n > 20:
                                click_freqs.append(n)
                            elif n > 0:
                                click_freqs.append(round(1.0 / n, 2))
                    density = seg_data.get("analysis", {}).get("data_density", 0.5)

            if not click_freqs:
                click_freqs = [440]

            interval = max(0.03, 0.3 / max(density, 0.01))
            t_click = 0.0
            freq_idx = 0
            while t_click < dur:
                freq = click_freqs[freq_idx % len(click_freqs)]
                click = data_click(freq, self.sr)
                pan = random.uniform(-0.6, 0.6)
                self._add_stereo(click, pan, start + t_click, vol)
                # 비주얼 데이터: 클릭 위치 기록
                click_sample = int(self.sr * (start + t_click))
                if 0 <= click_sample < self.total_samples:
                    self._data_click_positions[click_sample] = 1.0
                t_click += random.uniform(interval * 0.7, interval * 1.3)
                freq_idx += 1

        # F-8: 텍스처 크로스페이드 — raised cosine으로 더 부드러운 전환
        fade_duration = min(1.0, dur * 0.20)  # F-8: 0.5→1.0초, 15%→20% (더 넉넉한 크로스페이드)
        fade_samples = int(fade_duration * self.sr)
        seg_len = sec_end_sample - sec_start_sample
        if fade_samples > 0 and seg_len > 2 * fade_samples:
            delta_L = self.master_L[sec_start_sample:sec_end_sample] - snapshot_L
            delta_R = self.master_R[sec_start_sample:sec_end_sample] - snapshot_R

            # F-8: raised cosine (linear → cosine) — 더 자연스러운 에너지 전환
            fade_in_env = 0.5 * (1 - np.cos(np.linspace(0, np.pi, fade_samples)))
            fade_out_env = 0.5 * (1 + np.cos(np.linspace(0, np.pi, fade_samples)))
            delta_L[:fade_samples] *= fade_in_env
            delta_R[:fade_samples] *= fade_in_env
            delta_L[-fade_samples:] *= fade_out_env
            delta_R[-fade_samples:] *= fade_out_env

            self.master_L[sec_start_sample:sec_end_sample] = snapshot_L + delta_L
            self.master_R[sec_start_sample:sec_end_sample] = snapshot_R + delta_R

    def load_script_data(self, script_data_path):
        """script_data.json 로딩"""
        import os
        if script_data_path and os.path.exists(script_data_path):
            with open(script_data_path, 'r', encoding='utf-8') as f:
                self._script_data = json.load(f)
            print(f"  Script data loaded: {script_data_path}")
            # F-6: highlight_words → accent times 빌드
            self._build_accent_times()

    def _build_accent_times(self):
        """F-6: script_data 세그먼트에서 highlight_words 포함 세그먼트의 시작 시간 추출"""
        if not self._highlight_words or not self._script_data:
            return
        segments = self._script_data.get("segments", [])
        accent_set = set()
        for seg in segments:
            text = seg.get("text", "")
            for hw in self._highlight_words:
                if hw in text:
                    t = seg.get("start_sec", None)
                    if t is not None:
                        accent_set.add(round(t, 3))
                    break
        self._accent_times = sorted(accent_set)
        if self._accent_times:
            print(f"  [F-6] Accent times: {len(self._accent_times)} hits for {self._highlight_words}")

    def _script_data_enrichment(self, sections):
        """script_data로 섹션별 악기 파라미터를 장르에 맞게 풍부화 (v7-P3)

        enometa는 기존 로직(data_click freq) 유지.
        나머지 5개 장르: 숫자/키워드/바이트 데이터를 악기 파라미터에 매핑.
        """
        if not self._script_data:
            return

        genre = self.script.get("metadata", {}).get("genre", "default")
        sd_segments = self._script_data.get("segments", [])
        formula_keys = list(BYTEBEAT_FORMULAS.keys())
        enriched = 0

        for section in sections:
            seg_idx = section.get("_segment_index")
            if seg_idx is None or seg_idx >= len(sd_segments):
                continue

            seg = sd_segments[seg_idx]
            analysis = seg.get("analysis", {})
            numbers = analysis.get("numbers", [])
            si = analysis.get("semantic_intensity", 0.5)
            data_density = analysis.get("data_density", 0.5)
            instruments = section.get("instruments", {})

            if genre == "techno":
                # 숫자 → synth_lead 멜로디 패턴 비율
                lead = instruments.get("synth_lead")
                if lead and lead.get("active") and numbers:
                    ratios = [max(0.5, min(abs(n) / 100, 4.0)) for n in numbers[:6]]
                    if ratios:
                        lead["pattern"] = ratios
                        enriched += 1
                # data_density → click density 가산
                clicks = instruments.get("clicks")
                if clicks and clicks.get("active"):
                    clicks["density"] = clicks.get("density", 0.3) * (0.7 + data_density * 0.6)
                    enriched += 1

            elif genre == "bytebeat":
                # 숫자 합 → bytebeat formula 선택
                bb = instruments.get("bytebeat")
                if bb and bb.get("active") and numbers:
                    idx = int(abs(sum(numbers))) % len(formula_keys)
                    bb["formula"] = formula_keys[idx]
                    enriched += 1

            elif genre == "algorave":
                # data_density → metallic_hit density 가산
                metal = instruments.get("metallic_hit")
                if metal and metal.get("active"):
                    metal["density"] = metal.get("density", 0.2) * (0.6 + data_density * 0.8)
                    enriched += 1

            elif genre == "harsh_noise":
                # si → feedback gain/iterations 변조
                fb = instruments.get("feedback")
                if fb and fb.get("active"):
                    fb["gain"] = min(0.5 + si * 0.4, 0.95)  # 0.5~0.95
                    fb["iterations"] = 4 + int(si * 8)  # 4~12
                    enriched += 1

            elif genre == "chiptune":
                # 숫자 → chiptune_lead 멜로디 패턴 비율
                chip = instruments.get("chiptune_lead")
                if chip and chip.get("active") and numbers:
                    ratios = [max(0.5, min(abs(n) / 50, 3.0)) for n in numbers[:8]]
                    if ratios:
                        chip["pattern"] = ratios
                        enriched += 1

            # enometa는 기존 data_click 로직 유지 (이미 _render_section_textures에서 처리)

        if enriched > 0:
            print(f"  [script_data] {genre}: enriched {enriched} instrument params", flush=True)

    def _build_si_envelope(self) -> np.ndarray:
        """script_data의 semantic_intensity → 시간 도메인 변조 엔벨로프 (Problem 1)

        script_data.segments[].semantic_intensity (0~1)를 시간 배열로 변환.
        0.5초 cumsum 스무딩으로 세그먼트 간 자연스러운 전환.
        script_data 없으면 0.5(neutral)로 채움.
        """
        si_env = np.full(self.total_samples, 0.5)

        if not self._script_data:
            return si_env

        segments = self._script_data.get("segments", [])
        for seg in segments:
            analysis = seg.get("analysis", {})
            si = analysis.get("semantic_intensity", seg.get("semantic_intensity", 0.5))
            start_sample = int(seg.get("start_sec", seg.get("start", 0)) * self.sr)
            end_sample = int(seg.get("end_sec", seg.get("end", 0)) * self.sr)
            start_sample = max(0, min(start_sample, self.total_samples))
            end_sample = max(0, min(end_sample, self.total_samples))
            si_env[start_sample:end_sample] = si

        # 0.5초 cumsum 스무딩 (계단식 전환 방지)
        window = int(0.5 * self.sr)
        if window > 1 and len(si_env) > window:
            cumsum = np.cumsum(si_env)
            cumsum = np.insert(cumsum, 0, 0)
            smoothed = (cumsum[window:] - cumsum[:-window]) / window
            pad_left = window // 2
            pad_right = self.total_samples - len(smoothed) - pad_left
            si_env = np.concatenate([
                np.full(pad_left, smoothed[0]),
                smoothed,
                np.full(max(pad_right, 0), smoothed[-1])
            ])[:self.total_samples]

        return si_env

    # ── v18 장르 시스템 ──────────────────────────────────────────────────
    # 9개 실존 언더그라운드 전자음악 장르
    # acid(TB-303), microsound(Ikeda/Noto), IDM(Aphex/Autechre),
    # dub(Basic Channel), industrial(Perc/Ansome)
    # + ambient, minimal, glitch, techno (유지)
    _MOOD_DRUM_DEFAULT = {
        "ambient": False, "microsound": False, "IDM": True,
        "minimal": True,  "dub": True,         "glitch": True,
        "acid": True,     "industrial": True,  "techno": True,
        "house": True,
    }
    # ── v19: 장르별 레이어 스펙 (Vertical Remixing) ─────────────────────────
    # required = 항상 ON (장르 정체성)
    # optional_pool = seed가 N개 선택 (에피소드별 변형)
    # optional_count = (min, max) 선택 개수
    # 볼륨: (min, max) 튜플이면 seed가 범위 내 결정, 스칼라면 고정
    # inactive = 항상 OFF (장르에서 절대 안 쓰는 레이어)
    # extra = 추가 파라미터 (density, formula 등)
    _GENRE_SPECS = {
        "ambient": {
            "required": {
                "bass_drone":   {"volume": (0.7, 0.9)},   # 깊은 드론 = ambient 정체성
            },
            "optional_pool": {
                "sine_interference": {"volume": (0.4, 0.7)},
                "pulse_train":       {"volume": (0.4, 0.7)},
                "arpeggio":          {"volume": (0.4, 0.6)},
                "fm_bass":           {"volume": (0.4, 0.6)},
                "saw_sequence":      {"volume": (0.3, 0.5)},
            },
            "optional_count": (2, 3),
            "inactive": ["kick", "snare", "hi_hat", "data_click", "ultrahigh_texture",
                         "stutter_gate", "gap_burst", "glitch", "bytebeat"],
        },
        "microsound": {
            "required": {
                "data_click":        {"volume": (1.2, 1.6)},   # Ikeda 클릭 = 정체성
                "ultrahigh_texture":  {"volume": (0.8, 1.0)},   # 디지털 공기
            },
            "optional_pool": {
                "sine_interference": {"volume": (0.3, 0.5)},
                "pulse_train":       {"volume": (0.5, 0.8)},
                "stutter_gate":      {"volume": (0.5, 0.8)},
                "arpeggio":          {"volume": (0.3, 0.5)},
                "modular_clicks":    {"volume": (0.5, 0.8)},   # v22: 모듈러 클릭
            },
            "optional_count": (1, 2),
            "inactive": ["kick", "snare", "hi_hat", "saw_sequence", "bass_drone",
                         "glitch", "bytebeat", "gap_burst"],
        },
        "IDM": {
            "required": {
                "kick":          {"volume": (0.6, 0.8)},
                "snare":         {"volume": (0.4, 0.6)},
                "stutter_gate":  {"volume": (0.6, 0.8)},   # 글리치 리듬 = IDM 정체성
            },
            "optional_pool": {
                "hi_hat":            {"volume": (0.3, 0.5)},   # 불규칙 하이햇
                "saw_sequence":      {"volume": (0.4, 0.6)},
                "arpeggio":          {"volume": (0.5, 0.8)},
                "glitch":            {"volume": (0.5, 0.7), "extra": {"density": 0.7}},
                "bytebeat":          {"volume": (0.4, 0.6)},
                "fm_bass":           {"volume": (0.4, 0.6)},
                "ultrahigh_texture": {"volume": (0.3, 0.5)},
                "modular_clicks":    {"volume": (0.4, 0.7)},   # v22: 모듈러 클릭
            },
            "optional_count": (3, 4),
            "inactive": ["bass_drone", "gap_burst"],
        },
        "minimal": {
            "required": {
                "fm_bass":   {"volume": (0.7, 0.9)},   # 미니멀 FM 베이스 = 정체성
                "kick":      {"volume": (0.4, 0.6)},
            },
            "optional_pool": {
                "hi_hat":            {"volume": (0.3, 0.5)},   # 희소 하이햇
                "bass_drone":        {"volume": (0.5, 0.7)},
                "arpeggio":          {"volume": (0.5, 0.7)},
                "sine_interference": {"volume": (0.3, 0.5)},
                "pulse_train":       {"volume": (0.3, 0.5)},
                "saw_sequence":      {"volume": (0.3, 0.5)},
            },
            "optional_count": (2, 3),
            "inactive": ["snare", "glitch", "bytebeat", "gap_burst",
                         "data_click", "ultrahigh_texture"],
        },
        "dub": {
            "required": {
                "bass_drone":   {"volume": (0.8, 1.0)},   # 딥 서브 = dub 정체성
                "kick":         {"volume": (0.6, 0.8)},
                "chord_stab":   {"volume": (0.6, 0.8)},   # 코드 스탭 = dub 정체성
                "tape_delay":   {"volume": 1.0, "extra": {"feedback": (0.5, 0.75)}},
            },
            "optional_pool": {
                "hi_hat":            {"volume": (0.3, 0.5)},   # dub 하이햇 (희소)
                "snare":             {"volume": (0.3, 0.5)},
                "sine_interference": {"volume": (0.3, 0.6)},
                "arpeggio":          {"volume": (0.3, 0.5)},
                "pulse_train":       {"volume": (0.3, 0.5)},
            },
            "optional_count": (1, 2),
            "inactive": ["saw_sequence", "glitch", "bytebeat",
                         "data_click", "ultrahigh_texture", "gap_burst"],
        },
        "glitch": {
            "required": {
                "kick":          {"volume": (0.7, 0.9)},
                "snare":         {"volume": (0.5, 0.7)},
                "glitch":        {"volume": (0.8, 1.0), "extra": {"density": (0.5, 0.8)}},
                "stutter_gate":  {"volume": (0.8, 1.0)},   # 글리치 = 정체성
            },
            "optional_pool": {
                "bytebeat":          {"volume": (0.5, 0.7), "extra": {"formula": "glitch"}},
                "gap_burst":         {"volume": (0.8, 1.0)},
                "data_click":        {"volume": (0.7, 1.0)},
                "ultrahigh_texture": {"volume": (0.4, 0.6)},
                "saw_sequence":      {"volume": (0.3, 0.5)},
                "modular_clicks":    {"volume": (0.6, 0.9)},   # v22: 모듈러 클릭
            },
            "optional_count": (2, 3),
            "inactive": ["hi_hat", "arpeggio", "bass_drone", "fm_bass"],  # 글리치가 대신
        },
        "acid": {
            "required": {
                "kick":         {"volume": (0.8, 1.0)},
                "snare":        {"volume": (0.7, 0.9)},
                "hi_hat":       {"volume": (0.4, 0.6)},   # 808/909 하이햇 = acid 필수
                "acid_bass":    {"volume": (0.8, 1.0)},   # TB-303 = acid 정체성
                "saw_sequence": {"volume": (0.8, 1.0)},
            },
            "optional_pool": {
                "arpeggio":          {"volume": (0.5, 0.8)},
                "fm_bass":           {"volume": (0.4, 0.6)},
                "stutter_gate":      {"volume": (0.4, 0.6)},
                "ultrahigh_texture": {"volume": (0.3, 0.5)},
            },
            "optional_count": (1, 2),
            "inactive": ["bass_drone", "glitch", "bytebeat", "gap_burst",
                         "data_click"],
        },
        "industrial": {
            "required": {
                "kick":            {"volume": (0.9, 1.0)},
                "snare":           {"volume": (0.9, 1.0)},
                "saw_sequence":    {"volume": (0.9, 1.0)},
                "distorted_kick":  {"volume": (0.7, 0.9)},   # 디스토션 킥 = industrial 정체성
            },
            "optional_pool": {
                "hi_hat":            {"volume": (0.4, 0.6)},   # industrial 하이햇
                "ultrahigh_texture": {"volume": (0.6, 0.9)},
                "feedback_loop":     {"volume": (0.5, 0.8)},
                "gap_burst":         {"volume": (0.7, 1.0)},
                "stutter_gate":      {"volume": (0.6, 0.8)},
                "fm_bass":           {"volume": (0.5, 0.7)},
            },
            "optional_count": (2, 3),
            "inactive": ["arpeggio", "bass_drone", "glitch", "bytebeat",
                         "data_click"],
        },
        "techno": {
            "required": {
                "kick":         {"volume": (0.9, 1.0)},   # 4-on-the-floor = techno 정체성
                "snare":        {"volume": (0.6, 0.8)},
                "hi_hat":       {"volume": (0.5, 0.7)},   # 클로즈드 하이햇 = techno 필수
                "saw_sequence": {"volume": (0.8, 1.0)},
            },
            "optional_pool": {
                "arpeggio":          {"volume": (0.6, 0.9)},
                "fm_bass":           {"volume": (0.5, 0.8)},
                "ultrahigh_texture": {"volume": (0.4, 0.7)},
                "stutter_gate":      {"volume": (0.4, 0.6)},
                "bass_drone":        {"volume": (0.3, 0.5)},
            },
            "optional_count": (2, 3),
            "inactive": ["glitch", "bytebeat", "gap_burst", "data_click"],
        },
        "house": {
            "required": {
                "kick":         {"volume": (0.8, 1.0)},   # 4-on-the-floor = house 정체성
                "hi_hat":       {"volume": (0.5, 0.7)},   # 오프비트 하이햇 = house 필수
                "rhodes_pad":   {"volume": (0.6, 0.8)},   # Rhodes 코드 = deep house 정체성
                "bass_drone":   {"volume": (0.6, 0.8)},   # 깊은 서브베이스
            },
            "optional_pool": {
                "snare":             {"volume": (0.5, 0.7)},   # 2, 4박 스네어
                "chord_stab":        {"volume": (0.4, 0.6)},   # dub 분위기 코드 추가
                "arpeggio":          {"volume": (0.4, 0.6)},   # 하이 아르페지오
                "fm_bass":           {"volume": (0.4, 0.6)},   # FM 베이스 레이어
                "sine_interference": {"volume": (0.2, 0.4)},   # 배경 사인파 질감
            },
            "optional_count": (2, 3),
            "inactive": ["saw_sequence", "acid_bass", "distorted_kick", "glitch",
                         "bytebeat", "data_click", "ultrahigh_texture", "gap_burst",
                         "stutter_gate"],
        },
    }

    @staticmethod
    def _generate_mood_layers(genre: str, ep_seed: int) -> dict:
        """v19: seed 기반 Vertical Remixing — 같은 장르라도 에피소드마다 다른 레이어 조합.

        Returns: _MOOD_LAYERS 형식 dict (기존 소비 코드와 100% 호환)
        """
        import random as _rng_mod
        specs = EnometaMusicEngine._GENRE_SPECS
        spec = specs.get(genre, specs["acid"])
        rng = _rng_mod.Random(ep_seed)
        layers = {}

        def _resolve_vol(vol_spec):
            """볼륨: 튜플이면 seed 범위 선택, 스칼라면 고정."""
            if isinstance(vol_spec, tuple):
                return round(rng.uniform(vol_spec[0], vol_spec[1]), 2)
            return vol_spec

        def _resolve_extra(extra_spec):
            """extra 파라미터: 튜플이면 seed 범위 선택."""
            if not extra_spec:
                return {}
            resolved = {}
            for k, v in extra_spec.items():
                resolved[k] = round(rng.uniform(v[0], v[1]), 2) if isinstance(v, tuple) else v
            return resolved

        # 1. 필수 레이어 — 항상 ON
        for name, cfg in spec["required"].items():
            entry = {"active": True, "volume": _resolve_vol(cfg["volume"])}
            entry.update(_resolve_extra(cfg.get("extra")))
            layers[name] = entry

        # 2. 선택 레이어 — seed가 풀에서 N개 선택
        pool_names = list(spec["optional_pool"].keys())
        count_min, count_max = spec["optional_count"]
        n = rng.randint(count_min, min(count_max, len(pool_names)))
        chosen = rng.sample(pool_names, n)
        for name in chosen:
            cfg = spec["optional_pool"][name]
            entry = {"active": True, "volume": _resolve_vol(cfg["volume"])}
            entry.update(_resolve_extra(cfg.get("extra")))
            layers[name] = entry

        # 3. 비활성 레이어 — 항상 OFF
        for name in spec.get("inactive", []):
            if name not in layers:
                layers[name] = {"active": False}

        # 4. 선택풀에 있었지만 뽑히지 않은 것도 OFF
        for name in pool_names:
            if name not in layers:
                layers[name] = {"active": False}

        return layers

    # 기존 _MOOD_LAYERS는 fallback + 호환용으로 유지 (신규 코드는 _generate_mood_layers 사용)
    _MOOD_LAYERS = {
        "acid": {"kick": {"active": True, "volume": 0.9}, "snare": {"active": True, "volume": 0.8},
                 "saw_sequence": {"active": True, "volume": 1.0}, "arpeggio": {"active": True, "volume": 0.7},
                 "acid_bass": {"active": True, "volume": 0.9}},
    }
    _GAP_FILL_INTENSITY = {
        "ambient": 0.0, "microsound": 0.3, "IDM": 1.0,
        "minimal": 0.2, "dub": 0.3,        "glitch": 0.8,
        "acid": 0.6,    "industrial": 0.9, "techno": 0.7,
    }

    # ── 장르별 BPM 범위 ──────────────────────────────────────────────────────
    # ep_seed로 범위 내에서 결정론적 선택 → 장르별 템포 캐릭터 확보
    MOOD_BPM_RANGES = {
        "ambient":      (60,  72),   # very slow, spacious (60-72 BPM)
        "microsound":   (85, 100),   # precise, data-driven (Ikeda/Alva Noto)
        "house":        (118, 126),  # Deep House sweet spot (Larry Heard/Larry Heard)
        "minimal":      (118, 126),  # steady, hypnotic
        "dub":          (110, 125),  # deep, spacious (Basic Channel)
        "IDM":          (100, 155),  # wide range, unpredictable (Aphex/Autechre)
        "glitch":       (95,  155),  # intentionally wide = instability
        "acid":         (126, 138),  # TB-303 sweet spot
        "industrial":   (138, 155),  # fast, aggressive (Perc/Ansome)
        "techno":       (128, 138),  # 4-on-the-floor sweet spot
        "house":        (118, 126),  # Deep House sweet spot
    }

    # ── 장르별 유클리드 드럼 패턴 ─────────────────────────────────────────────
    # (pulses, steps): euclidean_rhythm(steps, pulses) → 장르 DNA
    # None = 해당 파트 seq_config 기본값 유지
    MOOD_RHYTHM_PRESETS = {
        "house":        {"kick": (4, 16), "snare": (2, 16), "hihat": (8, 16)},  # 4-on-the-floor + 오프비트 하이햇
        "techno":       {"kick": (4, 16), "snare": (2, 16), "hihat": (8, 16)},
        "glitch":       {"kick": (5, 16), "snare": (3, 11), "hihat": (11, 16)},
        "minimal":      {"kick": (3, 16), "snare": None,    "hihat": (5, 12)},
        "dub":          {"kick": (3, 16), "snare": (2, 16), "hihat": (4, 16)},
        "industrial":   {"kick": (4, 12), "snare": (3, 16), "hihat": (7,  8)},
        "IDM":          {"kick": (5, 12), "snare": (3,  8), "hihat": (9, 16)},
        "acid":         None,   # seq_config 기본값 — 클래식 808/909 패턴
        "ambient":      {"kick": None,    "snare": None,    "hihat": None},
        "microsound":   {"kick": None,    "snare": None,    "hihat": (3, 16)},
    }

    # ── 장르별 킥 캐릭터 ─────────────────────────────────────────────────────
    # 0=tight(단단), 1=boomy(울림), 2=punchy(어택)
    MOOD_KICK_CHARACTER = {
        "house":        1,   # boomy — 깊고 따뜻한 Deep House 킥 (Roland TR-909 스타일)
        "techno":       2,   # punchy — 믹스 관통
        "glitch":       0,   # tight — 짧고 클릭
        "minimal":      0,   # tight
        "dub":          1,   # boomy — 둥글고 깊은
        "industrial":   2,   # punchy — distorted_kick과 레이어링
        "IDM":          0,   # tight — 복잡 패턴에 어울리는 짧은 킥
        "acid":         2,   # punchy — 909 킥
        "ambient":      1,   # boomy
        "microsound":   0,   # tight — 데이터 클릭과 혼합
    }

    def apply_mood_to_sections(self, sections: list, mood: str, drum_mode: str = "default"):
        """v19: seed 기반 Vertical Remixing + drum_mode 4종으로 섹션별 instrument 적용."""
        # v19: 동적 레이어 생성 (캐시 재사용)
        if self._mood_layers_cache is None:
            self._mood_layers_cache = self._generate_mood_layers(mood, self._ep_seed)
            active_names = [k for k, v in self._mood_layers_cache.items() if v.get("active")]
            print(f"  [v19 Vertical Remixing] genre={mood}, seed={self._ep_seed}, active={active_names}", flush=True)
        mood_layers = self._mood_layers_cache
        drum_layers = {"kick", "snare", "hi_hat"}

        # drum_mode별 활성화 결정
        if drum_mode == "off":
            drum_on, snare_on = False, False
        elif drum_mode == "on":
            drum_on, snare_on = True, True
        elif drum_mode == "simple":
            drum_on, snare_on = True, True   # 베이직 4/4 루프 — 킥+하이햇+스네어 전부 ON (고정 패턴은 렌더러에서)
        elif drum_mode == "dynamic":
            drum_on, snare_on = True, True
        else:  # "default"
            drum_on = self._MOOD_DRUM_DEFAULT.get(mood, True)
            snare_on = drum_on

        print(f"  [mood] {mood}+{drum_mode}: drum={'ON' if drum_on else 'OFF'}, snare={'ON' if snare_on else 'OFF'}", flush=True)

        for section in sections:
            instruments = section.setdefault("instruments", {})
            for layer_name, config in mood_layers.items():
                if layer_name == "snare":
                    instruments[layer_name] = dict(config, active=snare_on and config.get("active", True))
                elif layer_name in drum_layers:  # kick, hi_hat
                    instruments[layer_name] = dict(config, active=drum_on and config.get("active", True))
                else:
                    instruments[layer_name] = dict(config)
            section["_drum_mode"] = drum_mode  # 렌더러 참조용

        return sections

    def _insert_gap_events(self, drops: list, mood: str = "acid"):
        """v15: drops[] 구간에 무드별 강도로 gap_burst/stutter/impact 삽입."""
        intensity = self._GAP_FILL_INTENSITY.get(mood, 0.5)
        if not drops or intensity == 0:
            return
        bpm = float(self.bpm)
        spb = (60.0 / bpm) * 4  # SEC_PER_BAR
        print(f"  [gap_events] {len(drops)} drops, mood={mood}, intensity={intensity:.1f}", flush=True)
        for drop in drops:
            start_sample = int(drop["start_sec"] * self.sr)
            end_sample = min(int(drop["end_sec"] * self.sr), self.total_samples)
            duration = drop["end_sec"] - drop["start_sec"]
            if start_sample >= self.total_samples:
                continue
            # 1마디 이상: gap_burst
            if duration >= spb and intensity >= 0.3:
                burst_dur = min(spb * 0.5, 0.4)
                burst = noise(burst_dur, self.sr)
                burst = lowpass(burst, 3000, self.sr)
                burst = fade_in(fade_out(burst, burst_dur * 0.5), 0.01)
                burst *= intensity * 0.4
                end_b = min(start_sample + len(burst), self.total_samples)
                length = end_b - start_sample
                self.master_L[start_sample:end_b] += burst[:length]
                self.master_R[start_sample:end_b] += burst[:length]
            # 2마디 이상: 중간 stutter
            if duration >= spb * 2 and intensity >= 0.5:
                mid_sample = (start_sample + end_sample) // 2
                mid_sample = min(mid_sample, self.total_samples - self.sr)
                stutter_len = int(0.1 * self.sr)
                if mid_sample + stutter_len <= self.total_samples:
                    src = self.master_L[mid_sample:mid_sample + stutter_len].copy()
                    for rep in range(3):
                        pos = mid_sample + rep * stutter_len
                        end_r = min(pos + stutter_len, self.total_samples)
                        length = end_r - pos
                        vol = (1.0 - rep * 0.3) * intensity * 0.3
                        self.master_L[pos:end_r] += src[:length] * vol
                        self.master_R[pos:end_r] += src[:length] * vol
            # 3마디 이상 + 강도 높음: impact
            if duration >= spb * 3 and intensity >= 0.7:
                impact_start = max(0.0, drop["end_sec"] - 0.05)
                impact = transition_impact(self.sr)
                impact *= intensity * 0.5
                pos = int(impact_start * self.sr)
                end_p = min(pos + len(impact), self.total_samples)
                length = end_p - pos
                self.master_L[pos:end_p] += impact[:length]
                self.master_R[pos:end_p] += impact[:length]

    # ─────────────────────────────────────────────────────────────────────

    def generate(self) -> np.ndarray:
        """music_script.json의 모든 섹션을 1곡으로 렌더링"""
        sections = self.script.get("sections", [])
        total = len(sections)
        overrides = self.script.get("metadata", {}).get("synthesis_overrides", {})
        is_enometa = overrides.get("enometa_mode", False)
        arc_name = self.script.get("metadata", {}).get("song_arc", "narrative")
        print(f"  Rendering {total} sections as one continuous track...", flush=True)
        print(f"  Song arc: {arc_name} ({SONG_ARC_PRESETS.get(arc_name, {}).get('description', '?')})", flush=True)

        # semantic_intensity 엔벨로프 사전 빌드 (adaptive arc가 참조하므로 arc 전에 빌드)
        self._si_env = self._build_si_envelope()
        self._si_modulation = 0.95 + self._si_env * 0.05  # v16: ±5% 이내 — 음악 연속성 최우선, ARRANGEMENT_TABLE이 에너지 주도
        self._si_gate = self._build_si_gate()  # v7-P8: 연속 악기 si 게이트
        self._tempo_curve = self._compute_tempo_curve()  # v7-P6: 가변 BPM 곡선
        if self._script_data:
            print(f"  SI modulation: range {self._si_modulation.min():.2f}~{self._si_modulation.max():.2f}", flush=True)
            gate_min = float(self._si_gate.min())
            if gate_min < 1.0:
                print(f"  SI gate: min={gate_min:.2f} (quiet sections detected)", flush=True)
            tempo_min, tempo_max = float(self._tempo_curve.min()), float(self._tempo_curve.max())
            if abs(tempo_max - tempo_min) > 0.5:
                print(f"  Tempo curve: {tempo_min:.1f}~{tempo_max:.1f} BPM (±{(tempo_max-tempo_min)/2/self.bpm*100:.1f}%)", flush=True)

        # v7-P3: script_data로 섹션별 악기 파라미터 풍부화 (전장르)
        self._script_data_enrichment(sections)

        # v16: SI 기반 레이어 밀도 제어 제거 — ARRANGEMENT_TABLE 볼륨이 유일한 소스
        # 음악 연속성을 위해 섹션별 볼륨 변조 최소화
        print(f"  [v16] Layer density: ARRANGEMENT_TABLE only (SI modulation at master level)", flush=True)

        # Song Arc 사전 계산 (adaptive arc는 위의 si_env를 사용)
        self._song_arc_env = self._compute_song_arc(arc_name)
        self._song_arc_name = arc_name

        # F-7: 콜앤리스폰스 엔벨로프 사전 계산
        # v16: 콜앤리스폰스 비활성 — 볼륨 고정 원칙 (마디별 감쇠 제거)
        self._cr_drum_env = np.ones(self.total_samples, dtype=np.float64)
        self._cr_melody_env = np.ones(self.total_samples, dtype=np.float64)

        # v18: 장르 기반 레이어 ON/OFF 적용 (drum_mode 4종)
        music_mood = self.script.get("metadata", {}).get("music_mood", "acid")
        # 하위호환: 이전 무드 이름 → 새 장르 이름 자동 변환
        _LEGACY_MOOD_MAP = {"raw": "acid", "ikeda": "microsound", "experimental": "IDM", "chill": "dub", "intense": "industrial"}
        music_mood = _LEGACY_MOOD_MAP.get(music_mood, music_mood)
        drum_mode = self.script.get("metadata", {}).get("drum_mode", "default")
        # 하위호환: 기존 drum_override bool → drum_mode 자동 변환
        if drum_mode == "default":
            drum_override = self.script.get("metadata", {}).get("drum_override", None)
            if drum_override is True:
                drum_mode = "on"
            elif drum_override is False:
                drum_mode = "off"
        self._drum_mode = drum_mode  # 렌더러에서 참조용

        # v17: 무드별 킥 캐릭터 오버라이드 (seq_config 기본값 덮어쓰기)
        kick_char = self.MOOD_KICK_CHARACTER.get(music_mood)
        if kick_char is not None:
            self.seq_config.kick_character = kick_char
            print(f"  [mood] kick_character → {kick_char} ({['tight','boomy','punchy'][kick_char]})", flush=True)

        if music_mood and music_mood != "acid":
            self.apply_mood_to_sections(sections, music_mood, drum_mode)
        elif drum_mode != "default":
            # acid 장르에서도 drum_mode 적용
            self.apply_mood_to_sections(sections, "acid", drum_mode)

        if is_enometa:
            # v19: seed 기반 Vertical Remixing — 같은 장르라도 에피소드마다 다른 레이어 조합
            if self._mood_layers_cache is None:
                self._mood_layers_cache = self._generate_mood_layers(music_mood or "acid", self._ep_seed)
                active_names = [k for k, v in self._mood_layers_cache.items() if v.get("active")]
                print(f"  [v19 Vertical Remixing] genre={music_mood}, seed={self._ep_seed}, active={active_names}", flush=True)
            _mood_cfg = self._mood_layers_cache
            def _layer_on(name, default=True):
                return _mood_cfg.get(name, {}).get("active", default)
            # 레이어 1: 리듬 뼈대 (킥 + 하이햇) — 항상 실행 (drum_mode가 off면 내부에서 처리)
            self._render_continuous_rhythm(sections)
            # 레이어 2: 쏘우파 게이트 시퀀서
            if _layer_on("saw_sequence"):
                self._render_continuous_saw_sequence(sections)
            else:
                print("  [saw_seq] SKIPPED (mood layer off)", flush=True)
            # 레이어 3: 아르페지오
            if _layer_on("arpeggio"):
                self._render_continuous_arpeggio(sections)
            else:
                print("  [arp] SKIPPED (mood layer off)", flush=True)
            # 레이어 4: 베이스 드론 + 서브
            if _layer_on("bass_drone"):
                self._render_continuous_bass(sections)
            else:
                print("  [bass] SKIPPED (mood layer off)", flush=True)
            self._render_continuous_sub_pulse(sections)
            # 레이어 5: 텍스처 (사인파 간섭, 펄스, 초고주파)
            if _layer_on("sine_interference"):
                self._render_continuous_sine_interference(sections)
            else:
                print("  [sine_interference] SKIPPED (mood layer off)", flush=True)
            if _layer_on("pulse_train", default=True):
                self._render_continuous_pulse_train(sections)
            else:
                print("  [pulse_train] SKIPPED (mood layer off)", flush=True)
            if _layer_on("ultrahigh_texture"):
                self._render_continuous_ultrahigh(sections)
            else:
                print("  [ultrahigh] SKIPPED (mood layer off)", flush=True)
            # v19: 미구현이었던 dub/industrial 전용 레이어 연결
            if _layer_on("chord_stab", default=False):
                self._render_continuous_chord_stab(sections)
            else:
                print("  [chord_stab] SKIPPED (mood layer off)", flush=True)
            # house 전용: Rhodes 패드
            if _layer_on("rhodes_pad", default=False):
                self._render_continuous_rhodes_pad(sections)
            else:
                print("  [rhodes_pad] SKIPPED (mood layer off)", flush=True)
            if _layer_on("distorted_kick", default=False):
                self._render_continuous_distorted_kick(sections)
            else:
                print("  [distorted_kick] SKIPPED (mood layer off)", flush=True)
            if _layer_on("tape_delay", default=False):
                self._apply_tape_delay_to_master()
            else:
                print("  [tape_delay] SKIPPED (mood layer off)", flush=True)
            # v22: 레이어 8b: 모듈러 클릭 (키워드 이벤트 텍스처)
            if _layer_on("modular_clicks", default=False):
                self._render_continuous_modular_clicks(sections)
            else:
                print("  [modular_clicks] SKIPPED (mood layer off)", flush=True)
            # 레이어 9: 게이트 + 스터터
            if _layer_on("stutter_gate", default=True):
                self._render_continuous_gate_stutter(sections)
            else:
                print("  [gate_stutter] SKIPPED (mood layer off)", flush=True)
            # 레이어 10: 무음 갭 버스트
            if _layer_on("gap_burst", default=True):
                self._render_gap_stutter_burst()
            else:
                print("  [gap_burst] SKIPPED (mood layer off)", flush=True)
            # v15: drops[] 기반 gap_events 삽입 (장르 강도 적용)
            drops = self.script.get("metadata", {}).get("drops", [])
            if drops:
                self._insert_gap_events(drops, music_mood)
        else:
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

        # v16: 볼륨 고정 — song_arc, SI modulation, breath envelope 모두 비활성
        # 음악은 ARRANGEMENT_TABLE 구조 + smooth_envelope만으로 에너지 표현
        print(f"  [v16] Volume: FIXED (no song_arc, no SI modulation, no breath)", flush=True)

        return self._master()

    def _master(self) -> np.ndarray:
        """마스터링 v11: enometa 마스터링 체인 — tanh(1.5) + RMS -6dB + 페이드"""
        print("  Mastering v11 (enometa: saturation + RMS normalize)...", flush=True)
        stereo = np.column_stack([self.master_L, self.master_R])

        # v11: enometa 마스터링 — 부드러운 새츄레이션
        peak = np.max(np.abs(stereo))
        if peak > 0:
            stereo = stereo / peak
        stereo = np.tanh(stereo * 1.5)  # v10.1: 새츄레이션 완화 (3.0→1.5, 너무 정신없음 피드백)

        # RMS 타겟 -6dB (0.5 linear) — v10: 더 큰 음악 볼륨 (이전: -10dB 0.316)
        rms = np.sqrt(np.mean(stereo ** 2))
        target_rms = 0.5  # -6dB
        if rms > 0:
            gain = target_rms / rms
            stereo *= gain

        # 피크 리미팅 (0.95 ceiling)
        peak2 = np.max(np.abs(stereo))
        if peak2 > 0.95:
            stereo *= 0.95 / peak2

        # v22: tape_stop — 아웃로 피치다운 (마지막 0.5초)
        tape_stop_dur = 0.5
        tape_stop_samp = min(int(self.sr * tape_stop_dur), len(stereo) // 4)
        if tape_stop_samp > 100:
            for ch in range(2):
                stereo[:, ch] = tape_stop(stereo[:, ch], stop_duration=tape_stop_dur, sr=self.sr)
            print(f"  [master] v22 tape_stop: {tape_stop_dur}s ending", flush=True)

        # v16: 마스터 페이드 제거 — 음악은 즉시 시작, 즉시 끝남
        # 클릭 방지용 anti-click (5ms — 앨리어싱 방지)
        anti_click = min(int(self.sr * 0.005), len(stereo) // 4)
        if anti_click > 1:
            for ch in range(2):
                stereo[:anti_click, ch] *= np.linspace(0, 1, anti_click)
                stereo[-anti_click:, ch] *= np.linspace(1, 0, anti_click)

        # 4) 16bit WAV
        audio_16bit = (stereo * 32767).astype(np.int16)
        return audio_16bit

    # ============================================================
    # F-5: 호흡 엔벨로프 — 미시적 에너지 딥
    # ============================================================

    def _compute_breath_envelope(self) -> np.ndarray:
        """8~16바 주기의 미시적 호흡: 바 단위 에너지 딥(dip)

        Song arc(매크로)와 보완하는 미시적 에너지 변조.
        매 8바의 7번째 바: 85%, 매 16바의 15번째 바: 70% (큰 호흡).
        0.3초 스무딩으로 계단 제거.
        """
        breath = np.ones(self.total_samples, dtype=np.float64)
        bar_dur = (60.0 / self.bpm) * 4  # 4/4 1바 (기본 BPM 기준)
        bar_samples = max(1, int(bar_dur * self.sr))
        total_bars = self.total_samples // bar_samples

        for bar in range(total_bars):
            start = bar * bar_samples
            end = min(start + bar_samples, self.total_samples)

            # v16: 호흡 깊이 완화 (음악 연속성 보호)
            # 매 16바의 15번째: 가벼운 호흡 (0.90)
            if bar % 16 == 14:
                breath[start:end] = 0.90
            # 매 8바의 7번째: 미세 호흡 (0.95)
            elif bar % 8 == 6:
                breath[start:end] = 0.95

        # 0.3초 cumsum 스무딩 (계단 → 부드러운 곡선)
        window = int(0.3 * self.sr)
        if window > 1 and self.total_samples > window:
            cumsum = np.cumsum(breath)
            cumsum = np.insert(cumsum, 0, 0)
            smoothed = (cumsum[window:] - cumsum[:-window]) / window
            pad_left = window // 2
            pad_right = self.total_samples - len(smoothed) - pad_left
            breath = np.concatenate([
                np.full(pad_left, smoothed[0]),
                smoothed,
                np.full(max(0, pad_right), smoothed[-1])
            ])[:self.total_samples]

        return breath

    def _compute_call_response_envelopes(self) -> tuple:
        """F-7: 콜앤리스폰스 — 드럼/멜로디 교대 gain 엔벨로프

        2바 주기로 드럼↔멜로디 gain이 교대:
        - 홀수 2바 그룹: 드럼 100%, 멜로디 75%
        - 짝수 2바 그룹: 드럼 75%, 멜로디 100%
        SI 0.3~0.7 구간에서만 활성 (극단값은 교대 불필요).
        """
        drum_env = np.ones(self.total_samples, dtype=np.float64)
        melody_env = np.ones(self.total_samples, dtype=np.float64)
        bar_dur = (60.0 / self.bpm) * 4
        bar_samples = max(1, int(bar_dur * self.sr))
        total_bars = self.total_samples // bar_samples

        for bar in range(total_bars):
            start = bar * bar_samples
            end = min(start + bar_samples, self.total_samples)

            # SI 체크: 해당 바 중앙의 SI
            mid_idx = min((start + end) // 2, self.total_samples - 1)
            si_val = float(self._si_env[mid_idx]) if self._si_env is not None else 0.5

            # SI 0.3~0.7 에서만 활성
            if 0.3 <= si_val <= 0.7:
                group = (bar // 2) % 2  # 0 또는 1
                if group == 0:
                    # 드럼 강조, 멜로디 절제
                    drum_env[start:end] = 1.0
                    melody_env[start:end] = 0.75
                else:
                    # 멜로디 강조, 드럼 절제
                    drum_env[start:end] = 0.75
                    melody_env[start:end] = 1.0

        # 0.2초 스무딩
        window = int(0.2 * self.sr)
        if window > 1 and self.total_samples > window:
            for env in [drum_env, melody_env]:
                cumsum = np.cumsum(env)
                cumsum = np.insert(cumsum, 0, 0)
                smoothed = (cumsum[window:] - cumsum[:-window]) / window
                pad_left = window // 2
                pad_right = self.total_samples - len(smoothed) - pad_left
                result = np.concatenate([
                    np.full(pad_left, smoothed[0]),
                    smoothed,
                    np.full(max(0, pad_right), smoothed[-1])
                ])[:self.total_samples]
                env[:] = result

        return drum_env, melody_env

    # Song Arc — 기승전결 매크로 에너지 엔벨로프
    # ============================================================

    def _compute_song_arc(self, arc_name: str = "narrative") -> np.ndarray:
        """매크로 에너지 엔벨로프 생성 — 기승전결 곡 구조

        섹션별 smooth_envelope 위에 곱해지는 상위 에너지 곡선.
        intro(조용) → buildup(성장) → climax(최대) → outro(소멸)

        v12: song_structure 모드 — sections의 role energy에서 직접 arc 생성.
        adaptive 모드: si 곡선에서 내러티브 구조를 자동 추출.

        Returns:
            np.ndarray: total_samples 길이, 0.0~1.5 범위
        """
        # v12: song_structure arc — sections의 role energy에서 직접 생성
        if arc_name == "song_structure":
            return self._compute_song_structure_arc()

        # Adaptive arc: si 곡선 기반 동적 phase 생성
        if arc_name == "adaptive":
            if self._si_env is not None and self._script_data:
                return self._compute_adaptive_arc()
            else:
                print("  [adaptive arc] No script_data → fallback to narrative", flush=True)
                arc_name = "narrative"

        arc_preset = SONG_ARC_PRESETS.get(arc_name, SONG_ARC_PRESETS["flat"])
        phases = arc_preset["phases"]

        return self._build_arc_from_phases(phases)

    def _compute_song_structure_arc(self) -> np.ndarray:
        """v12: sections의 role energy에서 직접 Song Arc 생성.

        ARRANGEMENT_TABLE의 role에서 ROLE_ENERGY를 읽어서
        시간축에 매핑. 별도 SONG_ARC_PRESETS 불필요.
        """
        sections = self.script.get("sections", [])
        if not sections:
            return np.ones(self.total_samples, dtype=np.float64)

        duration = self.duration
        phases = []
        for sec in sections:
            start_pct = sec["start_sec"] / duration if duration > 0 else 0
            end_pct = sec["end_sec"] / duration if duration > 0 else 1
            energy = sec.get("energy", 0.5)
            role = sec.get("_role", sec.get("emotion", ""))

            # energy를 arc 범위(0.2~1.2)로 매핑
            arc_low = 0.2 + energy * 0.6    # 0.2 ~ 0.8
            arc_high = 0.3 + energy * 0.9   # 0.3 ~ 1.2

            # role에 따라 에너지 곡선 형태 결정
            if role in ("buildup",):
                # 점진적 상승
                e_range = (arc_low, arc_high)
            elif role in ("drop", "drop2"):
                # 높은 에너지 유지
                e_range = (arc_high, arc_high)
            elif role == "outro":
                # v16: 점진적 하강 — 최저 0.5 (음악이 계속 살아있어야 함)
                e_range = (arc_low, 0.5)
            else:
                # intro/breakdown 등: 완만한 변화
                e_range = (arc_low, arc_high)

            phases.append({
                "name": role,
                "start_pct": min(start_pct, 1.0),
                "end_pct": min(end_pct, 1.0),
                "energy_range": e_range,
                "density_mult": energy,
            })

        roles_str = " → ".join(f"{p['name']}({p['energy_range'][0]:.1f}→{p['energy_range'][1]:.1f})" for p in phases)
        print(f"  [song_structure arc] {roles_str}", flush=True)

        return self._build_arc_from_phases(phases)

    def _build_arc_from_phases(self, phases: list) -> np.ndarray:
        """phase 리스트에서 에너지 엔벨로프를 생성 (공통 로직)"""
        arc_env = np.ones(self.total_samples, dtype=np.float64)

        for phase in phases:
            start_sample = min(int(self.total_samples * phase["start_pct"]), self.total_samples)
            end_sample = min(int(self.total_samples * phase["end_pct"]), self.total_samples)
            actual_length = end_sample - start_sample
            if actual_length <= 0:
                continue

            e_start, e_end = phase["energy_range"]
            arc_env[start_sample:end_sample] = np.linspace(e_start, e_end, actual_length)

        # Smooth transitions between phases (cumsum moving average, 1.5초 window)
        window = int(self.sr * 1.5)
        if window > 1 and len(arc_env) > window:
            cumsum = np.cumsum(arc_env)
            cumsum = np.insert(cumsum, 0, 0)
            smoothed = (cumsum[window:] - cumsum[:-window]) / window
            pad_left = window // 2
            pad_right = self.total_samples - len(smoothed) - pad_left
            arc_env = np.concatenate([
                np.full(pad_left, smoothed[0]),
                smoothed,
                np.full(max(pad_right, 0), smoothed[-1])
            ])[:self.total_samples]

        return arc_env

    def _compute_adaptive_arc(self) -> np.ndarray:
        """semantic_intensity 곡선 기반 적응형 Song Arc

        si 곡선의 매크로 구조를 분석하여 실제 대본의 기승전결에 맞는
        음악 에너지 엔벨로프를 자동 생성한다.

        알고리즘:
        1. si 곡선을 3초 window로 heavy smoothing → 매크로 구조 추출
        2. 글로벌 피크 위치 → 클라이맥스 중심점
        3. 피크 기준으로 intro/buildup/climax/outro 경계 비례 배분
        4. narrative preset과 동일한 에너지 범위를 데이터 기반 경계에 적용
        """
        si = self._si_env.copy()

        # 1. Heavy smoothing (3초 window) — 매크로 내러티브 구조 추출
        window = int(3.0 * self.sr)
        if window > 1 and len(si) > window:
            cumsum = np.cumsum(si)
            cumsum = np.insert(cumsum, 0, 0)
            smoothed = (cumsum[window:] - cumsum[:-window]) / window
            pad_left = window // 2
            pad_right = len(si) - len(smoothed) - pad_left
            si = np.concatenate([
                np.full(pad_left, smoothed[0]),
                smoothed,
                np.full(max(pad_right, 0), smoothed[-1])
            ])[:len(self._si_env)]

        # 2. 글로벌 피크 → 클라이맥스 중심 (30~80% 범위로 클램프)
        peak_idx = int(np.argmax(si))
        n = max(len(si) - 1, 1)
        peak_pct = np.clip(peak_idx / n, 0.30, 0.80)

        # 3. si 다이나믹 레인지 체크 — 변화 폭이 작으면 narrative fallback
        si_range = float(np.max(si) - np.min(si))
        if si_range < 0.08:
            print(f"  [adaptive arc] SI range too flat ({si_range:.3f}) → fallback to narrative", flush=True)
            return self._build_arc_from_phases(SONG_ARC_PRESETS["narrative"]["phases"])

        # 4. 피크 기준 비례 배분
        #    intro: 0 → peak의 앞 25% (최소 5%, 최대 25%)
        #    buildup: intro_end → climax_start
        #    climax: peak 중심 ±8% (최소 10% 폭)
        #    outro: climax_end → 1.0

        intro_end = np.clip(peak_pct * 0.30, 0.05, 0.25)
        climax_start = max(peak_pct - 0.08, intro_end + 0.05)
        climax_end = min(peak_pct + 0.08, 0.95)

        # climax 최소 폭 보장
        if climax_end - climax_start < 0.10:
            center = (climax_start + climax_end) / 2
            climax_start = max(center - 0.05, intro_end + 0.05)
            climax_end = min(center + 0.05, 0.95)

        outro_start = climax_end

        phases = [
            {
                "name": "intro",
                "start_pct": 0.0,
                "end_pct": intro_end,
                "energy_range": (0.25, 0.45),
                "density_mult": 0.5,
            },
            {
                "name": "buildup",
                "start_pct": intro_end,
                "end_pct": climax_start,
                "energy_range": (0.45, 0.85),
                "density_mult": 1.0,
            },
            {
                "name": "climax",
                "start_pct": climax_start,
                "end_pct": climax_end,
                "energy_range": (0.85, 1.2),
                "density_mult": 1.4,
            },
            {
                "name": "outro",
                "start_pct": outro_start,
                "end_pct": 1.0,
                "energy_range": (0.7, 0.15),
                "density_mult": 0.6,
            },
        ]

        # adaptive phases 저장 (export_raw_visual_data에서 _get_arc_phase_at 사용)
        self._adaptive_phases = phases

        print(f"  [adaptive arc] peak={peak_pct:.0%} | "
              f"intro=0-{intro_end:.0%} | buildup={intro_end:.0%}-{climax_start:.0%} | "
              f"climax={climax_start:.0%}-{climax_end:.0%} | outro={outro_start:.0%}-100%",
              flush=True)

        return self._build_arc_from_phases(phases)

    def _get_arc_phase_at(self, time_sec: float, arc_name: str = "narrative") -> str:
        """특정 시간에서의 아크 페이즈 이름 반환"""
        # v12: song_structure arc는 sections에서 직접 role 반환
        if arc_name == "song_structure":
            sections = self.script.get("sections", [])
            for sec in sections:
                if sec["start_sec"] <= time_sec < sec["end_sec"]:
                    return sec.get("_role", sec.get("emotion", "unknown"))
            return sections[-1].get("_role", "outro") if sections else "unknown"
        # adaptive arc는 동적 생성된 phases 사용
        if arc_name == "adaptive" and hasattr(self, "_adaptive_phases"):
            phases = self._adaptive_phases
        else:
            arc_preset = SONG_ARC_PRESETS.get(arc_name, SONG_ARC_PRESETS["flat"])
            phases = arc_preset.get("phases", [])

        if not phases:
            return "constant"

        progress = time_sec / max(self.duration, 0.001)
        for phase in phases:
            if phase["start_pct"] <= progress < phase["end_pct"]:
                return phase["name"]
        return phases[-1]["name"]

    def export_raw_visual_data(self, output_path: str, fps: int = 30):
        """Hybrid Visual Architecture: 음악 엔진의 원본 데이터를 비주얼 엔진에 전달

        프레임별 오디오 청크, bytebeat 원본 값, 섹션별 에너지 등을
        .npz로 압축 저장한다. 비주얼 엔진이 이 데이터를 직접 소비.
        """
        total_frames = int(self.duration * fps)
        samples_per_frame = self.sr // fps
        mono = (self.master_L + self.master_R) * 0.5

        # 프레임별 오디오 청크
        audio_chunks = np.zeros((total_frames, samples_per_frame))
        bytebeat_chunks = np.zeros((total_frames, samples_per_frame))

        for i in range(total_frames):
            s = i * samples_per_frame
            e = min(s + samples_per_frame, self.total_samples)
            length = e - s
            if length > 0:
                audio_chunks[i, :length] = mono[s:e]
                bytebeat_chunks[i, :length] = self._bytebeat_raw[s:e]

        # 섹션별 에너지 → 프레임별 에너지
        sections = self.script.get("sections", [])
        section_energies = np.zeros(total_frames)
        for sec in sections:
            sec_start_frame = int(sec.get("start_sec", 0) * fps)
            sec_end_frame = int(sec.get("end_sec", 0) * fps)
            energy = sec.get("energy", 0.5)
            sec_start_frame = max(0, min(sec_start_frame, total_frames))
            sec_end_frame = max(0, min(sec_end_frame, total_frames))
            section_energies[sec_start_frame:sec_end_frame] = energy

        # 프레임별 RMS 에너지
        frame_rms = np.zeros(total_frames)
        for i in range(total_frames):
            chunk = audio_chunks[i]
            frame_rms[i] = np.sqrt(np.mean(chunk ** 2)) if np.any(chunk) else 0

        # Ikeda: 사인파 간섭 + 데이터 클릭 비주얼 데이터
        sine_interference_chunks = np.zeros((total_frames, samples_per_frame))
        data_click_frames = np.zeros(total_frames)  # 프레임당 클릭 유무 boolean
        for i in range(total_frames):
            s = i * samples_per_frame
            e = min(s + samples_per_frame, self.total_samples)
            length = e - s
            if length > 0:
                sine_interference_chunks[i, :length] = self._sine_interference_raw[s:e]
                data_click_frames[i] = 1.0 if np.any(self._data_click_positions[s:e] > 0) else 0.0

        meta = self.script.get("metadata", {})

        # Song Arc: 프레임별 에너지 + 페이즈
        arc_name = getattr(self, "_song_arc_name", "flat")
        arc_energy_frames = np.zeros(total_frames, dtype=np.float64)
        arc_phase_frames = np.empty(total_frames, dtype="U10")  # max 10 chars

        if hasattr(self, "_song_arc_env") and arc_name != "flat":
            for i in range(total_frames):
                t = i / fps
                sample_idx = int(t * self.sr)
                sample_idx = min(sample_idx, len(self._song_arc_env) - 1)
                arc_energy_frames[i] = self._song_arc_env[sample_idx]
                arc_phase_frames[i] = self._get_arc_phase_at(t, arc_name)
        else:
            arc_energy_frames[:] = 1.0
            arc_phase_frames[:] = "constant"

        # v7-P6: 프레임별 BPM (가변 tempo curve)
        tempo_curve_frames = np.full(total_frames, float(meta.get("base_bpm", 80)))
        if hasattr(self, '_tempo_curve') and self._tempo_curve is not None:
            for i in range(total_frames):
                sample_idx = min(int((i / fps) * self.sr), len(self._tempo_curve) - 1)
                tempo_curve_frames[i] = self._tempo_curve[sample_idx]

        np.savez_compressed(
            output_path,
            audio_chunks=audio_chunks,
            bytebeat_values=bytebeat_chunks,
            section_energies=section_energies,
            frame_rms=frame_rms,
            sine_interference_values=sine_interference_chunks,
            data_click_positions=data_click_frames,
            arc_energy=arc_energy_frames,
            arc_phases=arc_phase_frames,
            bpm=np.array(meta.get("base_bpm", 80)),
            tempo_curve=tempo_curve_frames,  # v7-P6: per-frame BPM
            genre=np.array(meta.get("genre", "default")),
            arc_name=np.array(arc_name),
            sample_rate=np.array(self.sr),
            fps=np.array(fps),
            total_frames=np.array(total_frames),
        )
        print(f"  Raw visual data: {output_path} ({total_frames} frames)")


# ============================================================
# 감정 → 악기 매핑 테이블 v5: bytebeat/feedback/chiptune_lead/chiptune_drum 추가
# 장르 프리셋이 force_active/force_inactive로 최종 결정하므로 기본값만 배치
# ============================================================

# v12: generate_music_script()에서 더 이상 사용하지 않음.
# ARRANGEMENT_TABLE + _plan_song_structure()가 대체.
# v13: 하드코딩 패턴 제거, sequence_generators.py 사용.
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
        "saw_sequence": {"active": True, "volume": 0.7},  # v9
        "gate_stutter": {"active": True, "volume": 0.4},  # v9
        "sub_pulse": {"active": True, "volume": 0.8},
        "noise_burst": {"active": True, "density": 0.5},
        "bytebeat": {"active": True, "volume": 0.2, "formula": "industrial"},
        "feedback": {"active": False},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": True, "volume": 0.25},
        "pulse_train": {"active": True, "volume": 0.3},
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
        "feedback": {"active": True, "volume": 0.1},  # v8 C-2: enometa 피드백 텍스처
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
        "saw_sequence": {"active": True, "volume": 1.0},  # v9
        "gate_stutter": {"active": True, "volume": 0.6},  # v9
        "sub_pulse": {"active": True, "volume": 1.0},
        "stutter_gate": {"active": True, "divisions": 16, "blend": 0.5},
        "noise_burst": {"active": True, "density": 0.6},
        "bytebeat": {"active": True, "volume": 0.3, "formula": "chaos"},
        "feedback": {"active": True, "volume": 0.15},
        "chiptune_lead": {"active": False},
        "chiptune_drum": {"active": False},
        "pulse_train": {"active": True, "volume": 0.5},
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
        "saw_sequence": {"active": True, "volume": 0.8},  # v9
        "gate_stutter": {"active": True, "volume": 0.5},  # v9
        "sub_pulse": {"active": True, "volume": 0.7},
        "stutter_gate": {"active": True, "divisions": 8, "blend": 0.25},
        "bytebeat": {"active": True, "volume": 0.15, "formula": "cascade"},
        "feedback": {"active": True, "volume": 0.12},
        "chiptune_lead": {"active": True, "volume": 0.3, "duty": 0.25},
        "chiptune_drum": {"active": True, "volume": 0.25},
        "pulse_train": {"active": True, "volume": 0.45},
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
        "pulse_train": {"active": True, "volume": 0.35},
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
        "pulse_train": {"active": True, "volume": 0.2},
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
# v8 C-4: 감정별 사인파 멜로디 시퀀스 — 4마디마다 주파수 쌍 전환
# _render_continuous_sine_interference()에서 사용
# ============================================================

def build_sine_melody_sequences(pad_root: float, scale_offset: int = 0,
                                beat_base: float = 3.0) -> dict:
    """v21: ep_seed 기반 멜로디 다양화.
    scale_offset: 스케일 시작점 회전 (0~6) — 같은 emotion이라도 다른 음정 사용
    beat_base: 맥놀이 기본 주파수 (Hz) — 에피소드마다 다른 비팅 속도
    """
    r = pad_root
    # 스케일 음정 비율 (단조: 1, 9/8, 6/5, 4/3, 3/2, 8/5, 9/5)
    full_scale = [1, 9/8, 6/5, 4/3, 3/2, 8/5, 9/5]
    # scale_offset으로 시작점 회전 → 같은 "ascending"이라도 다른 음에서 시작
    rotated = full_scale[scale_offset:] + full_scale[:scale_offset]
    scale = [r * ratio for ratio in rotated] + [r * rotated[0] * 2]  # 옥타브 추가

    # beat_base로 맥놀이 속도 변조 (기존 고정 3/4/5/7... → beat_base 기반 스케일링)
    b = beat_base
    def bp(f, beat_mult): return (round(f, 1), round(f + b * beat_mult, 1))

    return {
        "ascending":  [bp(scale[0], 1.0), bp(scale[2], 1.3), bp(scale[4], 1.0), bp(scale[6], 1.7)],
        "descending": [bp(scale[6], 1.7), bp(scale[4], 1.0), bp(scale[2], 1.3), bp(scale[0], 1.0)],
        "tension":    [bp(scale[0], 2.3), bp(scale[0], 4.3), bp(scale[0], 6.7), bp(scale[0], 9.0)],
        "release":    [bp(scale[4], 9.0), bp(scale[4], 6.7), bp(scale[4], 4.3), bp(scale[4], 2.3)],
        "neutral":    [bp(scale[0], 1.0), bp(scale[2], 1.0), bp(scale[0], 1.0), bp(scale[2], 1.0)],
    }

# 기본값 (generate_music_script에서 키 선택 후 덮어씌움)
SINE_MELODY_SEQUENCES = build_sine_melody_sequences(329.6)  # E_minor 기본

# 감정 → 시퀀스 매핑
EMOTION_TO_MELODY = {
    "neutral": "neutral", "neutral_curious": "neutral", "neutral_analytical": "neutral",
    "curious": "ascending",
    "somber": "descending", "somber_reflective": "descending", "somber_repetitive": "descending",
    "somber_analytical": "descending", "somber_warning": "tension",
    "tension": "tension", "tension_reveal": "tension", "tension_transformative": "tension",
    "tension_redefine": "tension", "tension_frustrated": "tension", "tension_peak": "tension",
    "awakening_spark": "ascending", "awakening_climax": "ascending", "awakening": "ascending",
    "hopeful": "release", "transcendent": "release", "transcendent_open": "release",
    "fade": "neutral",
}


# ============================================================
# Song Arc 프리셋 — 기승전결 매크로 구조
# 섹션별 smooth_envelope 위에 곱해지는 상위 에너지 엔벨로프
# ============================================================

SONG_ARC_PRESETS = {
    "narrative": {
        "description": "v10: 공격적 기승전결 — intro(active) → buildup(intense) → climax(brutal) → outro(fade)",
        "phases": [
            {
                "name": "intro",
                "start_pct": 0.0,
                "end_pct": 0.12,
                "energy_range": (0.7, 0.9),   # v10: 0.25-0.45 → 0.7-0.9 (intro도 공격적)
                "density_mult": 0.8,
            },
            {
                "name": "buildup",
                "start_pct": 0.12,
                "end_pct": 0.50,
                "energy_range": (0.9, 1.2),   # v10: 0.45-0.85 → 0.9-1.2
                "density_mult": 1.1,
            },
            {
                "name": "climax",
                "start_pct": 0.50,
                "end_pct": 0.80,
                "energy_range": (1.2, 1.5),   # v10: 0.85-1.2 → 1.2-1.5 (브루탈)
                "density_mult": 1.5,
            },
            {
                "name": "outro",
                "start_pct": 0.80,
                "end_pct": 1.0,
                "energy_range": (0.9, 0.2),   # v10: 0.7-0.15 → 0.9-0.2 (더 늦게 떨어짐)
                "density_mult": 0.7,
            },
        ],
    },
    "crescendo": {
        "description": "서서히 성장 — 끝에 최대 에너지",
        "phases": [
            {
                "name": "grow",
                "start_pct": 0.0,
                "end_pct": 0.85,
                "energy_range": (0.2, 1.1),
                "density_mult": 1.0,
            },
            {
                "name": "release",
                "start_pct": 0.85,
                "end_pct": 1.0,
                "energy_range": (1.1, 0.3),
                "density_mult": 0.8,
            },
        ],
    },
    "flat": {
        "description": "균등 에너지 — 기존 동작과 동일 (아크 없음)",
        "phases": [
            {
                "name": "constant",
                "start_pct": 0.0,
                "end_pct": 1.0,
                "energy_range": (1.0, 1.0),
                "density_mult": 1.0,
            },
        ],
    },
    "adaptive": {
        "description": "적응형 — semantic_intensity 곡선에서 내러티브 구조 자동 추출 (script_data 필수, 없으면 narrative fallback)",
        "phases": [],  # 동적 생성 — _compute_adaptive_arc()에서 계산
    },
    # ── D-3b: 추가 arc 프리셋 3종 (v11.2) ──
    "wave": {
        "description": "파동 — 두 개의 피크, 중간에 밸리. 이중 나선 구조(C)에 적합",
        "phases": [
            {
                "name": "rise1",
                "start_pct": 0.0,
                "end_pct": 0.25,
                "energy_range": (0.8, 1.1),
                "density_mult": 1.0,
            },
            {
                "name": "dip",
                "start_pct": 0.25,
                "end_pct": 0.45,
                "energy_range": (1.1, 0.6),
                "density_mult": 0.8,
            },
            {
                "name": "rise2",
                "start_pct": 0.45,
                "end_pct": 0.75,
                "energy_range": (0.6, 1.4),
                "density_mult": 1.3,
            },
            {
                "name": "fade",
                "start_pct": 0.75,
                "end_pct": 1.0,
                "energy_range": (1.0, 0.3),
                "density_mult": 0.6,
            },
        ],
    },
    "shockwave": {
        "description": "충격파 — 강한 시작, 긴 감쇠, 여진. 역순 각성 구조(B)에 적합",
        "phases": [
            {
                "name": "spike",
                "start_pct": 0.0,
                "end_pct": 0.15,
                "energy_range": (1.4, 1.5),
                "density_mult": 1.5,
            },
            {
                "name": "decay",
                "start_pct": 0.15,
                "end_pct": 0.55,
                "energy_range": (1.2, 0.6),
                "density_mult": 0.8,
            },
            {
                "name": "aftershock",
                "start_pct": 0.55,
                "end_pct": 0.75,
                "energy_range": (0.6, 0.9),
                "density_mult": 1.0,
            },
            {
                "name": "settle",
                "start_pct": 0.75,
                "end_pct": 1.0,
                "energy_range": (0.7, 0.2),
                "density_mult": 0.5,
            },
        ],
    },
    "staircase": {
        "description": "계단 — 점진적 4단계 상승. 3단계 변환 구조(A)의 점진형 변형",
        "phases": [
            {
                "name": "step1",
                "start_pct": 0.0,
                "end_pct": 0.25,
                "energy_range": (0.6, 0.7),
                "density_mult": 0.7,
            },
            {
                "name": "step2",
                "start_pct": 0.25,
                "end_pct": 0.50,
                "energy_range": (0.8, 0.9),
                "density_mult": 0.9,
            },
            {
                "name": "step3",
                "start_pct": 0.50,
                "end_pct": 0.75,
                "energy_range": (1.0, 1.2),
                "density_mult": 1.2,
            },
            {
                "name": "step4",
                "start_pct": 0.75,
                "end_pct": 1.0,
                "energy_range": (1.3, 1.0),
                "density_mult": 1.4,
            },
        ],
    },
}


# ============================================================
# 장르 프리셋 v11 — ENOMETA Single Genre: enometa (대본 리액티브 댄스 뮤직)
# 6장르 통합 → enometa 단일 장르 + 패턴 엔진
# ============================================================

GENRE_PRESETS = {
    "enometa": {
        # v12: BPM 135 고정 (가변 BPM 제거 — 한 곡 통일감, 최소 120)
        "bpm_override": 135,
        "volume_scale": {
            # v9: 리듬 레이어 볼륨 정상화 (거의 안 들리던 수준에서 탈출)
            "kick": 0.8,          # 강한 킥
            "hi_hat": 0.8,        # v12: 하이햇 존재감 강화 (0.5→0.8)
            "saw_sequence": 1.0,  # 쏘우파 시퀀서 메인
            "arpeggio": 0.5,      # 아르페지오 서포트
            "bass_drone": 0.4,    # 드론 서브
            "sub_pulse": 0.35,    # 서브 베이스
            # enometa 시그니처 텍스처
            "sine_interference": 0.8,
            "data_click": 0.9,
            "pulse_train": 0.7,
            "ultrahigh_texture": 0.6,
            "clicks": 0.6,
            # 절제된 레이어
            "bytebeat": 0.15,
            "feedback": 0.2,       # B-4: 기본 활성화 (볼륨 상한 0.3)
            "fm_bass": 0.15,       # B-4: 기본 활성화
            "chiptune_lead": 0, "chiptune_drum": 0,
            "synth_lead": 0.15, "acid_bass": 0.4,  # B-4: synth_lead 기본 활성화
        },
        "force_active": [
            "saw_sequence", "sine_interference", "data_click", "pulse_train",
        ],
        # v9: acid_bass + chiptune_lead 허용 (EMOTION_MAP에서 제어)
        "force_inactive": ["chiptune_lead", "chiptune_drum"],  # B-4: fm_bass, synth_lead 제거
        "synthesis_overrides": {
            "enometa_mode": True,
            "rhythm_mode": "euclidean",  # 유클리드 리듬 패턴 유지
        },
        "description": "ENOMETA v11 — 대본 리액티브 댄스 뮤직: 패턴 엔진 + 드럼 뼈대 + build/drop 문법",
    },
}


# ============================================================
# v12: 댄스 음악 편곡 테이블 — 곡 구조 role별 악기 편성
# smooth_envelope과 호환: instruments[key]["active"]=bool, instruments[key]["volume"]=float
# ============================================================

# v16: 볼륨 완전 고정 — 모든 role이 동일한 악기 편성/볼륨
# smooth_envelope이 모핑할 차이가 없으므로 볼륨 변화 0
_FLAT_INSTRUMENTS = {
    "kick": 1.0, "hi_hat": 0.6, "snare": 0.2,
    "saw_sequence": 1.0, "arpeggio": 0.7, "bass_drone": 0.8, "fm_bass": 0.2,
    "sub_pulse": 0.4, "sine_interference": 0.8, "pulse_train": 0.7,
    "ultrahigh_texture": 0.5, "gate_stutter": 0.4,
    "data_click": 0.8, "clicks": 0.6,
    "feedback": 0.15, "bytebeat": 0.15, "synth_lead": 0.15, "acid_bass": 0.4,
    "modular_clicks": 0.5,
}
ARRANGEMENT_TABLE = {
    "intro": dict(_FLAT_INSTRUMENTS),
    "buildup": dict(_FLAT_INSTRUMENTS),
    "drop": dict(_FLAT_INSTRUMENTS),
    "breakdown": dict(_FLAT_INSTRUMENTS),
    "drop2": dict(_FLAT_INSTRUMENTS),
    "outro": dict(_FLAT_INSTRUMENTS),
}

# role별 에너지 (song_arc에 사용)
ROLE_ENERGY = {
    "intro": 0.5, "buildup": 0.8, "drop": 1.0,
    "breakdown": 0.4, "drop2": 1.0, "outro": 0.3,
}

# role별 바 수 비율 (전체 대비). 합계 = 72바 기준
# 짧은 영상(~60초)은 비례 축소, 긴 영상(~140초)은 비례 확대
ROLE_BAR_RATIOS = [
    ("intro",     8),
    ("buildup",  16),
    ("drop",     16),
    ("breakdown", 8),
    ("drop2",    16),
    ("outro",     8),
]


def _plan_song_structure(total_duration: float, bpm: float,
                         climax_time: float = None, outro_time: float = None,
                         mood_layers: dict = None) -> list:
    """v12: 대본 길이와 클라이맥스 시점으로 댄스 음악 구조 자동 생성.

    Args:
        total_duration: 전체 BGM 길이 (초), 엔드카드 포함
        bpm: 고정 BPM
        climax_time: SI 피크 시점 (초). None이면 60% 지점
        outro_time: 아웃트로 시작 시점 (초). None이면 80% 지점

    Returns: sections 리스트 (smooth_envelope 호환 형태)
    """
    bar_dur = (60.0 / bpm) * 4  # 4/4 1바 길이 (초)
    total_bars = int(total_duration / bar_dur)

    # 최소 24바 (약 43초 @135bpm) 보장
    total_bars = max(total_bars, 24)

    # 기준 72바 대비 비례 배분
    base_total = sum(r[1] for r in ROLE_BAR_RATIOS)  # 72
    scale = total_bars / base_total

    # 각 role의 바 수 계산 (최소 4바)
    roles_bars = []
    for role_name, base_bars in ROLE_BAR_RATIOS:
        bars = max(4, round(base_bars * scale / 4) * 4)  # 4바 단위 올림
        roles_bars.append((role_name, bars))

    # 총 바 수 조정 (초과/부족 시 drop/drop2에서 보정)
    actual_total = sum(b for _, b in roles_bars)
    diff = total_bars - actual_total
    if diff != 0:
        # drop2에서 조정 (4바 단위)
        for i, (name, bars) in enumerate(roles_bars):
            if name == "drop2":
                adjusted = max(4, bars + (diff // 4) * 4)
                roles_bars[i] = (name, adjusted)
                break

    # climax_time에 drop을 맞추기 위한 오프셋 계산
    # 단, climax가 영상의 20~70% 구간에 있을 때만 조정 (범위 밖이면 기본 비율 유지)
    if climax_time is not None:
        climax_pct = climax_time / total_duration if total_duration > 0 else 0.5
        if 0.20 <= climax_pct <= 0.70:
            buildup_bars = roles_bars[1][1]
            needed_intro_bars = max(4, round((climax_time - buildup_bars * bar_dur) / bar_dur / 4) * 4)
            # intro가 전체의 40%를 넘지 않도록 제한
            max_intro = max(4, int(total_bars * 0.4 / 4) * 4)
            needed_intro_bars = min(needed_intro_bars, max_intro)
            roles_bars[0] = ("intro", needed_intro_bars)
        else:
            print(f"  [v12] climax at {climax_pct:.0%} — outside 20~70% range, using default ratio")

    # v16: 총 바 수가 target을 초과하지 않도록 강제 축소
    final_total = sum(b for _, b in roles_bars)
    if final_total > total_bars:
        excess = final_total - total_bars
        # 큰 섹션부터 축소 (drop2 → intro → drop → buildup 순)
        for shrink_target in ("drop2", "intro", "drop", "buildup", "breakdown", "outro"):
            for i, (name, bars) in enumerate(roles_bars):
                if name == shrink_target and bars > 4:
                    reduction = min(excess, bars - 4)
                    reduction = (reduction // 4) * 4
                    if reduction > 0:
                        roles_bars[i] = (name, bars - reduction)
                        excess -= reduction
            if excess <= 0:
                break

    # sections 생성 (smooth_envelope 호환 형태)
    sections = []
    t = 0.0
    genre_preset = GENRE_PRESETS["enometa"]
    vol_scale = genre_preset.get("volume_scale", {})

    for role_name, bars in roles_bars:
        start_sec = t
        end_sec = t + bars * bar_dur

        # ARRANGEMENT_TABLE에서 악기 편성 가져와서 smooth_envelope 형태로 변환
        # v19: mood_layers로 장르별 레이어 ON/OFF + 볼륨 적용
        arr = ARRANGEMENT_TABLE[role_name]
        instruments = {}
        for inst_key, vol in arr.items():
            # genre_preset volume_scale 적용
            scaled_vol = vol * vol_scale.get(inst_key, 1.0)

            # v19: mood_layers가 있으면 레이어 활성/비활성 + 볼륨 오버라이드
            if mood_layers and inst_key in mood_layers:
                ml = mood_layers[inst_key]
                if not ml.get("active", False):
                    scaled_vol = 0.0  # 비활성 레이어 → 볼륨 0
                else:
                    # mood_layers 볼륨을 base로, ARRANGEMENT_TABLE 비율로 스케일
                    scaled_vol = ml.get("volume", scaled_vol)

            instruments[inst_key] = {
                "active": scaled_vol > 0.01,
                "volume": round(scaled_vol, 4),
            }

        section = {
            "id": f"music_{role_name}",
            "text": "",
            "start_sec": round(start_sec, 3),
            "end_sec": round(end_sec, 3),
            "emotion": role_name,  # role을 emotion 필드에 저장 (호환)
            "energy": ROLE_ENERGY[role_name],
            "instruments": instruments,
            "effects": {
                "reverb_decay": 0.3 + ROLE_ENERGY[role_name] * 0.3,
                "filter_cutoff": int(200 + ROLE_ENERGY[role_name] * 3000),
                "stereo_width": 0.3 + ROLE_ENERGY[role_name] * 0.5,
            },
            "transition_in": {"type": "crossfade", "duration_sec": 1.0},
            "_role": role_name,  # 원본 role 보존
        }
        sections.append(section)
        t = end_sec

    # 첫 섹션은 fade_in
    if sections:
        sections[0]["transition_in"] = {"type": "fade_in", "duration_sec": 1.0}

    print(f"  [v12] Song structure: {' → '.join(f'{r}({b}bar)' for r, b in roles_bars)}")
    print(f"  [v12] Total: {sum(b for _, b in roles_bars)} bars = {t:.1f}sec (target: {total_duration:.1f}sec)")

    # v19: 활성 레이어 로그
    if mood_layers:
        active = [k for k, v in mood_layers.items() if v.get("active")]
        inactive = [k for k, v in mood_layers.items() if not v.get("active")]
        print(f"  [v19] Active layers ({len(active)}): {', '.join(active)}")
        print(f"  [v19] Inactive layers ({len(inactive)}): {', '.join(inactive)}")

    return sections, t  # sections + 실제 total_duration 반환


# ============================================================
# v7-P7: 음악 키(Key) 프리셋 + 에피소드 이력
# ============================================================

KEY_PRESETS = {
    "C_minor":  {"bass_freq": 65.4, "pad_root": 261.6, "pad_fifth": 392.0, "arp_root": 196.0},
    "D_minor":  {"bass_freq": 73.4, "pad_root": 293.7, "pad_fifth": 440.0, "arp_root": 220.0},
    "E_minor":  {"bass_freq": 82.4, "pad_root": 329.6, "pad_fifth": 493.9, "arp_root": 220.0},
    "F_minor":  {"bass_freq": 87.3, "pad_root": 349.2, "pad_fifth": 523.3, "arp_root": 233.1},
    "G_minor":  {"bass_freq": 98.0, "pad_root": 392.0, "pad_fifth": 587.3, "arp_root": 261.6},
    "A_minor":  {"bass_freq": 110.0, "pad_root": 440.0, "pad_fifth": 659.3, "arp_root": 293.7},
    "Bb_minor": {"bass_freq": 116.5, "pad_root": 466.2, "pad_fifth": 698.5, "arp_root": 311.1},
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


def _quantize_to_bar(time_sec: float, bar_duration: float) -> float:
    """시간을 가장 가까운 마디 경계로 퀀타이즈 (반올림)"""
    if bar_duration <= 0:
        return time_sec
    return round(time_sec / bar_duration) * bar_duration


def generate_music_script(script_data_path: str, visual_script_path: str = None) -> dict:
    """script_data.json(마디 기반) 정보로 음악/오디오 섹션 스크립트를 생성합니다.
    시드 기반 랜덤 확정성 부여 (에피소드 이름/경로 해시 기반)
    visual_script는 선택 사항이며, 카메라 모션을 이용해 텍스처를 더할 수도 있습니다.
    """
    with open(script_data_path, 'r', encoding='utf-8') as f:
        script_data = json.load(f)

    meta = script_data.get("metadata", {})
    episode_id = meta.get("episode", "default")
    
    import hashlib
    import dataclasses
    seed_val = int(hashlib.md5(episode_id.encode()).hexdigest(), 16) % (2**32)
    random.seed(seed_val)
    np.random.seed(seed_val)
    print(f"  [MusicEngine] Fixed seed for episode '{episode_id}': {seed_val}")

    # v18: seq_config 생성 (에피소드 시드 기반 결정론적 음색/패턴)
    from sequence_generators import derive_episode_sequences
    seq_config = derive_episode_sequences(seed_val)

    segments = script_data.get("segments", [])
    total_dur = script_data.get("global", {}).get("total_duration_sec", 60.0)

    # v18: 장르 기반 BPM 선택 (ep_seed 결정론적)
    music_mood = meta.get("music_mood", "acid")
    _LEGACY_MOOD_MAP = {"raw": "acid", "ikeda": "microsound", "experimental": "IDM", "chill": "dub", "intense": "industrial"}
    music_mood = _LEGACY_MOOD_MAP.get(music_mood, music_mood)
    _MOOD_BPM_RANGES = {
        "ambient":      (60,  72),
        "microsound":   (85, 100),
        "house":        (118, 126),
        "minimal":      (118, 126),
        "dub":          (110, 125),
        "IDM":          (100, 155),
        "glitch":       (95,  155),
        "acid":         (126, 138),
        "industrial":   (138, 155),
        "techno":       (128, 138),
    }
    bpm_min, bpm_max = _MOOD_BPM_RANGES.get(music_mood, (124, 138))
    bpm = bpm_min + (seed_val % max(1, bpm_max - bpm_min + 1))
    print(f"  [v17] mood={music_mood} → BPM {bpm} (range {bpm_min}~{bpm_max})")

    base_freq = 60.0
    sections = []

    # v16: BGM = TTS 길이 + 엔드카드(6초) + 버퍼(2초)
    total_dur += 8  # 엔드카드 커버

    # v16: 음악은 TTS 문장 경계와 무관하게 하나의 연속 트랙으로 생성
    # ARRANGEMENT_TABLE 기반 음악적 구조 사용 (intro→buildup→drop→breakdown→drop2→outro)
    si_peak_time = None
    if segments:
        peak_seg = max(segments, key=lambda s: s.get("analysis", {}).get("semantic_intensity", 0))
        si_peak_time = (peak_seg.get("start_sec", 0) + peak_seg.get("end_sec", 0)) / 2

    # v19: 장르별 레이어 조합 생성
    mood_layers = EnometaMusicEngine._generate_mood_layers(music_mood, seed_val)

    sections, actual_dur = _plan_song_structure(
        total_dur, bpm, climax_time=si_peak_time,
        mood_layers=mood_layers
    )
    # v16: BGM 길이는 요청 길이(TTS+엔드카드)로 고정 — 초과 확장 금지
    total_dur = min(total_dur, actual_dur)

    # 세그먼트 인덱스 매핑 (script_data_enrichment 호환)
    for sec in sections:
        t_mid = (sec["start_sec"] + sec["end_sec"]) / 2
        best_idx = 0
        best_dist = float("inf")
        for seg in segments:
            seg_mid = (seg.get("start_sec", 0) + seg.get("end_sec", 0)) / 2
            dist = abs(t_mid - seg_mid)
            if dist < best_dist:
                best_dist = dist
                best_idx = seg.get("index", 0)
        sec["_segment_index"] = best_idx

    # script_data.json metadata에서 music_mood, drum_mode 전달
    music_mood_out = meta.get("music_mood", "acid")
    drum_mode_out = meta.get("drum_mode", "default")

    return {
        "metadata": {
            "duration": total_dur,
            "base_bpm": bpm,
            "episode": episode_id,
            "genre": "enometa",
            "song_arc": "song_structure",  # v16: ARRANGEMENT_TABLE role energy 기반 arc
            "synthesis_overrides": {"enometa_mode": True},
            "music_mood": music_mood_out,
            "drum_mode": drum_mode_out,
            "seq_config": dataclasses.asdict(seq_config),
            # v19: seed 기반 Vertical Remixing 레이어 조합 기록 (재현성)
            "mood_layers": mood_layers,
        },
        "palette": {
            "bass_freq": base_freq,
            "pad_root": base_freq * 2,
            "pad_fifth": base_freq * 3,
            "arp_root": base_freq * 4,
            "arp_pattern": seq_config.arp_pattern,
            "arp_division": seq_config.arp_division
        },
        "sections": sections
    }

# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="ENOMETA Generative Music Engine v12 (Music-First)")
    parser.add_argument("--script-data", required=True, help="script_data.json 경로")
    parser.add_argument("--visual-script", help="visual_script.json 경로 (선택적 텍스처용)")
    parser.add_argument("output", nargs="?", default="audio/bgm.wav", help="출력 WAV 파일 경로")
    parser.add_argument("--export-raw", action="store_true", help="비주얼용 원시 배열 저장 (*_raw_visual_data.npz)")
    args = parser.parse_args()

    script_data_path = args.script_data
    visual_script_path = args.visual_script
    out_path = args.output

    if not os.path.exists(script_data_path):
        print(f"[Error] script_data.json을 찾을 수 없습니다: {script_data_path}")
        sys.exit(1)

    print("=== ENOMETA Music-First Engine v12 ===")
    print(f"Script Data: {script_data_path}")
    if visual_script_path:
        print(f"Visual Script: {visual_script_path}")

    # 1. 스크립트 기반 Music Script 생성
    m_script = generate_music_script(script_data_path, visual_script_path)
    print(f"Generated music script for {len(m_script['sections'])} sections.")

    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    ms_path = os.path.join(out_dir, "music_script.json")
    with open(ms_path, 'w', encoding='utf-8') as f:
        json.dump(m_script, f, ensure_ascii=False, indent=2)
    print(f"Music script saved: {ms_path}")

    print()
    print(f"Duration: {m_script['metadata']['duration']:.1f}s")
    print(f"Base BPM: {m_script['metadata'].get('base_bpm', 135)}")
    print()

    # 2. 엔진 렌더링
    engine = EnometaMusicEngine(m_script)
    engine.load_script_data(script_data_path)  # 시맨틱 데이터 로드
    audio = engine.generate()

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    wavfile.write(out_path, SAMPLE_RATE, audio)
    print()
    print(f"Output: {out_path}")
    print(f"Format: {SAMPLE_RATE}Hz, 16bit, Stereo")

    if args.export_raw:
        raw_path = out_path.replace(".wav", "_raw_visual_data.npz")
        engine.export_raw_visual_data(raw_path)

    print("Done!")


if __name__ == "__main__":
    main()
