"""enometa_music: 기본 합성 함수 + DSP 유틸리티"""

import sys
import os
import json
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter, butter, sosfilt
import random
import math

SAMPLE_RATE = 44100


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
