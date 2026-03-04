# ENOMETA Generative Music Engine — Claude Code 실행 문서 (2026-03-04)

> Pure Python 전자음악 엔진 — Raw Synthesis, GPU 불필요
> numpy + scipy만으로 동작.
> **last_updated**: 2026-03-04 — v10.2: si_gate 연속 함수(min 0.45, 1.0s 스무딩) — 계단 함수/급감쇠 금지
> v9→v10: SI 변조 95~105%로 안정화, density_scale max(0.6,si), 마스터링 강화(tanh 3.0, -6dB), song arc 에너지 상향
> v10.1 (EP007): BGM duration = total_duration + 8 (endcard 6초 + 2초 buffer), outro energy 0.1→0.2
> v10.2 (EP007 피드백): si_gate 계단 함수 → 연속 함수 교체, 급변/급감쇠 방지

---

## 개요

대본 텍스트를 입력하면 Claude Code가 감정을 분석하고,
visual_script.json + narration_timing.json → music_script.json 자동 생성 → WAV 출력.

```
script.txt + narration_timing.json
  │
  ▼
visual_script_generator.py (감정 분석 + music_script.json 생성)
  │
  ▼
music_script.json (섹션별 감정, 에너지, 악기 파라미터)
  │
  ▼
enometa_music_engine.py v8 (numpy + scipy)
  │
  ▼
bgm.wav (44100Hz, 16bit, Stereo)
```

- 소요 시간: 60초 음악 생성에 약 2~3초 (CPU only)
- 의존성: numpy, scipy (`pip install numpy scipy`)
- GPU: 불필요
- 장르: ikeda 단일 (v8, `--genre` 옵션 무시됨)

---

## 합성 함수 (9종: v5 6개 + v6 3개)

### 1. bytebeat(formula_id, duration, sr)
시간 변수 t에 비트연산을 적용해 원시 파형 생성.
8000Hz 생성 → 44100Hz 리샘플 (lo-fi 유지).
내장 공식 12개 (Viznut 클래식 + 커스텀).

### 2. chiptune_square(freq, duration, duty, sr)
듀티사이클 조절 스퀘어 웨이브. 4bit 양자화.
duty=0.5: 정통, duty=0.125~0.875: 펄스파 (NES).

### 3. chiptune_noise_drum(drum_type, sr)
LFSR 노이즈 기반 퍼커션. kick/snare/hihat.
피치 엔벨로프 + 볼륨 엔벨로프로 차별화.

### 4. feedback_loop(seed_signal, iterations, feedback_gain, distortion_fn, sr)
신호를 자기 자신에 되먹임 — 카오틱/산업적 텍스처.
distortion_fn: soft_clip, wavefold, bit_crush 선택.

### 5. wavefold(signal, folds)
파형 접기 — 모듈러 신스 핵심 디스토션.
신호가 ±1 경계를 넘으면 반사(fold back).

### 6. euclidean_rhythm(steps, pulses)
유클리드 리듬 — N스텝에 K펄스를 최대한 균등 배치.
Bjorklund 알고리즘. E(3,8), E(5,8) 같은 비대칭 리듬.

### 7. sine_interference(freq1, freq2, duration, sr) — v6 신규
순수 사인파 2개의 합 → 비팅(beating) 간섭 패턴 자동 생성.
`sin(2π·f1·t) + sin(2π·f2·t)` → `|f1-f2|` Hz 맥놀이.
script_data의 숫자가 주파수 결정 (70Hz + 120Hz → 50Hz 비팅).

### 8. data_click(freq, sr) — v6 신규
극초단 (0.003s) 정밀 클릭, 1사이클 사인파 버스트.
주파수가 대본 숫자를 인코딩 (70Hz, 120Hz, 83.3Hz...).
기존 modular_click과 다름: 랜덤 아닌 데이터 기반.

### 9. ultrahigh_texture(duration, center_freq, bandwidth, sr) — v6 신규
8-20kHz 초고주파 텍스처, 매우 조용 (0.05-0.15 진폭).
대역통과 필터링된 노이즈, "디지털 공기" 역할.

---

## 악기 어휘 (Musical Vocabulary) — v8 (26종)

### 연속 렌더링 악기 (Continuous)

