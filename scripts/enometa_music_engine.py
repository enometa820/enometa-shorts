"""
ENOMETA Generative Music Engine — Pure Python
대본의 감정을 읽고 음악을 생성하는 엔진.
GPU 불필요. numpy + scipy만으로 동작.

사용법:
  python enometa_music_engine.py <music_script.json> [output.wav]
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


# ============================================================
# 악기/사운드 디자인
# ============================================================

def deep_bass_drone(freq, duration, sr=SAMPLE_RATE):
    """딥 베이스 드론 — 존재감, 무게, 공간의 바닥"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * 0.6
    wave += np.sin(2 * np.pi * (freq * 1.002) * t) * 0.3
    wave += np.sin(2 * np.pi * (freq * 0.5) * t) * 0.2
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
    wave = lowpass(wave * lfo, 200)
    return fade_in(fade_out(wave, 2.0), 2.0)


def modular_click(sr=SAMPLE_RATE):
    """모듈러 신스 클릭 — 데이터 포인트, 시간의 틱"""
    duration = 0.08
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    freq = random.uniform(2000, 6000)
    wave = np.sin(2 * np.pi * freq * t)
    env = np.exp(-t * 80)
    wave = wave * env * 0.3
    wave += noise(duration) * np.exp(-t * 120) * 0.1
    return highpass(wave, 800)


def ambient_pad(freq, duration, harmony=None, sr=SAMPLE_RATE):
    """앰비언트 패드 — 공간감, 따뜻함, 각성 (7 voices + sub-octave)"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.zeros_like(t)
    # 7개 디튠 보이스로 확장
    detunes = [0.993, 0.996, 0.998, 1.0, 1.002, 1.004, 1.007]
    for dt in detunes:
        wave += np.sin(2 * np.pi * freq * dt * t) * 0.18

    # 서브옥타브 레이어 (따뜻함 추가)
    wave += np.sin(2 * np.pi * (freq * 0.5) * t) * 0.12
    wave += np.sin(2 * np.pi * (freq * 0.501) * t) * 0.08

    # 하모니 레이어
    if harmony == "root_fifth":
        for dt in detunes:
            wave += np.sin(2 * np.pi * (freq * 1.5) * dt * t) * 0.12
    elif harmony == "root_third":
        for dt in detunes:
            wave += np.sin(2 * np.pi * (freq * 1.2) * dt * t) * 0.1

    # 시간변화 필터 (LFO로 cutoff를 움직여 살아있는 느낌)
    lfo = np.sin(2 * np.pi * 0.05 * t)
    # 청크별 시간변화 로우패스
    chunk_size = int(sr * 0.1)
    result = np.zeros_like(wave)
    for i in range(0, len(wave), chunk_size):
        end = min(i + chunk_size, len(wave))
        mid_t = (i + end) / 2 / sr
        lfo_val = np.sin(2 * np.pi * 0.05 * mid_t)
        cutoff = 600 + 400 * lfo_val  # 200~1000 range
        chunk = wave[i:end]
        if len(chunk) > 12:
            try:
                result[i:end] = lowpass(chunk, cutoff, sr)
            except Exception:
                result[i:end] = chunk
        else:
            result[i:end] = chunk
    result = reverb(result, decay=0.55, delay_ms=130, repeats=10)
    return fade_in(fade_out(result, 3.0), 3.0)


def glitch_texture(duration, density=0.3, sr=SAMPLE_RATE):
    """글리치 텍스처 — 불안, 혼란, 디지털 노이즈"""
    total_samples = int(sr * duration)
    result = np.zeros(total_samples)
    num_events = int(duration * density * 20)
    for _ in range(num_events):
        pos = random.randint(0, max(total_samples - int(sr * 0.05), 1))
        event_len = random.randint(int(sr * 0.001), int(sr * 0.03))
        freq = random.uniform(200, 8000)
        t = np.linspace(0, event_len / sr, event_len, endpoint=False)
        grain = np.sin(2 * np.pi * freq * t) * np.exp(-t * random.uniform(50, 200))
        grain *= random.uniform(0.05, 0.15)
        end = min(pos + event_len, total_samples)
        result[pos:end] += grain[:end - pos]
    return result


def arpeggio_sequence(base_freq, duration, pattern=None, speed=0.2, sr=SAMPLE_RATE):
    """시퀀서 아르페지오 — 반복, 패턴, 기계적 움직임"""
    if pattern is None:
        pattern = [1, 1.25, 1.5, 2, 1.5, 1.25]
    total_samples = int(sr * duration)
    result = np.zeros(total_samples)
    step_samples = int(sr * speed)
    if step_samples < 1:
        step_samples = 1
    step_idx = 0
    for i in range(0, total_samples, step_samples):
        freq = base_freq * pattern[step_idx % len(pattern)]
        step_idx += 1
        t = np.linspace(0, speed, step_samples, endpoint=False)
        note = np.sin(2 * np.pi * freq * t)
        note = envelope(note, attack=0.005, decay=0.05, sustain=0.3, release=0.1)
        note *= 0.15
        end = min(i + step_samples, total_samples)
        result[i:end] += note[:end - i]
    result = lowpass(result, 3000)
    result = reverb(result, decay=0.3, delay_ms=100, repeats=4)
    return result


def shimmer_high(freq, duration, sr=SAMPLE_RATE):
    """쉬머 하이톤 — 빛, 깨달음, 열림, 희망"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.zeros_like(t)
    for dt in [0.998, 1.0, 1.002]:
        wave += np.sin(2 * np.pi * freq * dt * t) * 0.15
    # 트레몰로
    tremolo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t)
    wave *= tremolo
    wave = reverb(wave, decay=0.6, delay_ms=150, repeats=10)
    return fade_in(fade_out(wave, 2.0), 2.0)


