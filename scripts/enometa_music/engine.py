"""enometa_music/engine.py — EnometaMusicEngine 클래스"""
import json
import random
import numpy as np
from scipy.io import wavfile

from .synthesis import (
    SAMPLE_RATE, sine, noise, lowpass, highpass, bandpass,
    reverb, fade_in, fade_out, envelope,
    resonant_lowpass, resonant_bandpass,
    make_wavetable, wavetable_osc, chorus, sidechain_pump,
    stereo_pan, smooth_envelope,
)
from .instruments import (
    deep_bass_drone, modular_click, bit_crush, fm_bass,
    noise_burst, stutter_gate, tape_stop,
    kick_drum, hi_hat, snare_drum, transition_impact,
    synth_lead, soft_clip, sawtooth, sawtooth_distorted, saw_sequence,
)
from .textures import (
    BYTEBEAT_FORMULAS, bytebeat, chiptune_square, chiptune_noise_drum,
    feedback_loop, wavefold, euclidean_rhythm, glitch_texture,
    arpeggio_sequence, metallic_hit, noise_sweep, sub_pulse, reverse_swell,
    numbers_to_euclidean, gate_pattern_from_si, stutter_from_data,
    sine_interference, data_click, pulse_train, granular_cloud,
    ultrahigh_texture, acid_bass,
)
from .tables import (
    EMOTION_MAP, SINE_MELODY_SEQUENCES, EMOTION_TO_MELODY,
    SONG_ARC_PRESETS, GENRE_PRESETS, ARRANGEMENT_TABLE,
    ROLE_ENERGY, ROLE_BAR_RATIOS,
    MUSIC_MOOD_PRESETS, CRASH_RULES, FILL_RULES, GAP_FILL_INTENSITY,
    DEFAULT_MUSIC_MOOD,
)


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
            )
        else:
            # fallback: 시드 42
            self.seq_config = derive_episode_sequences(42)

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
        최소 BPM 120 보장.
        """
        fixed_bpm = max(float(self.bpm), 120.0)
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

    def _render_continuous_bass(self, sections):
        """전체 길이 베이스 드론 — 볼륨만 섹션별 모핑"""
        print("  [bass] continuous drone...", flush=True)
        drone = deep_bass_drone(self.bass_freq, self.duration, self.sr,
                                detune=self.seq_config.bass_detune)
        vol_env = smooth_envelope(
            len(drone), sections, "bass_drone", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        drone *= vol_env * self._si_gate[:len(drone)] * 1.2  # v7-P8: si gate
        # 전체 시작/끝 페이드
        drone = fade_in(fade_out(drone, 3.0), 2.0)
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
        fm *= vol_env * self._si_gate[:len(fm)] * 1.0  # v7-P8: si gate
        fm = fade_in(fade_out(fm, 2.0), 1.5)
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
            section_drum_pat[sid] = generate_drum_pattern(self.seq_config, role, si_avg)

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

            # v13: 패턴 결정 — 시퀀스 기반 or 필인
            if drop_state == 1:
                pat = generate_fill_pattern(self.seq_config, "drop_impact")
                drop_state = 0
            elif is_near_drop and drop_state == 0:
                pat = generate_fill_pattern(self.seq_config, "drop_silence")
                drop_state = 1
            elif cur_role == "buildup" and is_near_drop:
                pat = generate_fill_pattern(self.seq_config, "fill_snare_roll")
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

        si_g = self._si_gate[:self.total_samples]
        # F-7: 콜앤리스폰스 드럼 엔벨로프
        cr_d = self._cr_drum_env[:self.total_samples] if hasattr(self, '_cr_drum_env') else 1.0
        self.master_L += kick_full * kick_vol_env * si_g * cr_d * 2.5
        self.master_R += kick_full * kick_vol_env * si_g * cr_d * 2.5
        self.master_L += snare_full * snare_vol_env * si_g * cr_d * 1.2
        self.master_R += snare_full * snare_vol_env * si_g * cr_d * 1.2
        self.master_L += hihat_full_L * hihat_vol_env * si_g * cr_d * 2.2
        self.master_R += hihat_full_R * hihat_vol_env * si_g * cr_d * 2.2
        # v12: 전환 임팩트 — 킥 볼륨 엔벨로프 공유, 약간 더 크게
        self.master_L += impact_full * kick_vol_env * si_g * 3.0
        self.master_R += impact_full * kick_vol_env * si_g * 3.0

    def _render_continuous_sub_pulse(self, sections):
        """전체 길이 서브 펄스"""
        print("  [sub] continuous sub pulse...", flush=True)
        sub = sub_pulse(self.bass_freq * 0.5, self.duration, self.bpm, self.sr)
        vol_env = smooth_envelope(
            len(sub), sections, "sub_pulse", "volume",
            default=0.0, morph_sec=0.8, sr=self.sr
        )
        sub *= vol_env * self._si_gate[:len(sub)] * 0.7  # v7-P8: si gate
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
            speed=avg_speed, sr=self.sr, bpm=self.bpm,
            apply_chorus=True, chorus_depth_ms=self.seq_config.chorus_depth_ms
        )
        vol_env = smooth_envelope(
            len(arp), sections, "arpeggio", "volume",
            default=0.0, morph_sec=1.0, sr=self.sr
        )
        arp *= vol_env * self._si_gate[:len(arp)] * 1.2  # v7-P8: si gate

        # 디튠 스테레오 쌍
        arp2 = arpeggio_sequence(
            self.arp_root + 1, self.duration,
            [p * 1.01 for p in self.arp_pattern],
            speed=avg_speed * 1.02, sr=self.sr
        )
        arp2 *= vol_env * self._si_gate[:len(arp2)] * 0.7  # v7-P8: si gate

        self._add_stereo(arp, -0.3, 0, 1.0)
        self._add_stereo(arp2, 0.3, 0.05, 1.0)

    # ---- Ikeda 전용 연속 렌더러 ----

    def _render_continuous_sine_interference(self, sections):
        """v8: 전체 길이 사인파 간섭 드론 — 감정별 멜로디 시퀀스 + 4마디 주파수 전환"""
        print("  [sine_interference] v8 melodic interference drone...", flush=True)
        bpm = self.script.get("metadata", {}).get("base_bpm", 60)
        bar_duration = (60.0 / bpm) * 4  # 4/4 박자 1마디
        fade_sec = 0.1  # 주파수 쌍 전환 크로스페이드

        # script_data에서 기본 주파수 쌍 추출 (fallback용)
        base_freq_pairs = []
        if self._script_data:
            freq_map = self._script_data.get("global", {}).get("freq_map", {})
            freqs = sorted(set(freq_map.values()))
            if len(freqs) >= 2:
                for i in range(len(freqs) - 1):
                    base_freq_pairs.append((freqs[i], freqs[i + 1]))
        if not base_freq_pairs:
            base_freq_pairs = [(220, 223), (440, 443)]  # 기본 3Hz 비팅

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
            sec_duration = sec_end - sec_start
            num_bars_in_section = max(1, int(sec_duration / bar_duration))
            chunk_bars = 4  # 4마디마다 전환

            local_pos = 0
            chunk_idx = 0
            while local_pos < (s1 - s0):
                # 현재 chunk의 주파수 쌍
                pair_idx = chunk_idx % len(melody_seq)
                f1, f2 = melody_seq[pair_idx]

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
        total *= vol_env * self._si_gate[:len(total)]  # v7-P8: si gate

        # 비주얼 데이터 수집
        self._sine_interference_raw[:len(total)] = total

        # 스테레오: L/R에 미세하게 다른 디튠
        total_L = total.copy()
        total_R = total.copy()
        detune = np.sin(2 * np.pi * 220.5 * t) * 0.05
        total_R += detune[:self.total_samples]

        total = fade_in(fade_out(total, 3.0), 2.0)
        total_L = fade_in(fade_out(total_L, 3.0), 2.0)
        total_R = fade_in(fade_out(total_R, 3.0), 2.0)
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
        texture *= vol_env * self._si_gate[:len(texture)]  # v7-P8: si gate
        texture = fade_in(fade_out(texture, 2.0), 1.0)
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

        pt = fade_in(fade_out(pt, 2.0), 1.0)
        # 좌우 약간 다른 위치에 배치 (스테레오 width)
        self._add_stereo(pt, random.uniform(-0.3, 0.3), 0, 1.0)

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

        fixed_gate_div = GATE_DIV[fixed_pat_key]
        fixed_note_len = 0.85 if fixed_pat_key in ["low", "mid"] else 0.6

        # v13: Norgard 수열에서 3개 변형 생성 (4바 로테이션)
        base_pitch_pat = generate_pitch_pattern(self.seq_config, fixed_pat_key)
        pat_list = [
            base_pitch_pat,
            seq_rotate(base_pitch_pat, 2),
            seq_rotate(base_pitch_pat, len(base_pitch_pat) // 2),
        ]
        print(f"  [saw_seq] v13 sequence pitch: {fixed_pat_key} (avg_energy={avg_energy:.2f}, pat_len={len(base_pitch_pat)})", flush=True)

        # 전체 길이를 4바 청크로 연속 렌더링 (섹션 경계 무시)
        bar_dur = (60.0 / bpm) * 4  # 4/4 1바 길이
        chunk_bars = 4  # 4바마다 패턴 로테이션
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
            _si_val = float(self._si_gate[_si_idx]) if self._si_gate is not None else 0.5
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
        saw_L *= vol_env * self._si_gate[:self.total_samples] * cr_m
        saw_R *= vol_env * self._si_gate[:self.total_samples] * cr_m

        # v14: 코러스로 스테레오 풍부함 추가
        saw_L = chorus(saw_L, sr=self.sr, depth_ms=self.seq_config.chorus_depth_ms)
        saw_R = chorus(saw_R, sr=self.sr, depth_ms=self.seq_config.chorus_depth_ms, lfo_rate=1.7)

        saw_L = fade_in(fade_out(saw_L, 2.0), 0.5)
        saw_R = fade_in(fade_out(saw_R, 2.0), 0.5)

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
        gate_L *= vol_env * self._si_gate[:self.total_samples]
        gate_R *= vol_env * self._si_gate[:self.total_samples]

        gate_L = fade_in(fade_out(gate_L, 2.0), 0.3)
        gate_R = fade_in(fade_out(gate_R, 2.0), 0.3)

        self.master_L += gate_L
        self.master_R += gate_R

    def _insert_gap_events(self, drops: list, mood: str = "raw"):
        """v15: drops[] 구간에 무드별 강도로 gap_burst/stutter 삽입.
        drops: [{"start_sec": X, "end_sec": Y}, ...]
        SEC_PER_BAR는 음악 BPM에서 동적 계산.
        """
        intensity = GAP_FILL_INTENSITY.get(mood, 0.5)
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

            # 1마디 이상: gap_burst (기존 활용)
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
                end_sec = drop["end_sec"]
                impact_start = max(0, end_sec - 0.05)
                impact = transition_impact(0.3, self.sr)
                impact *= intensity * 0.5
                pos = int(impact_start * self.sr)
                end_p = min(pos + len(impact), self.total_samples)
                length = end_p - pos
                self.master_L[pos:end_p] += impact[:length]
                self.master_R[pos:end_p] += impact[:length]

    def apply_mood_to_sections(self, sections: list, mood: str, drum_override: bool | None = None):
        """v15: 무드 프리셋에 따라 섹션별 instrument active/volume 적용.
        drum_override: True=강제 ON, False=강제 OFF, None=무드 기본값
        """
        preset = MUSIC_MOOD_PRESETS.get(mood, MUSIC_MOOD_PRESETS[DEFAULT_MUSIC_MOOD])
        mood_layers = preset["layers"]

        # 드럼 기본값 결정
        if drum_override is None:
            drum_on = preset.get("drum_default", True)
        else:
            drum_on = drum_override

        drum_layers = {"kick", "snare", "hi_hat"}

        print(f"  [mood] {mood}: drum={'ON' if drum_on else 'OFF'}", flush=True)

        for section in sections:
            instruments = section.setdefault("instruments", {})

            for layer_name, config in mood_layers.items():
                if layer_name in drum_layers:
                    # 드럼 레이어: drum_on으로 결정
                    instruments[layer_name] = dict(config, active=drum_on and config.get("active", True))
                else:
                    instruments[layer_name] = dict(config)

        return sections