```
deep_bass_drone      딥 베이스 드론 (40-80Hz), 볼륨 ×1.2
fm_bass              FM 합성 베이스 (2-op), 볼륨 ×1.0
arpeggio_sequence    시퀀서 아르페지오 (타일링 최적화), 볼륨 ×1.2
sub_pulse            서브 베이스 펄스 (사이드체인), 볼륨 ×0.7
kick_drum + hi_hat   리듬 섹션 (타일링 최적화)
                     v5: euclidean 리듬 모드 추가 (algorave 장르)
```

### 텍스처/이벤트 악기 (Per-section)

```
modular_click        모듈러 신스 클릭
glitch_texture       글리치 텍스처 v5 (6종 이벤트: sine/bitcrush/stutter/noise/feedback/wavefold)
noise_sweep          노이즈 스윕 (하모닉 엔벨로프)
noise_burst          짧은 노이즈 히트
metallic_hit         금속성 타격
synth_lead           신스 리드 (4 하모닉스)
acid_bass            애시드 베이스 (하모닉 엔벨로프 + soft_clip)
reverse_swell        리버스 스웰
silence_break        의도적 무음
bytebeat             v5 신규 — 비트연산 공식 오디오 (12개 공식)
feedback             v5 신규 — 자기참조 피드백 루프 텍스처
chiptune_lead        v5 신규 — 듀티사이클 스퀘어 리드 + 4bit 양자화
chiptune_drum        v5 신규 — LFSR 노이즈 퍼커션 (kick/snare/hihat)
sine_interference    v6 신규 — 2개 사인파 합 → 맥놀이 (ikeda 장르 핵심)
data_click           v6 신규 — 대본 숫자 인코딩 정밀 클릭 (ikeda 장르)
ultrahigh_texture    v6 신규 — 8-20kHz 초고주파 디지털 텍스처 (ikeda 장르)
```

### 이펙트 / 프로세서

```
bit_crush            비트 감소 + 다운샘플링
stutter_gate         리듬 볼륨 게이팅
tape_stop            테이프 정지 (피치 다운)
soft_clip            소프트 클리핑 (np.tanh)
wavefold             v5 신규 — 파형 접기 디스토션
reverb               공간 리버브
stereo_pan           스테레오 패닝
envelope             ADSR 엔벨로프
```

---

## 장르 프리셋 (v9: ikeda 단일)

| 장르 | BPM | 핵심 사운드 | synthesis_overrides |
|------|-----|------------|---------------------|
| **ikeda** | **135** (±20%) | 쏘우파+스퀘어 brutal + 사인 간섭 + 데이터 클릭 + gap burst | ikeda_mode: True, rhythm_mode: euclidean |

> BPM은 SI 기반 가변: `section_bpm = 135 × (0.80 + si_avg × 0.40)` → 108~162 BPM 범위

### v9 ikeda 10레이어 구조

| 레이어 | 함수 | 역할 |
|--------|------|------|
| 1 | `_render_continuous_rhythm` | 킥/하이햇 리듬 백본 |
| 2 | `_render_continuous_saw_sequence` | 쏘우파 게이트 시퀀서 ('뚜두두') |
| 3 | `_render_continuous_arpeggio` | 고음역 아르페지오 |
| 4 | `_render_continuous_bass` | 서브 베이스 드론 |
| 5 | `_render_continuous_sub_pulse` | 서브 펄스 |
| 6 | `_render_continuous_sine_interference` | 사인파 간섭 (맥놀이) |
| 7 | `_render_continuous_pulse_train` | 펄스 트레인 |
| 8 | `_render_continuous_ultrahigh` | 8-20kHz 초고주파 텍스처 |
| 9 | `_render_continuous_gate_stutter` | **SI/data_density/numbers 연동** — 게이트+유클리드+스터터+다파형 |
| 10 | `_render_gap_stutter_burst` | **무음 구간 brutal burst** — 나레이션 gap에 쏘우+스퀘어 삽입 |

### SI 기반 레이어 밀도 제어 (v10)
```
density_scale = max(0.60, si)      ← v10: 최소 60% 보장 (v9: si^1.5 최소 0.05%)
적용 레이어: saw_sequence, arpeggio, pulse_train, ultrahigh, sine_interference, gate_stutter
si=0.25 → density_scale=0.60 (v9: 0.09 → v10: 60% — 조용한 구간도 충분히 들림)
si=0.50 → density_scale=0.60 (최소 하한)
si=1.00 → density_scale=1.00 (최대)
```