def noise_sweep(duration, direction="up", speed=0.3, sr=SAMPLE_RATE):
    """노이즈 스윕 — 전환, 상승, 에너지 축적"""
    total_samples = int(sr * duration)
    n = noise(duration)
    # 주파수 스윕
    if direction == "up":
        centers = np.linspace(200, 8000, total_samples)
    else:
        centers = np.linspace(8000, 200, total_samples)
    # 시간 변화 밴드패스를 청크별로 적용
    chunk_size = int(sr * 0.05)  # 50ms 청크
    result = np.zeros(total_samples)
    for i in range(0, total_samples, chunk_size):
        end = min(i + chunk_size, total_samples)
        center = float(centers[min(i + chunk_size // 2, total_samples - 1)])
        bw = center * 0.5
        low_f = max(center - bw, 20)
        high_f = min(center + bw, sr / 2 - 1)
        chunk = n[i:end]
        if len(chunk) > 12:  # butter 필터 최소 길이
            try:
                result[i:end] = bandpass(chunk, low_f, high_f, sr, order=1)
            except Exception:
                result[i:end] = chunk * 0.1
        else:
            result[i:end] = chunk * 0.1
    result *= 0.15
    result = reverb(result, decay=0.3, delay_ms=60, repeats=4)
    return result


def sub_pulse(freq, duration, bpm=80, sr=SAMPLE_RATE):
    """서브 베이스 펄스 — 심장 박동, 긴장, 압박"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    # BPM 기반 펄스 엔벨로프
    beat_interval = 60.0 / bpm
    pulse_env = np.zeros_like(t)
    beat_time = 0.0
    while beat_time < duration:
        beat_start = int(sr * beat_time)
        # 빠른 어택 → 느린 릴리즈
        attack_len = int(sr * 0.02)
        release_len = int(sr * beat_interval * 0.6)
        for j in range(attack_len):
            idx = beat_start + j
            if idx < len(pulse_env):
                pulse_env[idx] = max(pulse_env[idx], j / attack_len)
        for j in range(release_len):
            idx = beat_start + attack_len + j
            if idx < len(pulse_env):
                val = 1.0 - (j / release_len)
                pulse_env[idx] = max(pulse_env[idx], val)
        beat_time += beat_interval
    wave *= pulse_env
    wave = lowpass(wave, 100)
    return wave


def reverse_swell(duration, freq=330, sr=SAMPLE_RATE):
    """리버스 스웰 — 기대감, 다가오는 변화"""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave = np.zeros_like(t)
    for dt in [0.998, 1.0, 1.002]:
        wave += np.sin(2 * np.pi * freq * dt * t) * 0.2
    # 리버스 엔벨로프 (작게→크게)
    env = np.linspace(0, 1, len(wave)) ** 2
    wave *= env
    wave = reverb(wave, decay=0.5, delay_ms=100, repeats=6)
    return wave


# ============================================================
# EnometaMusicEngine — music_script.json 기반 렌더러
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

    def _get_section_duration(self, section):
        return section["end_sec"] - section["start_sec"]

    def _apply_section_transition(self, signal, section):
        """섹션 전환 이펙트 적용"""
        trans = section.get("transition_in", {})
        trans_type = trans.get("type", "crossfade")
        dur = trans.get("duration_sec", 1.0)

        if trans_type == "fade_in":
            signal = fade_in(signal, dur)
        elif trans_type == "crossfade":
            signal = fade_in(signal, dur)
        elif trans_type == "silence_break":
            silence_dur = trans.get("silence_sec", 0.3)
            silence_samples = int(self.sr * silence_dur)
            if silence_samples < len(signal):
                signal[:silence_samples] = 0
                then_type = trans.get("then", "fade_in")
                then_dur = trans.get("duration_sec", 1.0)
                if then_type == "fade_in":
                    remaining = signal[silence_samples:]
                    remaining = fade_in(remaining, then_dur)
                    signal[silence_samples:] = remaining

        return signal

    def _render_section(self, section):
        """섹션의 모든 악기를 렌더링"""
        start = section["start_sec"]
        dur = self._get_section_duration(section)
        instruments = section.get("instruments", {})
        effects = section.get("effects", {})

        filter_cutoff = effects.get("filter_cutoff", 4000)
        reverb_decay = effects.get("reverb_decay", 0.3)
        stereo_width = effects.get("stereo_width", 0.5)

        # Bass Drone
        bass_cfg = instruments.get("bass_drone", {})
        if bass_cfg.get("active"):
            freq = bass_cfg.get("freq_override") or self.bass_freq
            vol = bass_cfg.get("volume", 0.4)
            drone = deep_bass_drone(freq, dur, self.sr)
            drone = self._apply_section_transition(drone, section)
            if bass_cfg.get("fade") == "out":
                drone = fade_out(drone, dur * 0.7)
            self._add_mono(drone, start, vol * 0.8)

        # Clicks
        clicks_cfg = instruments.get("clicks", {})
        if clicks_cfg.get("active"):
            density = clicks_cfg.get("density", 0.3)
            pan_spread = clicks_cfg.get("pan_spread", 0.5)
            freq_range = clicks_cfg.get("freq_range", [2000, 5000])
            t_click = 0.0
            interval = max(0.05, 0.5 / max(density, 0.01))
            while t_click < dur:
                click = modular_click(self.sr)
                pan = random.uniform(-pan_spread, pan_spread)
                vol = random.uniform(0.3, 0.7) * density
                self._add_stereo(click, pan, start + t_click, vol)
                t_click += random.uniform(interval * 0.5, interval * 1.5)

        # Pad
        pad_cfg = instruments.get("pad", {})
        if pad_cfg.get("active"):
            vol = pad_cfg.get("volume", 0.5)
            harmony = pad_cfg.get("harmony")
            pad_signal = ambient_pad(self.pad_root, dur, harmony=harmony, sr=self.sr)
            pad_signal = self._apply_section_transition(pad_signal, section)
            if pad_cfg.get("fade") == "out":
                pad_signal = fade_out(pad_signal, dur * 0.5)
            self._add_stereo(pad_signal, 0.0, start, vol * 0.75)

        # Arpeggio
        arp_cfg = instruments.get("arpeggio", {})
        if arp_cfg.get("active"):
            vol = arp_cfg.get("volume", 0.5)
            speed = arp_cfg.get("speed", 0.2)
            arp_signal = arpeggio_sequence(
                self.arp_root, dur, self.arp_pattern, speed=speed, sr=self.sr
            )
            arp_signal = self._apply_section_transition(arp_signal, section)
            if arp_cfg.get("fade") == "out":
                arp_signal = fade_out(arp_signal, dur * 0.5)
            # 디튠 스테레오 쌍
            arp2 = arpeggio_sequence(
                self.arp_root + 1, dur,
                [p * 1.01 for p in self.arp_pattern],
                speed=speed * 1.02, sr=self.sr
            )
            if arp_cfg.get("fade") == "out":
                arp2 = fade_out(arp2, dur * 0.5)
            self._add_stereo(arp_signal, -0.3 * stereo_width, start, vol * 0.85)
            self._add_stereo(arp2, 0.3 * stereo_width, start + 0.05, vol * 0.5)

        # Glitch
        glitch_cfg = instruments.get("glitch", {})
        if glitch_cfg.get("active"):
            density = glitch_cfg.get("density", 0.3)
            glitch_signal = glitch_texture(dur, density, self.sr)
            glitch_signal = self._apply_section_transition(glitch_signal, section)
            if glitch_cfg.get("fade") == "out":
                glitch_signal = fade_out(glitch_signal, dur * 0.5)
            self._add_stereo(
                glitch_signal, 0.4 * stereo_width, start, 0.5
            )

        # Shimmer High
        shimmer_cfg = instruments.get("shimmer_high", {})
        if shimmer_cfg.get("active"):
            vol = shimmer_cfg.get("volume", 0.3)
            shim = shimmer_high(self.pad_root * 8, dur, self.sr)
            shim = self._apply_section_transition(shim, section)
            if shimmer_cfg.get("fade") == "out":
                shim = fade_out(shim, dur * 0.5)
            self._add_stereo(shim, 0.2, start, vol)

        # Noise Sweep
        sweep_cfg = instruments.get("noise_sweep", {})
        if sweep_cfg.get("active"):
            direction = sweep_cfg.get("direction", "up")
            speed = sweep_cfg.get("speed", 0.3)
            sweep = noise_sweep(dur, direction, speed, self.sr)
            self._add_stereo(sweep, 0.0, start, 0.6)

        # Sub Pulse
        sub_cfg = instruments.get("sub_pulse", {})
        if sub_cfg.get("active"):
            vol = sub_cfg.get("volume", 0.5)
            sub = sub_pulse(self.bass_freq * 0.5, dur, self.bpm, self.sr)
            self._add_mono(sub, start, vol * 0.4)

    def generate(self) -> np.ndarray:
        """music_script.json의 모든 섹션을 렌더링하고 마스터링"""
        sections = self.script.get("sections", [])
        total = len(sections)

        for i, section in enumerate(sections):
            sid = section.get("id", f"sec_{i}")
            emotion = section.get("emotion", "?")
            print(f"  [{i+1}/{total}] {sid} ({emotion}) "
                  f"{section['start_sec']:.1f}~{section['end_sec']:.1f}s",
                  flush=True)
            self._render_section(section)

        return self._master()

    def _master(self) -> np.ndarray:
        """마스터링: 리미팅 + 페이드 + 16bit 변환"""
        print("  Mastering...", flush=True)
        stereo = np.column_stack([self.master_L, self.master_R])

        # 리미팅
        peak = np.max(np.abs(stereo))
        if peak > 0:
            stereo = stereo / peak * 0.95

        # 전체 페이드
        fade_in_samples = int(self.sr * 2)
        fade_out_samples = int(self.sr * 3)
        for ch in range(2):
            stereo[:fade_in_samples, ch] *= np.linspace(0, 1, fade_in_samples)
            stereo[-fade_out_samples:, ch] *= np.linspace(1, 0, fade_out_samples)

        # 16bit WAV
        audio_16bit = (stereo * 32767).astype(np.int16)
        return audio_16bit


# ============================================================
# music_script.json 생성기 (visual_script.json → music_script.json)
# ============================================================

# 감정 → 악기 매핑 테이블
EMOTION_MAP = {
    "neutral": {
        "energy": 0.35,
        "bass_drone": {"active": True, "volume": 0.4},
        "clicks": {"active": True, "density": 0.25, "pan_spread": 0.4},
        "pad": {"active": True, "volume": 0.2},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.2},
    },
    "neutral_curious": {
        "energy": 0.4,
        "bass_drone": {"active": True, "volume": 0.45},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.5},
        "pad": {"active": True, "volume": 0.25},
        "arpeggio": {"active": True, "speed": 0.35, "volume": 0.15},
        "glitch": {"active": True, "density": 0.1},
        "sub_pulse": {"active": True, "volume": 0.25},
    },
    "curious": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.5},
        "clicks": {"active": True, "density": 0.4, "pan_spread": 0.5},
        "pad": {"active": True, "volume": 0.3},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.2},
        "glitch": {"active": True, "density": 0.12},
        "sub_pulse": {"active": True, "volume": 0.3},
    },
    "somber": {
        "energy": 0.45,
        "bass_drone": {"active": True, "volume": 0.65},
        "clicks": {"active": True, "density": 0.15, "pan_spread": 0.3},
        "pad": {"active": True, "volume": 0.35},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.3},
    },
    "somber_reflective": {
        "energy": 0.5,
        "bass_drone": {"active": True, "volume": 0.6},
        "clicks": {"active": True, "density": 0.1, "pan_spread": 0.3},
        "pad": {"active": True, "volume": 0.4},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.3},
        "glitch": {"active": False},
        "sub_pulse": {"active": True, "volume": 0.3},
    },
    "somber_repetitive": {
        "energy": 0.55,
        "bass_drone": {"active": True, "volume": 0.65},
        "clicks": {"active": True, "density": 0.3, "pan_spread": 0.4},
        "pad": {"active": True, "volume": 0.4},
        "arpeggio": {"active": True, "speed": 0.22, "volume": 0.45},
        "glitch": {"active": True, "density": 0.08},
        "sub_pulse": {"active": True, "volume": 0.35},
    },
    "somber_analytical": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.7},
        "clicks": {"active": True, "density": 0.35, "pan_spread": 0.5},
        "pad": {"active": True, "volume": 0.45},
        "arpeggio": {"active": True, "speed": 0.2, "volume": 0.5},
        "glitch": {"active": True, "density": 0.2},
        "sub_pulse": {"active": True, "volume": 0.4},
    },
    "tension": {
        "energy": 0.75,
        "bass_drone": {"active": True, "volume": 0.8},
        "clicks": {"active": True, "density": 1.0, "pan_spread": 0.8},
        "pad": {"active": True, "volume": 0.3},
        "arpeggio": {"active": True, "speed": 0.15, "volume": 0.6},
        "glitch": {"active": True, "density": 0.6},
        "noise_sweep": {"active": True, "direction": "up", "speed": 0.3},
        "sub_pulse": {"active": True, "volume": 0.6},
    },
    "tension_frustrated": {
        "energy": 0.85,
        "bass_drone": {"active": True, "volume": 0.85},
        "clicks": {"active": True, "density": 1.2, "pan_spread": 0.9},
        "pad": {"active": True, "volume": 0.35},
        "arpeggio": {"active": True, "speed": 0.1, "volume": 0.7},
        "glitch": {"active": True, "density": 0.7},
        "sub_pulse": {"active": True, "volume": 0.7},
    },
    "tension_peak": {
        "energy": 0.95,
        "bass_drone": {"active": True, "volume": 0.9},
        "clicks": {"active": True, "density": 1.5, "pan_spread": 1.0},
        "pad": {"active": True, "volume": 0.4},
        "arpeggio": {"active": True, "speed": 0.1, "volume": 0.8},
        "glitch": {"active": True, "density": 0.8},
        "noise_sweep": {"active": True, "direction": "up", "speed": 0.3},
        "sub_pulse": {"active": True, "volume": 0.8},
    },
    "awakening_climax": {
        "energy": 1.0,
        "bass_drone": {"active": True, "volume": 0.95},
        "clicks": {"active": True, "density": 0.3, "pan_spread": 0.6},
        "pad": {"active": True, "volume": 0.9, "harmony": "root_fifth"},
        "arpeggio": {"active": True, "speed": 0.18, "volume": 0.4, "fade": "out"},
        "glitch": {"active": True, "density": 0.15, "fade": "out"},
        "shimmer_high": {"active": True, "volume": 0.6},
        "sub_pulse": {"active": True, "volume": 0.5},
    },
    "awakening": {
        "energy": 0.85,
        "bass_drone": {"active": True, "volume": 0.8},
        "clicks": {"active": True, "density": 0.15, "pan_spread": 0.4},
        "pad": {"active": True, "volume": 0.75, "harmony": "root_fifth"},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.2},
        "glitch": {"active": False},
        "shimmer_high": {"active": True, "volume": 0.5},
        "sub_pulse": {"active": True, "volume": 0.4},
    },
    "hopeful": {
        "energy": 0.7,
        "bass_drone": {"active": True, "volume": 0.65},
        "clicks": {"active": True, "density": 0.1, "pan_spread": 0.3},
        "pad": {"active": True, "volume": 0.75, "harmony": "root_fifth"},
        "arpeggio": {"active": True, "speed": 0.3, "volume": 0.2},
        "glitch": {"active": False},
        "shimmer_high": {"active": True, "volume": 0.45},
        "sub_pulse": {"active": True, "volume": 0.3},
    },
    "transcendent": {
        "energy": 0.65,
        "bass_drone": {"active": True, "volume": 0.55},
        "clicks": {"active": False},
        "pad": {"active": True, "volume": 0.7, "harmony": "root_fifth"},
        "arpeggio": {"active": True, "speed": 0.35, "volume": 0.15},
        "glitch": {"active": False},
        "shimmer_high": {"active": True, "volume": 0.45, "fade": "out"},
        "sub_pulse": {"active": True, "volume": 0.25},
    },
    "transcendent_open": {
        "energy": 0.6,
        "bass_drone": {"active": True, "volume": 0.5},
        "clicks": {"active": False},
        "pad": {"active": True, "volume": 0.65, "harmony": "root_fifth"},
        "arpeggio": {"active": True, "speed": 0.4, "volume": 0.1},
        "glitch": {"active": False},
        "shimmer_high": {"active": True, "volume": 0.4, "fade": "out"},
    },
    "fade": {
        "energy": 0.1,
        "bass_drone": {"active": True, "volume": 0.15, "fade": "out"},
        "clicks": {"active": False},
        "pad": {"active": True, "volume": 0.1, "fade": "out"},
        "arpeggio": {"active": False},
        "glitch": {"active": False},
    },
}


def _get_transition(prev_emotion, curr_emotion):
    """두 감정 사이의 전환 방식 결정"""
    dramatic_pairs = {
        ("tension", "awakening"), ("tension_frustrated", "awakening_climax"),
        ("tension_peak", "awakening"), ("somber_analytical", "awakening_climax"),
        ("tension", "awakening_climax"),
    }
    pair = (prev_emotion, curr_emotion)
    if pair in dramatic_pairs:
        return {"type": "silence_break", "silence_sec": 0.3,
                "then": "fade_in", "duration_sec": 1.5}

    # 같은 계열이면 짧은 크로스페이드
    if prev_emotion.split("_")[0] == curr_emotion.split("_")[0]:
        return {"type": "crossfade", "duration_sec": 1.0}

    # 기본 크로스페이드
    return {"type": "crossfade", "duration_sec": 2.0}


def generate_music_script(visual_script: dict, narration_timing: dict = None) -> dict:
    """
    visual_script.json + narration_timing.json → music_script.json
    대본의 씬별 감정을 읽어서 악기 배치를 자동 결정.
    """
    scenes = visual_script.get("scenes", [])
    title = visual_script.get("title", "ENOMETA")

    # 전체 길이 계산
    total_duration = max(s["end_sec"] for s in scenes) if scenes else 60
    # 아웃로 여유 추가
    total_duration = total_duration + 5

    # 나레이션 세그먼트 → 씬 매핑 (있으면)
    segments = []
    if narration_timing:
        segments = narration_timing.get("segments", [])

    sections = []
    prev_emotion = None

    for i, scene in enumerate(scenes):
        emotion_key = scene.get("emotion", "neutral")

        # 감정 매핑 (정확한 매칭 → 접두사 매칭 → 기본)
        if emotion_key in EMOTION_MAP:
            mapping = EMOTION_MAP[emotion_key]
        else:
            # 접두사로 가장 가까운 감정 찾기
            base = emotion_key.split("_")[0]
            mapping = EMOTION_MAP.get(base, EMOTION_MAP["neutral"])

        # 전환 방식 결정
        if prev_emotion:
            transition = _get_transition(prev_emotion, emotion_key)
        elif i == 0:
            transition = {"type": "fade_in", "duration_sec": 1.0}
        else:
            transition = {"type": "crossfade", "duration_sec": 1.0}

        # 이펙트 설정 (에너지 기반)
        energy = mapping.get("energy", 0.3)
        effects = {
            "reverb_decay": 0.3 + energy * 0.3,
            "filter_cutoff": int(200 + energy * 3000),
            "stereo_width": 0.3 + energy * 0.5,
        }

        # 악기 구성
        instruments = {}
        for key in ["bass_drone", "clicks", "pad", "arpeggio", "glitch",
                     "shimmer_high", "noise_sweep", "sub_pulse"]:
            if key in mapping:
                instruments[key] = dict(mapping[key])  # copy

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

    # 아웃로 섹션 추가
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
                "bass_drone": {"active": True, "volume": 0.15, "fade": "out"},
                "pad": {"active": True, "volume": 0.1, "fade": "out"},
            },
            "effects": {
                "reverb_decay": 0.7,
                "filter_cutoff": 500,
                "stereo_width": 0.3,
            },
            "transition_in": {"type": "crossfade", "duration_sec": 3.0},
        }
        sections.append(outro)

    music_script = {
        "metadata": {
            "title": title,
            "duration": total_duration,
            "sample_rate": SAMPLE_RATE,
            "key": "E_minor",
            "base_bpm": 80,
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
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python enometa_music_engine.py <music_script.json> [output.wav]")
        print()
        print("Auto-generate from visual_script:")
        print("  python enometa_music_engine.py --from-visual <visual_script.json> "
              "[narration_timing.json] [output.wav]")
        sys.exit(1)

    if sys.argv[1] == "--from-visual":
        # visual_script.json → music_script.json → bgm.wav
        visual_path = sys.argv[2]
        narration_path = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].endswith(".wav") else None
        output_path = sys.argv[-1] if sys.argv[-1].endswith(".wav") else None

        import os
        if not output_path:
            output_path = os.path.join(os.path.dirname(visual_path), "bgm.wav")

        with open(visual_path, 'r', encoding='utf-8') as f:
            visual_script = json.load(f)

        narration_timing = None
        if narration_path:
            with open(narration_path, 'r', encoding='utf-8') as f:
                narration_timing = json.load(f)

        print("=== ENOMETA Music Script Generator ===")
        print(f"Visual script: {visual_path}")
        music_script = generate_music_script(visual_script, narration_timing)

        # music_script.json 저장
        ms_path = os.path.join(os.path.dirname(output_path), "music_script.json")
        with open(ms_path, 'w', encoding='utf-8') as f:
            json.dump(music_script, f, ensure_ascii=False, indent=2)
        print(f"Music script saved: {ms_path}")

    else:
        # music_script.json 직접 읽기
        script_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else "bgm.wav"

        with open(script_path, 'r', encoding='utf-8') as f:
            music_script = json.load(f)

    print()
    print("=== ENOMETA Generative Music Engine ===")
    print(f"Duration: {music_script['metadata']['duration']:.1f}s")
    print(f"Sections: {len(music_script['sections'])}")
    print(f"Key: {music_script['metadata'].get('key', 'E_minor')}")
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
