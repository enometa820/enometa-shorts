"""enometa_music: 악기 합성 함수"""
import random
import numpy as np
from .synthesis import (
    SAMPLE_RATE, sine, noise, lowpass, highpass, bandpass,
    reverb, fade_in, fade_out, envelope,
    resonant_lowpass, resonant_bandpass,
    make_wavetable, wavetable_osc, chorus, sidechain_pump,
    stereo_pan, smooth_envelope,
)


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


def transition_impact(sr=SAMPLE_RATE):
    """v12: 섹션 전환 임팩트 — 디지털 노이즈 크래시.
    전통적 심벌이 아닌 enometa 스타일: 날카로운 노이즈 버스트 + 빠른 감쇠.
    섹션 경계 첫 비트에서 킥 대신 배치.
    """
    duration = 0.15
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 밝은 노이즈 버스트 — 빠른 감쇠
    n = noise(duration, sr) * np.exp(-t * 25) * 0.5
    # 고주파 강조 (간단한 1차 하이패스: 차분)
    n[1:] = n[1:] - n[:-1] * 0.3
    # 어택 클릭
    click_samples = int(sr * 0.001)
    n[:click_samples] += noise(0.001, sr) * 0.4
    return n


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