### SI 변조 시스템 (v10)
```
v9: self._si_modulation = 0.7 + self._si_env * 0.6   (70%~130%)
v10: self._si_modulation = 0.95 + self._si_env * 0.1  (95%~105%)
변동폭 축소 → 조용한 구간에서도 음악이 과도하게 감쇠되지 않음
```

### 레이어 9: gate_stutter 다파형 매핑
| SI 구간 | 파형 | drive |
|---------|------|-------|
| si < 0.30 | sine (clean) | — |
| 0.30 ≤ si < 0.55 | sawtooth | — |
| 0.55 ≤ si < 0.75 | sawtooth_distorted | 2.5~5.5 |
| si ≥ 0.75 | saw + square (brutal) | 4.5~8.5 |

### 레이어 10: gap_stutter_burst 설계 (v9 신규)
```
조건: 나레이션 세그먼트 사이 gap_dur ≥ 30ms
에너지: (prev_seg.si + next_seg.si) / 2 = burst_energy
파형: sawtooth_distorted + chiptune_square(×0.5)
drive: 5.0 + burst_energy × 5.0  → 5.0~10.0 (항상 brutal)
gate: si=1.0 기준 32분음표 (최대 스터터)
fade: 5ms in/out (클릭 방지)
vol: 0.5 + burst_energy × 0.35  → 0.50~0.85
```

### v9→v10 주요 변경 (2026-03-03)
- **SI 변조 안정화**: `0.7+si*0.6` → `0.95+si*0.1` — 변동폭 60% → 10%로 축소
- **density_scale 하한 보장**: `si^1.5` → `max(0.6, si)` — 최소 60% 보장
- **마스터링 강화**: tanh drive `1.2` → `3.0`, RMS target `-10dB` → `-6dB` (+4dB)
- **Song arc 에너지 전체 상향**: intro 0.25~0.45→0.7~0.9, buildup 0.45~0.85→0.9~1.2, climax 0.85~1.2→1.2~1.5
- **킥/하이햇 볼륨**: 킥 `si_g*1.2`→`si_g*2.5`, 하이햇 `si_g*1.0`→`si_g*1.8`
- **saw_sequence 볼륨**: default `0.4`→`0.7`

### v8→v9 주요 변경
- **유클리드 리듬** (from algorave): numbers 리스트 → Bjorklund 알고리즘 → 비대칭 게이트 패턴
- **다파형 스터터**: si 구간별 sine→saw→distorted→brutal 자동 전환
- **SINE_MELODY_SEQUENCES**: 감정별 5종 멜로디 시퀀스, key_palette 기반 동적 생성
- **에피소드 해시 시드**: `random.seed(42)` 제거 → `hashlib.md5(episode_id)`

### 비주얼 레이어 연동 (v9: ikeda 전용)
ikeda 프리셋: Music 3 + TTS 4 = 7레이어, blend_ratio=0.45, SI_INTENSITY_SCALE 실시간 스케일. 상세: `ENOMETA_Hybrid_Visual_Architecture_20260304.md` 참조

---

## v10 마스터링 체인 (ikeda 전용)

```python
def _master(self) -> np.ndarray:
    stereo = np.column_stack([self.master_L, self.master_R])

    # v10: ikeda 전용 마스터링 강화 (v8 대비 drive/RMS 상향)
    # 1. 피크 노멀라이즈
    # 2. 소프트 새츄레이션 (tanh drive=3.0)  ← v9: 1.2
    # 3. RMS 노멀라이즈 (target -6dB, RMS=0.5)  ← v9: -10dB, RMS=0.316
    # 4. 피크 리미팅 (0.95 ceiling)
    # 5. 페이드 + 16bit 변환

# 후처리: audio_mixer.py에서 EBU R128 loudnorm 적용
# loudnorm=I=-14:TP=-1.5:LRA=11 (클리핑 방지)
```

---

## v5 성능 최적화

### smooth_envelope O(n) 최적화
```
v4: np.convolve(env, kernel, 'same') → O(n*m), 4.5M × 44K = 무한 행
v5: cumsum 이동평균 → O(n), 즉시 완료
```

### 패턴 타일링 (v4에서 유지)
```
1 bar pre-render → np.tile() → 볼륨 엔벨로프 곱셈
적용: arpeggio, sub_pulse, kick_drum + hi_hat
```

---

## CLI 사용법

