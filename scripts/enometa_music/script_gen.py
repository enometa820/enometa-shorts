"""enometa_music/script_gen.py — 음악 스크립트 생성 함수"""
import os
import json
import random
import numpy as np
from .synthesis import SAMPLE_RATE
from .tables import (
    EMOTION_MAP, SINE_MELODY_SEQUENCES, EMOTION_TO_MELODY,
    build_sine_melody_sequences,
    SONG_ARC_PRESETS, GENRE_PRESETS, ARRANGEMENT_TABLE,
    ROLE_ENERGY, ROLE_BAR_RATIOS,
    KEY_PRESETS, KEY_PRIORITY,
    AVAILABLE_TEXTURE_MODULES,
)


def _plan_song_structure(total_duration: float, bpm: float,
                         climax_time: float = None, outro_time: float = None) -> list:
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

    # 총 바 수가 target 대비 ±20% 이내가 되도록 재조정
    final_total = sum(b for _, b in roles_bars)
    max_bars = int(total_bars * 1.2)
    if final_total > max_bars:
        # 가장 큰 섹션부터 축소
        excess = final_total - total_bars
        for shrink_target in ("drop2", "drop", "intro"):
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
        arr = ARRANGEMENT_TABLE[role_name]
        instruments = {}
        for inst_key, vol in arr.items():
            # genre_preset volume_scale 적용
            scaled_vol = vol * vol_scale.get(inst_key, 1.0)
            instruments[inst_key] = {
                "active": scaled_vol > 0.01,
                "volume": scaled_vol,
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

    return sections, t  # sections + 실제 total_duration 반환


def _load_music_history(project_dir: str) -> dict:
    """v7-P7: music_history.json 로딩"""
    path = os.path.join(project_dir, "music_history.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"episodes": {}}


def _save_music_history(project_dir: str, history: dict):
    """v7-P7 + v8: music_history.json 저장 (texture_modules 포함)"""
    path = os.path.join(project_dir, "music_history.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print(f"  Music history saved: {path}")


def _select_texture_modules_from_history(project_dir: str, count: int = 4) -> list:
    """v8 C-6: 최근 2개 에피소드에서 사용한 텍스처 모듈을 피해 새 조합 선택.

    Returns:
        list: 선택된 texture module 이름 리스트 (3~4개)
    """
    history = _load_music_history(project_dir) if project_dir else {"episodes": {}}
    episodes = history.get("episodes", {})

    # 최근 2개 에피소드의 텍스처 모듈 수집
    recent_modules = set()
    sorted_eps = sorted(episodes.keys(), reverse=True)
    for ep in sorted_eps[:2]:
        ep_data = episodes[ep]
        mods = ep_data.get("texture_modules", [])
        recent_modules.update(mods)

    # 최근 사용하지 않은 모듈 우선 선택
    available = [m for m in AVAILABLE_TEXTURE_MODULES if m not in recent_modules]

    # 모두 최근 사용됐으면 전체에서 선택
    if len(available) < count:
        available = list(AVAILABLE_TEXTURE_MODULES)

    # melodic_sequence는 항상 포함 (v8 핵심 기능)
    selected = []
    if "melodic_sequence" not in available:
        selected.append("melodic_sequence")
        count -= 1

    # 나머지 랜덤 선택
    remaining = [m for m in available if m not in selected]
    random.shuffle(remaining)
    selected.extend(remaining[:count])

    # 최소 3개 보장
    if len(selected) < 3:
        for m in AVAILABLE_TEXTURE_MODULES:
            if m not in selected:
                selected.append(m)
            if len(selected) >= 3:
                break

    print(f"  [v8 texture_modules] selected: {selected}")
    if recent_modules:
        print(f"  [v8 texture_modules] avoided (recent): {recent_modules}")

    return selected


def _select_key_from_history(history: dict, genre: str, lookback: int = 2) -> str:
    """v7-P7: 최근 에피소드 이력 기반 키 자동 선택 (중복 회피)"""
    episodes = history.get("episodes", {})
    if not episodes:
        return KEY_PRIORITY[0]  # 이력 없으면 기본 키

    # 최근 N개 에피소드의 키 수집
    sorted_eps = sorted(episodes.keys(), reverse=True)
    recent_keys = []
    recent_genres = []
    for ep in sorted_eps[:lookback]:
        ep_data = episodes[ep]
        recent_keys.append(ep_data.get("key", ""))
        recent_genres.append(ep_data.get("genre", ""))

    # 최근 사용하지 않은 키 선택
    for key in KEY_PRIORITY:
        if key not in recent_keys:
            return key

    # 모든 키가 최근 사용됨 → 가장 오래된 키 재사용
    return KEY_PRIORITY[0]


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


def generate_music_script(visual_script: dict, narration_timing: dict = None,
                          genre: str = "enometa", episode: str = None,
                          project_dir: str = None) -> dict:
    """
    visual_script.json + narration_timing.json → music_script.json
    대본의 씬별 감정을 읽어서 악기 배치를 자동 결정.
    genre: v8부터 enometa 단일 장르. 하위호환을 위해 파라미터 유지.
    episode: 에피소드 ID (ep006 등) — 이력 추적용
    project_dir: 프로젝트 루트 — music_history.json 위치
    """
    # v11: enometa 단일 장르 — 하위호환: "ikeda" 입력 시 자동 매핑
    if genre == "ikeda":
        genre = "enometa"
    if genre and genre != "enometa":
        print(f"  [v11 WARNING] Genre '{genre}' is deprecated. Using 'enometa' (single genre system).")
        genre = "enometa"
    if not genre:
        genre = "enometa"

    scenes = visual_script.get("scenes", [])
    title = visual_script.get("title", "ENOMETA")

    total_duration = max(s["end_sec"] for s in scenes) if scenes else 60
    # 엔드카드(6초) + 여유(2초) 포함하여 BGM이 엔드카드까지 이어지도록
    total_duration = total_duration + 8

    # v11: 항상 enometa 프리셋 적용
    genre_preset = GENRE_PRESETS["enometa"]

    # v13: BPM을 에피소드 시드에서 결정 (하드코딩 135 제거)
    import hashlib as _hl
    # 시드 소스: episode > visual_script.metadata.episode > title
    _seed_src = episode or visual_script.get("metadata", {}).get("episode") or title
    _pre_seed = int(_hl.md5(_seed_src.encode()).hexdigest(), 16) % (2**31)
    from sequence_generators import derive_episode_sequences
    _seq_config = derive_episode_sequences(_pre_seed)
    base_bpm = _seq_config.bpm

    # ── v12: 대본 씬 종속 → 댄스 음악 자율 구조 ──
    # 대본에서 3개만 읽음: total_duration, climax_time, outro_time
    # 나머지는 음악이 자체 문법(8바/16바)으로 결정

    # climax_time: SI(semantic_intensity)가 가장 높은 씬의 시작 시점
    # SI가 없으면 emotion 이름에서 에너지 추정 (climax/awakening/tension = 고에너지)
    _EMOTION_ENERGY_HINT = {
        "climax": 1.0, "transcendent": 0.9, "awakening": 0.85, "tension": 0.8,
        "hopeful": 0.6, "neutral": 0.4, "somber": 0.3, "intro": 0.2, "fade": 0.1,
    }
    climax_time = None
    if scenes:
        best_energy = -1
        for s in scenes:
            si = s.get("semantic_intensity", s.get("energy", None))
            if si is None:
                # emotion 이름에서 추정
                emotion = s.get("emotion", "neutral")
                base_emo = emotion.split("_")[0]
                si = _EMOTION_ENERGY_HINT.get(base_emo, 0.4)
            if si > best_energy:
                best_energy = si
                climax_time = s["start_sec"]

    # outro_time: 마지막 씬의 시작 시점
    outro_time = scenes[-1]["start_sec"] if scenes else None

    climax_str = f"{climax_time:.1f}s" if climax_time is not None else "auto(60%)"
    outro_str = f"{outro_time:.1f}s" if outro_time is not None else "auto(80%)"
    print(f"  [v12] Script inputs: total={total_duration:.1f}s, climax={climax_str}, outro={outro_str}")

    # 곡 구조 자동 생성 (intro→buildup→drop→breakdown→drop2→outro)
    sections, actual_duration = _plan_song_structure(
        total_duration=total_duration,
        bpm=base_bpm,
        climax_time=climax_time,
        outro_time=outro_time,
    )
    total_duration = actual_duration

    genre_label = "enometa"  # v11: always enometa
    synthesis_overrides = {"enometa_mode": True}  # v11: always enometa mastering

    # v7-P7: 에피소드 이력 기반 키/패턴 자동 선택
    music_history = _load_music_history(project_dir) if project_dir else {"episodes": {}}
    selected_key = _select_key_from_history(music_history, genre_label)
    # v13: ARP 패턴도 시퀀스 기반 생성 (하드코딩 ARP_PATTERNS 제거)
    from sequence_generators import generate_pitch_pattern
    selected_arp = generate_pitch_pattern(_seq_config, "mid")
    arp_idx = -1  # v13: 더 이상 인덱스 기반이 아님
    key_palette = KEY_PRESETS[selected_key]

    # v9: episode 해시 기반 랜덤 시드 — 에피소드마다 다른 텍스처 패턴
    import hashlib
    ep_str = episode if episode else (title + selected_key)
    ep_hash = int(hashlib.md5(ep_str.encode()).hexdigest(), 16) % (2**31)
    random.seed(ep_hash)
    np.random.seed(ep_hash)
    print(f"  [v9] random seed={ep_hash} (episode: {ep_str})")

    # v9: SINE_MELODY_SEQUENCES를 선택된 키의 pad_root 기반으로 동적 생성
    from . import tables
    tables.SINE_MELODY_SEQUENCES = build_sine_melody_sequences(key_palette["pad_root"])
    print(f"  [v9] SINE_MELODY_SEQUENCES built for key={selected_key} (pad_root={key_palette['pad_root']:.1f}Hz)")

    if episode or project_dir:
        print(f"  [music_history] key={selected_key}, arp_pattern={arp_idx}")
        recent_eps = sorted(music_history.get("episodes", {}).keys(), reverse=True)[:2]
        if recent_eps:
            print(f"  [music_history] recent episodes: {recent_eps}")

    # 주요 악기 사용 통계 (이력 저장용)
    dominant_instruments = set()
    for sec in sections:
        for inst_key, inst_val in sec.get("instruments", {}).items():
            if isinstance(inst_val, dict) and inst_val.get("active", False):
                dominant_instruments.add(inst_key)

    # F-6: visual_script → highlight_words 전달
    highlight_words = visual_script.get("highlightWords", [])

    music_script = {
        "metadata": {
            "title": title,
            "duration": total_duration,
            "sample_rate": SAMPLE_RATE,
            "key": selected_key,
            "base_bpm": base_bpm,
            "genre": genre_label,
            "song_arc": "song_structure",  # v12: role 기반 자동 arc
            "synthesis_overrides": synthesis_overrides,
            "highlight_words": highlight_words,
            # v13: 시퀀스 설정 (렌더링 시 사용)
            "seq_config": {
                "drum_seq_type": _seq_config.drum_seq_type,
                "drum_rotation": _seq_config.drum_rotation,
                "pitch_rotation": _seq_config.pitch_rotation,
                "pitch_length": _seq_config.pitch_length,
                # v14: 음색 파라미터
                "saw_harmonics": {str(k): v for k, v in _seq_config.saw_harmonics.items()},
                "filter_cutoff_base": _seq_config.filter_cutoff_base,
                "chorus_depth_ms": _seq_config.chorus_depth_ms,
                "fm_mod_ratio": _seq_config.fm_mod_ratio,
                "bass_detune": _seq_config.bass_detune,
                "kick_character": _seq_config.kick_character,
            },
        },
        "palette": {
            "bass_freq": key_palette["bass_freq"],
            "pad_root": key_palette["pad_root"],
            "pad_fifth": key_palette["pad_fifth"],
            "arp_root": key_palette["arp_root"],
            "arp_pattern": selected_arp,
        },
        "sections": sections,
    }

    # v8 C-6: 텍스처 모듈 선택
    texture_modules = _select_texture_modules_from_history(project_dir) if project_dir else list(AVAILABLE_TEXTURE_MODULES[:4])
    music_script["metadata"]["texture_modules"] = texture_modules

    # v7-P7 + v8: 이력 저장
    if episode and project_dir:
        # 에너지 프로파일 추출 (4구간 평균)
        energy_profile = []
        if sections:
            chunk_size = max(1, len(sections) // 4)
            for ci in range(4):
                chunk = sections[ci * chunk_size: (ci + 1) * chunk_size]
                if chunk:
                    avg_e = sum(s.get("energy", 0.3) for s in chunk) / len(chunk)
                    energy_profile.append(round(avg_e, 2))

        music_history["episodes"][episode] = {
            "genre": genre_label,
            "bpm": base_bpm,
            "key": selected_key,
            "arp_pattern_idx": arp_idx,  # v13: deprecated (-1), kept for compat
            "seq_drum_type": _seq_config.drum_seq_type,
            "seq_bpm": _seq_config.bpm,
            "dominant_instruments": sorted(list(dominant_instruments)),
            "energy_profile": energy_profile,
            "num_sections": len(sections),
            "texture_modules": texture_modules,  # v8 C-6: 텍스처 모듈 이력
        }
        _save_music_history(project_dir, music_history)

    return music_script
