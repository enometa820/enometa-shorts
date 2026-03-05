"""enometa_music/textures.py — 텍스처/이펙트 생성 함수"""
import random
import numpy as np
from .synthesis import (
    SAMPLE_RATE, noise, sine, bandpass, reverb, envelope,
    resonant_lowpass, chorus,
)
from .instruments import bit_crush, soft_clip


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


def wavefold(signal, folds=3):
    """웨이브폴딩 — 모듈러 신스 디스토션 (파형 접기)"""
    # 신호 증폭 → ±1 경계에서 반사
    s = signal * folds
    # 삼각파 접기: [-1, 1] 범위로 반복 반사
    return 4.0 * (np.abs((s - 1) % 4 - 2) - 1) / 4.0


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
                      bpm=0, apply_chorus=False, chorus_depth_ms=2.5):
    """시퀀서 아르페지오 v14 — BPM 동기 + 코러스 옵션
    bpm>0이면 speed를 BPM 16분음표로 자동 동기화.
    """
    if pattern is None:
        pattern = [1, 1.25, 1.5, 2, 1.5, 1.25]
    total_samples = int(sr * duration)

    # v14: BPM 동기화 (16분음표 단위)
    if bpm > 0:
        speed = 60.0 / bpm / 4  # 16분음표

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