```bash
# v8: ikeda 단일 장르 + export-raw + script-data + arc
py scripts/enometa_music_engine.py \
  --from-visual episodes/epXXX/visual_script.json \
  --export-raw --arc narrative \
  --script-data episodes/epXXX/script_data.json \
  --episode epXXX \
  episodes/epXXX/narration_timing.json \
  episodes/epXXX/bgm.wav

# --export-raw: raw_visual_data.npz 동시 출력 (Hybrid 비주얼 엔진용)
# --script-data: 대본 데이터 기반 주파수/클릭 밀도 자동 설정
# --arc: Song Arc 프리셋 (narrative|crescendo|flat|adaptive, 기본: narrative)
# --episode: 에피소드 식별자 (music_history.json 이력 추적용)
# --genre: (v8 무시됨, 항상 ikeda)
```

### Song Arc 시스템 (v6.1)

음악 1곡에 매크로 에너지 엔벨로프를 적용하여 기승전결 구조를 만든다.
기존 섹션별 에너지 시스템 위에 곱해지는 **상위 레이어**이므로 하위호환 유지.

| 아크 | 구간 | 에너지 범위 |
|------|------|------------|
| **narrative** | intro(0-15%) → buildup(15-55%) → climax(55-80%) → outro(80-100%) | 0.7~1.5 (v10 상향) |
| crescendo | grow(0-85%) → release(85-100%) | 0.2~1.1 |
| flat | constant(0-100%) | 1.0 (아크 없음) |
| **adaptive** | si 곡선 기반 동적 경계 (intro→buildup→climax→outro, script_data 필수) | 0.25~1.2 |

- `_compute_song_arc()`: 페이즈별 np.linspace → 연결 → cumsum 1.5s smoothing, adaptive 분기
- `_build_arc_from_phases()`: phase 리스트 → 에너지 엔벨로프 공통 로직 (v7-P2)
- `_compute_adaptive_arc()`: si 곡선 3s heavy smoothing → 피크 탐지 → 동적 phase 경계 (v7-P2)
- `_get_arc_phase_at()`: 시간 → 페이즈 이름 반환 (adaptive phases 지원)
- `generate()`: 마스터 버퍼에 아크 엔벨로프 곱셈 (flat 아닌 경우)
- `export_raw_visual_data()`: npz에 `arc_energy`(float), `arc_phases`(string) 배열 추가
- `generate_music_script()`: metadata에 `"song_arc": "narrative"` 기본값

### Adaptive Song Arc (v7-P2)

si 곡선에서 실제 내러티브 구조를 자동 추출하여 음악의 기승전결을 대본과 정렬한다.

**알고리즘**:
1. si 곡선을 3초 window cumsum smoothing → 매크로 구조 추출
2. 글로벌 피크 위치 → 클라이맥스 중심점 (30~80% 클램프)
3. si 다이나믹 레인지 < 0.08 → narrative fallback (플랫 대본)
4. 피크 기준 비례 배분: intro=peak×30%, climax=peak±8%, 나머지 buildup/outro

**Fallback**: script_data 없거나 si 변화 폭 부족 → narrative preset 사용

**CLI**: `--arc adaptive` (script_data 필수, 없으면 자동 narrative fallback)

### 박자 정렬 시스템 (v7-P4)

`generate_music_script()`에서 음악 섹션 경계를 **마디(bar) 경계로 퀀타이즈**.
비주얼 씬 경계(나레이션 타이밍)는 그대로 유지, 음악 섹션만 정렬.

```
bar_duration = (60 / bpm) * 4    # 4/4 박자 1마디 길이 (초)
quantized = round(time / bar_duration) * bar_duration
```

| 장르 | BPM | 1마디 길이 |
|------|-----|-----------|
| ikeda | 60 | 4.000초 |

- `_quantize_to_bar(time_sec, bar_duration)`: 반올림 퀀타이즈 헬퍼
- 첫 섹션: start = 0.0 고정
- 일반 섹션: end를 가장 가까운 마디로, 최소 1마디 길이 보장
- outro: end를 올림 퀀타이즈 (`math.ceil`)
- 인접 섹션 연속성 보장: `sections[i+1].start = sections[i].end`
- 원본 경계 보존: `_original_start_sec`, `_original_end_sec` 필드

### 감정 전환 크로스페이드 (v7-P5)

