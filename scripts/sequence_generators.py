"""v13 수학적 시퀀스 생성기 — 하드코딩 패턴을 대체하는 알고리즘 패턴 엔진.

3종 시퀀스:
  - Thue-Morse: 이진(0/1), 자기유사 리듬
  - Nørgård Infinity: 정수, 프랙탈 멜로디 윤곽
  - Rudin-Shapiro: 이진(0/1), 불규칙 리듬

에피소드 시드 → EpisodeSequenceConfig → 드럼/피치 패턴 생성.
enometa_music_engine.py 에서 import 하여 사용.
"""

import random
from dataclasses import dataclass

# ── 시퀀스 생성기 ──────────────────────────────────────────

def thue_morse(n: int) -> list:
    """Thue-Morse 수열: bin(i)의 1 개수 mod 2."""
    return [bin(i).count('1') % 2 for i in range(n)]


def norgard(n: int) -> list:
    """Nørgård Infinity Series: s(0)=0, s(2k)=-s(k), s(2k+1)=s(k)+1."""
    if n <= 0:
        return []
    s = [0] * max(n, 2)
    s[0] = 0
    if n > 1:
        s[1] = 1
    for i in range(2, n):
        if i % 2 == 0:
            s[i] = -s[i // 2]
        else:
            s[i] = s[(i - 1) // 2] + 1
    return s[:n]


def rudin_shapiro(n: int) -> list:
    """Rudin-Shapiro 수열: hamming(i & (i<<1)) mod 2."""
    return [bin(i & (i << 1)).count('1') % 2 for i in range(n)]


def fibonacci_word(n: int) -> list:
    """Fibonacci Word 수열: F(0)=0, F(1)=01, F(k)=F(k-1)+F(k-2).
    황금비 기반 준주기 패턴 — Thue-Morse보다 불규칙하고 유기적.
    """
    if n <= 0:
        return []
    a, b = [0], [0, 1]
    while len(b) < n + 32:  # 여유분 생성
        a, b = b, b + a
    return [x % 2 for x in b[:n]]  # 0/1 이진화


def cantor_set(n: int, density: float = 0.5) -> list:
    """Cantor Set 기반 수열: 3등분 자기유사 패턴.
    density로 밀도 제어 (0.33=칸토르 3등분, 0.5=균형).
    """
    if n <= 0:
        return []
    result = [1] * n
    # 중간 1/3 제거를 재귀적으로 적용 (depth=3)
    def remove_middle(start, end, depth):
        if depth == 0 or end - start < 3:
            return
        third = (end - start) // 3
        mid_s = start + third
        mid_e = end - third
        for i in range(mid_s, mid_e):
            if i < n:
                result[i] = 0
        remove_middle(start, mid_s, depth - 1)
        remove_middle(mid_e, end, depth - 1)
    remove_middle(0, n, 3)
    return result


# ── 변환 함수 ──────────────────────────────────────────────

def invert_binary(seq: list) -> list:
    """이진 수열 반전: 0↔1."""
    return [1 - x for x in seq]


def rotate(seq: list, n: int) -> list:
    """순환 시프트 (왼쪽으로 n칸)."""
    if not seq:
        return []
    n = n % len(seq)
    return seq[n:] + seq[:n]


def normalize_to_range(seq: list, lo: float, hi: float) -> list:
    """정수 수열을 [lo, hi] 실수 범위로 매핑."""
    mn, mx = min(seq), max(seq)
    if mn == mx:
        return [0.5 * (lo + hi)] * len(seq)
    return [lo + (x - mn) / (mx - mn) * (hi - lo) for x in seq]


def density_filter(seq: list, target_density: float, seed: int = 0) -> list:
    """이진 수열의 밀도를 target_density에 맞춤 (1을 솎아냄).

    밀도가 이미 target 이하면 그대로 반환.
    target > 현재면 0을 1로 채움.
    """
    if not seq:
        return []
    current = sum(seq) / len(seq)
    result = list(seq)
    rng = random.Random(seed)

    if current > target_density:
        # 1을 솎아냄
        active = [i for i, v in enumerate(result) if v == 1]
        remove_count = max(0, int(len(active) - target_density * len(seq)))
        rng.shuffle(active)
        for i in active[:remove_count]:
            result[i] = 0
    elif current < target_density:
        # 0을 1로 채움
        inactive = [i for i, v in enumerate(result) if v == 0]
        add_count = max(0, int(target_density * len(seq) - sum(result)))
        rng.shuffle(inactive)
        for i in inactive[:add_count]:
            result[i] = 1

    return result


# ── 에피소드 시퀀스 설정 ──────────────────────────────────

@dataclass
class EpisodeSequenceConfig:
    """에피소드별 시퀀스+음색 파라미터. ep_seed에서 결정론적으로 파생."""
    # v13: 패턴
    drum_seq_type: int     # 0=thue_morse, 1=rudin_shapiro
    drum_rotation: int     # 0~15
    pitch_rotation: int    # 0~7
    pitch_length: int      # 4~8
    bpm: int               # 108~162
    # v14: 음색
    saw_harmonics: dict    # 웨이브테이블 배음 {번호: 진폭}
    filter_cutoff_base: int   # LP 필터 기본 컷오프 (Hz)
    chorus_depth_ms: float    # 코러스 깊이 (ms)
    fm_mod_ratio: float       # FM 베이스 모듈레이터 비율
    bass_detune: float        # 베이스 디튜닝 비율 (0.001~0.01)
    kick_character: int       # 킥 캐릭터 0=tight 1=boomy 2=punchy
    # v19: 아르페지오 다양화
    arp_pattern: list          # 음정 비율 패턴 (예: [1, 1.25, 1.5, 2])
    arp_division: int          # BPM 분할 (2=8분, 3=3연음, 4=16분)
    # v21: 멜로디 다양화 (sine_interference)
    melody_scale_offset: int   # 0~6, 스케일 시작 음계 회전
    melody_beat_base: float    # 2.0~8.0 Hz, 맥놀이 기본 주파수
    melody_norgard_offset: int # 0~15, Norgard 수열 시작점 오프셋
    # v23: 음색/조성 다양성
    base_freq: float           # 근음 주파수 55~73 Hz (에피소드마다 다른 키)
    chord_voicing: str         # 코드 보이싱 (minor/minor7/sus4/power/dim)
    hat_brightness: int        # 하이햇 HP 필터 컷오프 Hz (3000~12000)
    hat_decay: float           # 하이햇 감쇠 속도 (40~80)
    snare_tone_mix: float      # 스네어 톤/노이즈 비율 (0.0~0.45)
    snare_freq: int            # 스네어 톤 주파수 Hz (150~260)
    rhodes_brightness: float   # 로즈 패드 밝기 (0.0~1.0)
    # v23: 드럼 패턴 다양성
    snare_independent: bool    # True=독립 시퀀스, False=킥 파생(기존)
    # v24: 멜로디 수열 유형 + 장르별 음정 풀
    melody_seq_type: int       # 0=norgard 1=fibonacci 2=thue_morse 3=random_contour
    # v25: 신규 멜로디 레이어 파라미터 (별도 rng offset으로 파생 — 기존 스트림 보존)
    pluck_brightness: float    # 0.2~0.9 (나일론→금속)
    pad_morph_speed: float     # 0.1~0.8 (느린→빠른 LFO 모핑)
    fm_lead_mod_ratio: float   # 1.5~5.0 (FM 모듈레이터 비율)


# ── 아르페지오 패턴 풀 ─────────────────────────────────────
ARP_PATTERN_POOL = [
    [1, 1.25, 1.5, 2, 1.5, 1.25],     # 0: up-down (클래식)
    [1, 1.5, 1.25, 2],                  # 1: broken up (불규칙 상승)
    [2, 1.5, 1.25, 1, 1.25, 1.5],      # 2: down-up (역방향)
    [1, 2, 1.5, 1.25],                  # 3: octave-first (옥타브 점프)
    [1, 1.25, 2, 1.5, 1.25, 1],        # 4: peak-middle (중간 피크)
    [1, 1.5, 2, 1.5],                   # 5: fifths (5도 중심)
    [1, 1.333, 1.5, 2, 1.333, 1],      # 6: minor feel (단조 느낌)
    [0.5, 1, 1.5, 2],                   # 7: wide ascending (넓은 상승)
]

ARP_DIVISION_POOL = [4, 4, 3, 2]  # 4=16분음표, 3=3연음, 2=8분음표

BPM_POOL = [108, 115, 120, 125, 128, 130, 135, 138, 140, 145, 150, 155, 160, 162]

# v14: 웨이브테이블용 배음 풀 — 홀수/짝수 혼합으로 다양한 음색
_HARMONIC_POOL = [1, 2, 3, 4, 5, 6, 7, 8]
_CUTOFF_POOL = [2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000]

# v23: 다양성 강화 풀
KEY_FREQS = [55.0, 58.27, 61.74, 65.41, 69.30, 73.42]  # A1~D2 반음 6개
CHORD_VOICING_POOL = ["minor", "minor7", "sus4", "power", "dim"]
HAT_BRIGHTNESS_POOL = [3000, 4500, 6000, 8000, 10000, 12000]
SNARE_FREQ_POOL = [150, 175, 200, 230, 260]


def derive_episode_sequences(ep_seed: int) -> EpisodeSequenceConfig:
    """에피소드 시드에서 결정론적으로 시퀀스+음색 설정 파생."""
    rng = random.Random(ep_seed)
    # v13 패턴 파라미터 (drum_seq_type은 v23에서 4종으로 확장됨, 아래에서 재정의)
    drum_rotation = rng.randint(0, 15)
    pitch_rotation = rng.randint(0, 7)
    pitch_length = rng.choice([4, 5, 6, 7, 8])
    bpm = rng.choice(BPM_POOL)
    # v14 음색 파라미터
    n_harmonics = rng.randint(3, 6)
    saw_harmonics = {1: 1.0}  # 기본음 항상 최대
    used = {1}
    for _ in range(n_harmonics - 1):
        h = rng.choice([x for x in _HARMONIC_POOL if x not in used])
        saw_harmonics[h] = round(rng.uniform(0.15, 0.8), 2)
        used.add(h)
    # v19: 아르페지오 다양화
    arp_pattern = rng.choice(ARP_PATTERN_POOL)
    arp_division = rng.choice(ARP_DIVISION_POOL)
    # v21: 멜로디 다양화
    melody_scale_offset = rng.randint(0, 6)
    melody_beat_base = round(rng.uniform(2.0, 8.0), 1)
    melody_norgard_offset = rng.randint(0, 15)
    # v23: 음색/조성 다양성
    base_freq = rng.choice(KEY_FREQS)
    chord_voicing = rng.choice(CHORD_VOICING_POOL)
    hat_brightness = rng.choice(HAT_BRIGHTNESS_POOL)
    hat_decay = round(rng.uniform(40.0, 80.0), 1)
    snare_tone_mix = round(rng.uniform(0.0, 0.45), 2)
    snare_freq = rng.choice(SNARE_FREQ_POOL)
    rhodes_brightness = round(rng.uniform(0.0, 1.0), 2)
    # v23: 드럼 다양성 — 시퀀스 4종 + 스네어 독립 여부
    drum_seq_type = rng.randint(0, 3)   # 0=TM 1=RS 2=Fibonacci 3=Cantor
    snare_independent = rng.random() > 0.5  # 50% 확률로 독립 패턴
    # v24: 멜로디 수열 유형
    melody_seq_type = rng.randint(0, 3)  # 0=norgard 1=fibonacci 2=thue_morse 3=random_contour
    # v25: 신규 레이어 파라미터 — 별도 rng (기존 스트림 보존)
    rng25 = random.Random(ep_seed + 25000)
    pluck_brightness  = round(rng25.uniform(0.2, 0.9), 2)
    pad_morph_speed   = round(rng25.uniform(0.1, 0.8), 2)
    fm_lead_mod_ratio = round(rng25.uniform(1.5, 5.0), 2)
    return EpisodeSequenceConfig(
        drum_seq_type=drum_seq_type,
        drum_rotation=drum_rotation,
        pitch_rotation=pitch_rotation,
        pitch_length=pitch_length,
        bpm=bpm,
        saw_harmonics=saw_harmonics,
        filter_cutoff_base=rng.choice(_CUTOFF_POOL),
        chorus_depth_ms=round(rng.uniform(1.0, 4.5), 1),
        fm_mod_ratio=round(rng.uniform(1.5, 3.5), 2),
        bass_detune=round(rng.uniform(0.001, 0.008), 4),
        kick_character=rng.randint(0, 2),
        arp_pattern=arp_pattern,
        arp_division=arp_division,
        melody_scale_offset=melody_scale_offset,
        melody_beat_base=melody_beat_base,
        melody_norgard_offset=melody_norgard_offset,
        base_freq=base_freq,
        chord_voicing=chord_voicing,
        hat_brightness=hat_brightness,
        hat_decay=hat_decay,
        snare_tone_mix=snare_tone_mix,
        snare_freq=snare_freq,
        rhodes_brightness=rhodes_brightness,
        snare_independent=snare_independent,
        melody_seq_type=melody_seq_type,
        pluck_brightness=pluck_brightness,
        pad_morph_speed=pad_morph_speed,
        fm_lead_mod_ratio=fm_lead_mod_ratio,
    )


# ── 드럼 패턴 생성 ────────────────────────────────────────

# 역할별 목표 밀도 (16스텝 중 1의 비율)
ROLE_DENSITY = {
    "intro":     {"kick": 0.19, "snare": 0.00, "hihat": 0.25},
    "buildup":   {"kick": 0.25, "snare": 0.06, "hihat": 0.38},
    "drop":      {"kick": 0.38, "snare": 0.13, "hihat": 0.50},
    "breakdown": {"kick": 0.13, "snare": 0.00, "hihat": 0.25},
    "drop2":     {"kick": 0.44, "snare": 0.13, "hihat": 0.56},
    "outro":     {"kick": 0.13, "snare": 0.00, "hihat": 0.19},
}


def generate_drum_pattern(config: EpisodeSequenceConfig, role: str, si: float = 0.5) -> dict:
    """시퀀스 기반 16스텝 드럼 패턴 생성.

    Returns: {"kick": [0/1]*16, "snare": [0/1]*16, "hihat": [0/1]*16}
    """
    # v23: 4종 기본 시퀀스 (0=TM 1=RS 2=Fibonacci 3=Cantor)
    _SEQ_POOL = [thue_morse, rudin_shapiro,
                 lambda n: fibonacci_word(n),
                 lambda n: cantor_set(n)]
    seq_fn_kick  = _SEQ_POOL[config.drum_seq_type % 4]
    seq_fn_hihat = _SEQ_POOL[(config.drum_seq_type + 1) % 4]  # 킥과 다른 시퀀스
    kick_base  = seq_fn_kick(16)
    hihat_base = seq_fn_hihat(16)

    # 에피소드별 회전
    kick_base = rotate(kick_base, config.drum_rotation)
    hihat_base = rotate(hihat_base, config.drum_rotation + 2)

    # 스네어: 독립 패턴 or 킥 파생 (snare_independent 플래그)
    if getattr(config, 'snare_independent', False):
        seq_fn_snare = _SEQ_POOL[(config.drum_seq_type + 2) % 4]
        snare_base = rotate(seq_fn_snare(16), config.drum_rotation + 8)
    else:
        snare_base = invert_binary(rotate(kick_base, 4))

    # 밀도 테이블
    densities = ROLE_DENSITY.get(role, ROLE_DENSITY["drop"])

    # SI 밀도 스케일: si=0 → ×0.7, si=1 → ×1.3
    si_mult = 0.7 + si * 0.6

    seed_base = config.drum_rotation + hash(role) % 1000

    kick = density_filter(kick_base, densities["kick"] * si_mult, seed=seed_base)
    snare = density_filter(snare_base, densities["snare"] * si_mult, seed=seed_base + 1)
    hihat = density_filter(hihat_base, densities["hihat"] * si_mult, seed=seed_base + 2)

    # 음악적 제약: non-minimal 역할에서 beat-1 킥 보장
    if densities["kick"] >= 0.19 and role not in ("outro",):
        kick[0] = 1

    return {"kick": kick, "snare": snare, "hihat": hihat}


def generate_fill_pattern(config: EpisodeSequenceConfig, fill_type: str) -> dict:
    """필인/드롭용 16스텝 패턴 생성."""
    if fill_type == "fill_buildup":
        # 기본 수열 + 후반 밀도 증가
        if config.drum_seq_type == 0:
            base = thue_morse(16)
        else:
            base = rudin_shapiro(16)
        base = rotate(base, config.drum_rotation)
        # 후반 8스텝: 짝수 인덱스 강제 활성
        for i in range(8, 16):
            if i % 2 == 0:
                base[i] = 1
        return {
            "kick": base,
            "snare": [0]*8 + [0, 0, 0, 0, 0, 0, 1, 0],
            "hihat": [1] * 16,
        }

    elif fill_type == "fill_snare_roll":
        # 가속 스네어 (구조적으로 항상 같아야 함)
        return {
            "kick": [1] + [0] * 15,
            "snare": [0]*4 + [1, 0, 0, 0] + [1, 0, 1, 0] + [1, 0, 1, 1],
            "hihat": [0] * 16,
        }

    elif fill_type == "drop_silence":
        return {"kick": [0]*16, "snare": [0]*16, "hihat": [0]*16}

    elif fill_type == "drop_impact":
        if config.drum_seq_type == 0:
            base = thue_morse(16)
        else:
            base = rudin_shapiro(16)
        sparse = density_filter(base, 0.13, seed=config.drum_rotation)
        sparse[0] = 1  # beat-1 보장
        return {
            "kick": sparse,
            "snare": [0] * 16,
            "hihat": density_filter(invert_binary(sparse), 0.19, seed=config.drum_rotation),
        }

    # fallback
    return {"kick": [0]*16, "snare": [0]*16, "hihat": [0]*16}


# ── 피치 패턴 생성 ────────────────────────────────────────

# 기본 음정비율 풀 (fallback)
PITCH_RATIOS = [0.5, 0.75, 1.0, 1.125, 1.25, 1.333, 1.5, 1.75, 2.0]

# v24: 장르별 음정 풀 — 장르 정체성에 맞는 음정 집합
GENRE_PITCH_RATIOS = {
    # 크로매틱 반음계 — acid 특유의 액체 필터 스윕과 어울림
    "acid":       [1.0, 1.059, 1.122, 1.189, 1.260, 1.335, 1.414, 1.498, 1.587, 1.782, 2.0],
    # 옥타브+5도 도약 — techno의 강렬한 리듬감
    "techno":     [0.5, 1.0, 1.5, 2.0, 0.75, 1.25],
    # 파워코드 간격 — industrial의 거칠고 강한 질감
    "industrial": [0.5, 1.0, 1.189, 1.498, 2.0],
    # 펜타토닉 — ambient의 떠다니는 명상적 질감
    "ambient":    [1.0, 1.125, 1.25, 1.5, 1.75, 2.0],
    # 펜타토닉 — dub의 느슨한 그루브
    "dub":        [1.0, 1.125, 1.333, 1.5, 1.75, 2.0],
    # 미분음 느낌 — microsound의 입자적 텍스처
    "microsound": [1.0, 1.059, 1.122, 1.414, 1.587, 2.0],
    # 단순 3화음 — minimal의 절제
    "minimal":    [1.0, 1.25, 1.5, 2.0],
    # 불규칙 크로매틱 — IDM의 복잡한 리듬/멜로디
    "IDM":        [0.5, 1.0, 1.189, 1.414, 1.498, 1.782, 2.0],
    # 극단 도약 — glitch의 파괴적 음정
    "glitch":     [0.5, 0.75, 1.0, 1.414, 2.0, 2.828],
    # 메이저 7th 풍 — house의 따뜻한 코드감
    "house":      [1.0, 1.125, 1.25, 1.333, 1.5, 1.75, 2.0],
}

# 에너지 레벨별 음역 범위
ENERGY_PITCH_RANGE = {
    "high":    (0.75, 2.0),
    "mid":     (0.75, 1.5),
    "low":     (1.0, 1.5),
    "tension": (0.5, 2.0),
}


def generate_pitch_pattern(config: EpisodeSequenceConfig, energy_key: str = "mid",
                            genre: str = "") -> list:
    """v24: 멜로디 수열 4종 × 장르별 음정 풀 — 에피소드마다 다른 멜로디 윤곽.

    melody_seq_type:
      0 = Nørgård  (프랙탈 자기유사)
      1 = Fibonacci word (황금비 비주기)
      2 = Thue-Morse (이진 교대 → 멜로디 변환)
      3 = Random contour (ep_seed 기반 완전 랜덤)

    genre: GENRE_PITCH_RATIOS 키 (없으면 PITCH_RATIOS fallback)

    Returns: [float, ...] 길이 = config.pitch_length
    """
    length = config.pitch_length
    seq_type = getattr(config, "melody_seq_type", 0)

    # ── 수열 선택 ──────────────────────────────────────────
    if seq_type == 0:
        # Nørgård: 프랙탈 자기유사 윤곽
        raw = norgard(length * 4)
        raw = rotate(raw, config.pitch_rotation)[:length]
    elif seq_type == 1:
        # Fibonacci word: 황금비 기반 비주기 패턴 → 정수로 스케일
        raw_bin = fibonacci_word(length * 4)[:length]
        # 0/1 이진 → 0~7 범위로 확장 (pitch_rotation으로 오프셋)
        offset = config.pitch_rotation % 4
        raw = [v * (3 + offset) + (i % 3) for i, v in enumerate(raw_bin)]
    elif seq_type == 2:
        # Thue-Morse: 이진 교대 → 멜로디 윤곽으로 변환
        raw_bin = thue_morse(length * 4)[:length]
        scale = config.pitch_rotation % 5 + 2  # 2~6
        raw = [v * scale + (i % scale) for i, v in enumerate(raw_bin)]
    else:
        # Random contour: ep_seed 기반 완전 랜덤 (같은 ep에서는 항상 동일)
        crng = random.Random(config.pitch_rotation * 997 + length * 31)
        raw = [crng.randint(0, 8) for _ in range(length)]

    # ── 장르별 음정 풀 선택 ────────────────────────────────
    pitch_pool = GENRE_PITCH_RATIOS.get(genre, PITCH_RATIOS)

    # ── 음역 범위 적용 ─────────────────────────────────────
    lo, hi = ENERGY_PITCH_RANGE.get(energy_key, (0.75, 1.5))
    ratios = normalize_to_range(raw, lo, hi)

    # ── 가장 가까운 음정으로 양자화 ────────────────────────
    return [min(pitch_pool, key=lambda r: abs(r - v)) for v in ratios]


# ── 테스트 ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Sequence Generators v14 Test ===\n")

    # 시퀀스 출력
    print("Thue-Morse(16):", thue_morse(16))
    print("Rudin-Shapiro(16):", rudin_shapiro(16))
    print("Norgard(16):", norgard(16))

    # 변환 테스트
    tm = thue_morse(16)
    print("\nTM invert:", invert_binary(tm))
    print("TM rotate(4):", rotate(tm, 4))
    # 에피소드 설정
    for seed in [42, 123, 777, 9999]:
        cfg = derive_episode_sequences(seed)
        print(f"\nSeed {seed}: drum={['TM','RS'][cfg.drum_seq_type]}, "
              f"rot={cfg.drum_rotation}, pitch_len={cfg.pitch_length}, bpm={cfg.bpm}")
        print(f"  v14 timbre: harmonics={cfg.saw_harmonics}, cutoff={cfg.filter_cutoff_base}Hz, "
              f"chorus={cfg.chorus_depth_ms}ms, fm_ratio={cfg.fm_mod_ratio}, "
              f"kick={'tight/boomy/punchy'.split('/')[cfg.kick_character]}")

        # 드럼 패턴
        for role in ["intro", "drop", "breakdown"]:
            pat = generate_drum_pattern(cfg, role, si=0.6)
            k_density = sum(pat["kick"]) / 16
            h_density = sum(pat["hihat"]) / 16
            print(f"  {role:11s} kick={''.join(str(x) for x in pat['kick'])} "
                  f"({k_density:.2f})  hihat={''.join(str(x) for x in pat['hihat'])} ({h_density:.2f})")

        # 피치 패턴
        for ek in ["high", "low"]:
            pp = generate_pitch_pattern(cfg, ek)
            print(f"  pitch({ek:7s}): {pp}")

    # 결정론 확인
    cfg1 = derive_episode_sequences(42)
    cfg2 = derive_episode_sequences(42)
    p1 = generate_drum_pattern(cfg1, "drop", 0.7)
    p2 = generate_drum_pattern(cfg2, "drop", 0.7)
    assert p1 == p2, "Determinism failed!"
    print("\n[OK] Determinism check passed")
