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


def mirror(seq: list) -> list:
    """palindrome: 원본 + 역순."""
    return seq + seq[::-1]


def normalize_to_range(seq: list, lo: float, hi: float) -> list:
    """정수 수열을 [lo, hi] 실수 범위로 매핑."""
    mn, mx = min(seq), max(seq)
    if mn == mx:
        return [0.5 * (lo + hi)] * len(seq)
    return [lo + (x - mn) / (mx - mn) * (hi - lo) for x in seq]


def composite(gate_seq: list, value_seq: list) -> list:
    """게이트 수열(0/1)로 값 수열 필터링. 0인 곳은 0."""
    out = []
    for i, g in enumerate(gate_seq):
        v = value_seq[i % len(value_seq)]
        out.append(v if g else 0)
    return out


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


def derive_episode_sequences(ep_seed: int) -> EpisodeSequenceConfig:
    """에피소드 시드에서 결정론적으로 시퀀스+음색 설정 파생."""
    rng = random.Random(ep_seed)
    # v13 패턴 파라미터
    drum_seq_type = rng.randint(0, 1)
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
    # 기본 16스텝 이진 수열
    if config.drum_seq_type == 0:
        kick_base = thue_morse(16)
        hihat_base = rudin_shapiro(16)
    else:
        kick_base = rudin_shapiro(16)
        hihat_base = thue_morse(16)

    # 에피소드별 회전
    kick_base = rotate(kick_base, config.drum_rotation)
    hihat_base = rotate(hihat_base, config.drum_rotation + 2)

    # 스네어: 킥 반전 + 4스텝 회전 (킥과 엇갈림)
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

# 양자화 대상 음정비율
PITCH_RATIOS = [0.5, 0.75, 1.0, 1.125, 1.25, 1.333, 1.5, 1.75, 2.0]

# 에너지 레벨별 음역 범위
ENERGY_PITCH_RANGE = {
    "high":    (0.75, 2.0),
    "mid":     (0.75, 1.5),
    "low":     (1.0, 1.5),
    "tension": (0.5, 2.0),
}


def generate_pitch_pattern(config: EpisodeSequenceConfig, energy_key: str = "mid") -> list:
    """Nørgård 수열 기반 음정비율 패턴 생성.

    Returns: [float, ...] 길이 = config.pitch_length
    """
    length = config.pitch_length

    # Nørgård 수열 생성 (여유분 포함)
    raw = norgard(length * 4)
    raw = rotate(raw, config.pitch_rotation)[:length]

    # 에너지별 음역 범위
    lo, hi = ENERGY_PITCH_RANGE.get(energy_key, (0.75, 1.5))

    # 정수 → 실수 매핑
    ratios = normalize_to_range(raw, lo, hi)

    # 가장 가까운 음악적 비율로 양자화
    return [min(PITCH_RATIOS, key=lambda r: abs(r - v)) for v in ratios]


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
    print("Composite(TM, RS):", composite(tm, rudin_shapiro(16)))

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