섹션별 텍스처 악기의 **기여분(delta)에만** fade-in/fade-out을 적용하여 씬 전환 시 부드러운 크로스페이드를 만든다.
연속 악기(bass, arp 등)는 영향받지 않음 — 텍스처 기여분만 정밀 페이드.

```
fade_duration = min(0.5, section_duration × 0.15)  # 최대 0.5초 또는 15%
```

**구현**: `_render_section_textures()` 에서 렌더 전 마스터 스냅샷 → 렌더 후 delta 추출 → fade 적용 → 복원

### Pulse Train / Granular 합성 (v7-P9)

Ikeda 특유의 "뚜두두두두" 고속 클릭 반복 사운드를 구현하는 2개의 합성 함수 + 1개의 연속 렌더러.

**합성 함수 2종:**
- `pulse_train(click_freq, repeat_rate, duration, rate_curve)`: 극초단 클릭(`data_click`)을 가변 속도로 반복 배치
  - `rate_curve`: si 연동 시 `20 + si * 180` (si=0 → 20Hz 느린 클릭, si=1 → 200Hz 급속 버즈)
  - 클릭 겹침 방지: `pos += max(interval, click_len + 1)`
- `granular_cloud(source_signal, grain_size_ms, density, scatter)`: Hanning window grain 추출 → 재배열
  - 균일(scatter=0) ~ 완전 랜덤(scatter=1) 배치

**연속 렌더러:**
- `_render_continuous_pulse_train(sections)`: si 기반 rate_curve + 대본 숫자 → click_freq, 그래뉼러 서브레이어
  - ikeda 모드에서만 호출 (`generate()` ikeda 분기)
  - EMOTION_MAP에서 `pulse_train.volume` → `smooth_envelope()` 모핑

**EMOTION_MAP 추가:**
| 감정 | pulse_train.volume |
|------|-------------------|
| tension | 0.3 |
| tension_peak | 0.5 |
| awakening | 0.35 |
| awakening_climax | 0.45 |
| transcendent | 0.2 |

### 에피소드 간 음악 이력 추적 (v7-P7)

`music_history.json`으로 에피소드별 음악 특성을 추적, 다음 에피소드에서 키/패턴 자동 다양화.

**KEY_PRESETS (7키)**:
| 키 | bass_freq | pad_root | pad_fifth | arp_root |
|----|-----------|----------|-----------|----------|
| C_minor | 65.4 | 261.6 | 392.0 | 196.0 |
| D_minor | 73.4 | 293.7 | 440.0 | 220.0 |
| E_minor | 82.4 | 329.6 | 493.9 | 220.0 |
| F_minor | 87.3 | 349.2 | 523.3 | 233.1 |
| G_minor | 98.0 | 392.0 | 587.3 | 261.6 |
| A_minor | 110.0 | 440.0 | 659.3 | 293.7 |
| Bb_minor | 116.5 | 466.2 | 698.5 | 311.1 |

**ARP_PATTERNS (5종)**: 상행-하행, 변형A, 하행-상행, 변형B, 옥타브점프

**이력 기반 자동 선택**:
- `_select_key_from_history()`: 최근 2개 에피소드와 다른 키 자동 선택 (KEY_PRIORITY 순위)
- `_select_arp_pattern_from_history()`: 최근 2개와 다른 아르페지오 패턴 선택
- `generate_music_script()`에 `episode`, `project_dir` 매개변수 추가
- `--episode ep006` CLI 옵션 → music_history.json에 자동 기록

**music_history.json 형식**:
```json
{
  "episodes": {
    "ep005": {
      "genre": "ikeda", "bpm": 60, "key": "E_minor",
      "arp_pattern_idx": 0,
      "dominant_instruments": ["data_click", "sine_interference", ...],
      "energy_profile": [0.3, 0.5, 0.8, 0.4],
      "num_sections": 13
    }
  }
}
```

- `lookback_window = 2` (vocab_history와 동일)
- `--episode` 없으면 이력 저장 안 함 (하위호환)

### 연속 악기 si 게이트 (v7-P8 → v10.2 리라이트)

조용한 구간(si 낮음)에서 연속 악기(bass, arp, rhythm 등) 볼륨을 자동 감쇠하여 다이나믹 레인지를 확보한다.

```
v10.2 연속 함수 (EP007 피드백으로 교체):
  gate = 0.45 + si * 1.1    (min 0.45, max ~1.55 → clamp 1.0)
  + 1.0초 cumsum 스무딩     (급변 방지)

⚠ 금지 사항:
  - 계단 함수 금지 (si<0.15→0.1 같은 극단적 감쇠 금지)
  - 최소값 0.45 미만 금지
  - 스무딩 1.0초 미만 금지 (0.3초는 급변 유발)
```

**적용 대상**: 모든 7개 연속 렌더러
- `_render_continuous_bass`: `drone *= vol_env * si_gate * 1.2`
- `_render_continuous_fm_bass`: `fm *= vol_env * si_gate * 1.0`
- `_render_continuous_rhythm`: kick/hihat에 si_gate 곱셈
- `_render_continuous_sub_pulse`: `sub *= vol_env * si_gate * 0.7`
- `_render_continuous_arpeggio`: arp/arp2에 si_gate 곱셈
- `_render_continuous_sine_interference`: `total *= vol_env * si_gate`
- `_render_continuous_ultrahigh`: `texture *= vol_env * si_gate`

**구현**:
- `_build_si_gate()`: si_env → 연속 함수 `0.45 + si * 1.1` + 1.0초 스무딩
- `generate()`에서 si_modulation 직후 `self._si_gate = self._build_si_gate()` 계산
- script_data 없으면 gate = 1.0 전체 (무변조, 하위호환)

### 가변 BPM 시스템 (v7-P6)

`_compute_tempo_curve()` — si 기반 섹션별 BPM 변조 (±15% 범위).
조용한 대사는 느린 템포, 격렬한 대사는 빠른 템포로 음악의 표현력 확장.

```
section_bpm = base_bpm × (0.85 + si_avg × 0.30)
  si=0.0 → 85% BPM (느림)    si=0.5 → 100% BPM (기본)    si=1.0 → 115% BPM (빠름)
+ 0.5초 cumsum 스무딩 (섹션 경계 자연스러운 전환)
```

**BPM 변동 범위 (ikeda)**:

| 장르 | base_bpm | si=0 (85%) | si=1 (115%) |
|------|----------|-----------|-------------|
| ikeda | 60 | 51.0 | 69.0 |

**가변 BPM 적용 대상**:
- `_render_continuous_rhythm()`: 이벤트 기반 배치 — 비트마다 `bpm_at(t)` 조회하여 간격 결정
- `_render_section_textures()` acid_bass: `beat_interval = 60 / section_bpm`
- `_render_section_textures()` chiptune_drum: `beat_interval = 60 / section_bpm`
- `_render_section_textures()` stutter_gate: `section_bpm` 전달
- `_section_bpm(section)`: 섹션 시간 범위의 평균 BPM 조회 헬퍼

**비주얼 연동**:
- `export_raw_visual_data()`: `tempo_curve` 프레임별 BPM 배열 추가 (npz)
- 비주얼 엔진에서 현재 BPM 참조 가능

**하위호환**: script_data 없으면 tempo_curve = base_bpm 균일 (무변조)

### script_data 활용 (v8: ikeda 전용)

`_script_data_enrichment(sections)` — script_data의 숫자/키워드/밀도를 ikeda 엔진에서 활용.
대본 데이터가 음악의 주파수, 클릭 밀도, 텍스처 모듈 파라미터에 직접 반영된다.

| 활용 요소 | 변조 대상 |
|----------|----------|
| freq_map, numbers | sine_interference 주파수쌍, data_click 주파수 |
| data_density | click 밀도, pulse_train rate |
| si → gain/iterations | 텍스처 모듈 피드백 (고긴장 구간) |
| numbers 합 → 공식 인덱스 | bytebeat 미세 텍스처 공식 선택 |

- `generate()` 에서 si_env 빌드 후, arc 계산 전에 호출
- script_data 없으면 무동작 (하위호환)

### semantic_intensity → 음악 변조 시스템 (v7-P1)

`script_data.json`의 `segments[].semantic_intensity` (0~1)를 음악 에너지에 실시간 반영.
비주얼과 동일한 si 데이터 소스를 음악이 공유 → **음악-비주얼-대사 삼위일체** 달성.

```
볼륨 변조: final_volume = base_volume × (0.7 + si × 0.6)
  si=0.0 → 70% (조용)    si=0.5 → 100% (기본)    si=1.0 → 130% (격렬)

밀도 변조: final_density = base_density × (0.5 + si)
  si=0.0 → 50% (희박)    si=0.5 → 100% (기본)    si=1.0 → 150% (밀집)
```

- `_build_si_envelope()`: segments → 시간 도메인 numpy 배열, 0.5초 cumsum 스무딩
- `generate()`: Song Arc 적용 후 `master_L/R *= si_modulation` (마스터 볼륨 변조)
- `_render_section_textures()`: `si_density_mod`로 클릭/글리치/노이즈/메탈릭 밀도 변조
- script_data 없으면 si=0.5(neutral) → 무변조 (하위호환)

---

## script_data_extractor.py 출력 형식 (v6.2 변경)

음악 엔진이 `--script-data`로 소비하는 `script_data.json`의 형식이 v6.2에서 확장됨.
**음악 엔진 코드 자체는 미변경** — 기존 필드(numbers, chemical_formulas, utf8_bytes 등)는 동일하게 유지됨.

### v6.2 추가 필드
각 키워드 엔트리에 `intensity` 필드가 추가됨:
```json
{
  "keywords": [
    {
      "text": "공포",
      "start": 5.2,
      "end": 6.1,
      "type": "emotion",
      "intensity": 0.9
    },
    {
      "text": "폭발",
      "start": 12.3,
      "end": 13.0,
      "type": "verb",
      "intensity": 0.95
    }
  ],
  "segments": [
    {
      "text": "공포와 각성의 화학식은 같다",
      "start": 5.0,
      "end": 8.5,
      "semantic_intensity": 0.72,
      "numbers": [...],
      "utf8_bytes": [...]
    }
  ]
}
```

### semantic_intensity 계산 (compute_semantic_intensity) — v2 대폭 확장
- **VERB_ENERGY** (101개): "폭발"(0.9) ~ "있"(0.1) — 파괴/변혁/인지/상태 전 범위
- **EMOTION_INTENSITY** (68개): "공포"(0.9) ~ "정적"(0.1) — 극단~잔잔함 5단계
- **SCIENCE_TERMS** (85개), **CHEMICALS** (19개), **BODY_PARTS** (30개)
- **가중합산**: verb_energy×0.30 + emotion×0.30 + sentence_structure×0.20 + density×0.20
- **custom_dictionary.json**: 사용자 추가 단어 외부 사전 (모듈 로드 시 자동 머지)
- **미등록 단어 감지**: `--update-dict` 대화형 사전 업데이트 지원
- 음악 엔진은 이 필드를 현재 사용하지 않으나, 비주얼 렌더러(visual_renderer.py)가 소비함

---

---

## audio_mixer.py 연동 — 오디오 믹싱 + 엔드카드 BGM (EP007 수정)

음악 엔진 출력(bgm.wav)과 나레이션(narration.wav)을 최종 믹싱하는 `audio_mixer.py` 스펙.

### 믹싱 파라미터
| 파라미터 | 값 | 비고 |
|---------|-----|------|
| narration_volume | 0.90 | 하드코딩 |
| bgm_volume | 1.0 | CLI --bgm-volume으로 조절 가능 |
| output_duration | max(narration, bgm) | BGM이 더 길면 엔드카드까지 이어짐 |
| loudnorm | I=-14:TP=-1.5:LRA=11 | EBU R128 최종 정규화 |

### 엔드카드 BGM 연장 메커니즘
```
1. 음악 엔진: total_duration + 8초로 BGM 생성 (endcard 6초 + 2초 buffer)
   - outro 구간: energy 0.2 (이전 0.1), bass_drone 0.3, fm_bass 0.2, arpeggio 0.15
2. audio_mixer: output_duration = max(narration_duration, bgm_duration)
   - 나레이션을 apad로 output_duration까지 무음 패딩
   - BGM은 atrim으로 output_duration까지 재생
   - amix duration=longest로 더 긴 쪽 기준 출력
3. 결과: 엔드카드(마지막 6초)에도 BGM이 자연스럽게 지속
```

### 사이드체인 덕킹 (선택적)
`--sidechain narration_timing.json` 옵션으로 나레이션 구간에서 BGM -3dB 덕킹 가능.
기본값은 사이드체인 미사용 (loudnorm이 전체 밸런스 처리).

---

*이 문서는 enometa_music_engine.py v10의 동작 스펙을 기술한다. 프로젝트 경로: `C:\옵시디언\enometa\enometa-shorts\`*
