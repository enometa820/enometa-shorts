# ENOMETA 음악 엔진 업그레이드 계획서

> 버전: 1.9 (최종)
> 작성일: 2026-03-02
> 상태: **Phase A+B+C 전부 완료 — 9대 문제 전부 구현 (9/9) ✅**
> 대상: `scripts/enometa_music_engine.py` + 연관 파이프라인

---

## 배경

ENOMETA v6 시스템 분석 결과 음악 엔진에 8가지 구조적 문제가 발견됨.
핵심 철학 "매 에피소드가 시스템을 성장시킨다"를 실현하기 위해 전면 업그레이드 필요.

**핵심 요약**: 비주얼은 semantic_intensity로 대사에 반응하는데, 음악은 정적 EMOTION_MAP에만 의존 → 음악-비주얼-대사 삼위일체 단절.

---

## 문제 1: 음악↔비주얼 의미 단절 (Critical)

### 현상
- 비주얼: `semantic_intensity` (0-1) 기반 다이나믹 반응 (si 높으면 크고 밝게, 낮으면 작고 어둡게)
- 음악: `semantic_intensity` 완전 무시 — EMOTION_MAP(감정 문자열 → 악기 파라미터)만 사용
- 대사 "폭발하다"(si=0.95)일 때 비주얼은 격렬하지만 음악은 해당 씬 emotion 태그에만 반응

### 영향
- 음악과 비주얼 강도가 따로 놀음
- 대사의 극적 순간에 음악이 뒤따라가지 못함

### 해결 방안
- `script_data.json`의 `segments[].semantic_intensity`를 음악 엔진에 주입
- 세그먼트별 si 값으로 **실시간 악기 파라미터 변조**:
  - si > 0.7: 에너지 부스트 (+20% volume, +density)
  - si < 0.3: 에너지 감소 (-30% volume, 텍스처 악기 비활성)
  - si 0.3~0.7: 기본 EMOTION_MAP 값 유지
- 공식: `final_param = emotion_map_param × (0.7 + si × 0.6)` (si=0일 때 70%, si=1일 때 130%)

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | generate()에 script_data 로딩, 세그먼트별 si 기반 파라미터 변조 |
| `enometa_music_engine.py` | _render_section_textures()에 si 변조 적용 |
| `enometa_music_engine.py` | _render_continuous_*()에 si 기반 envelope 변조 |

### 난이도: 중 | 영향도: 높

---

## 문제 2: Song Arc와 실제 내러티브 미정렬 (Critical)

### 현상
- Song Arc는 총 길이를 **비율로 기계적 분할** (narrative = intro 15% → buildup 30% → climax 35% → outro 20%)
- 실제 대본 감정 곡선과 무관
- 대사 클라이맥스가 70%에 있어도 Song Arc climax는 45-80% 구간에 고정

### 영향
- 음악의 기승전결이 대본의 기승전결과 어긋남
- 극적 순간에 음악이 아직 buildup이거나, 이미 outro인 상황 발생

### 해결 방안
- `script_data.json`의 `segments[].semantic_intensity` 곡선에서 **자동 내러티브 구조 추출**
- si 곡선을 smoothing 후 peak/valley 분석:
  - 첫 valley → intro 끝
  - 최대 peak → climax 중심
  - 마지막 valley → outro 시작
- `_compute_song_arc()`를 `_compute_adaptive_arc()`로 확장:
  - script_data 있으면 → si 곡선 기반 adaptive arc
  - script_data 없으면 → 기존 비율 기반 fallback

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | `_compute_adaptive_arc()` 신규 — si 곡선 기반 아크 생성 |
| `enometa_music_engine.py` | SONG_ARC_PRESETS에 `"adaptive"` 추가 |
| `enometa_music_engine.py` | `--arc adaptive` CLI 옵션 (script_data 필수) |

### 난이도: 중 | 영향도: 높

---

## 문제 3: script_data 전장르 활용 부족 (High)

### 현상
- `script_data.json`에 숫자, 화학물질, 바이트 인코딩, semantic_intensity, keywords 등 풍부한 데이터 존재
- **ikeda 장르만** script_data 사용 (sine_interference + data_click 주파수)
- 나머지 5개 장르는 script_data 완전 무시

### 영향
- 대본 분석 데이터의 83% (5/6 장르)가 낭비됨
- 음악이 대본 내용과 무관하게 생성됨

### 해결 방안
- 장르별 script_data 활용 전략:

| 장르 | script_data 활용 | 구현 |
|------|-----------------|------|
| techno | keywords.intensity → kick 패턴 밀도, 숫자 → arpeggio 음정 | 텍스처 변조 |
| bytebeat | 바이트 데이터 → bytebeat 공식 파라미터, 숫자 → bit_depth 변조 | 직접 매핑 |
| algorave | keywords → euclidean rhythm 패턴 변화, 감정어 → 필터 cutoff | 리듬 변조 |
| harsh_noise | si → noise density/bandwidth, 감정어 → wavefold 강도 | 텍스처 변조 |
| chiptune | 숫자 → 멜로디 시퀀스, 바이트 → 듀티사이클 변조 | 음정 매핑 |
| ikeda | (기존 유지) freq_map → sine_interference, numbers → data_click | 주파수 매핑 |

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | 각 장르 프리셋에 `script_data_strategy` 딕셔너리 추가 |
| `enometa_music_engine.py` | `_apply_script_data()` 범용 메서드 — 장르별 분기 처리 |
| `enometa_music_engine.py` | 각 렌더러에 script_data 파라미터 주입점 추가 |

### 난이도: 중 | 영향도: 중

---

## 문제 4: 씬 경계 박자 미정렬 (Critical — 사용자 체감 최대 문제)

### 현상
- 음악 섹션이 visual_script.json의 씬 경계를 그대로 따름
- 비주얼 타이밍은 **대사 타이밍** 기반이지, **음악적 프레이징** 기반이 아님
- 4/4 박자에서 3.7초 지점에 씬이 끝나면 → 4마디 완성 전에 음악이 끊김
- **근본 원인**: 음악 섹션과 비주얼 씬이 1:1 결합되어 있음 — 음악이 대사에 종속

### 영향
- 음악적 어색함 (비트가 중간에 끊기는 느낌)
- 전문적인 음악 품질에 도달하지 못함
- **사용자 체감 최대 문제** — 들으면 바로 느껴지는 부자연스러움

### 해결 방안
- `generate_music_script()`에서 씬 경계를 **가장 가까운 마디 경계로 quantize**:
  ```
  bar_duration = 60 / bpm * 4  # 4/4 박자 기준 1마디 길이
  quantized_end = round(scene_end / bar_duration) * bar_duration
  ```
- 비주얼 씬 경계는 유지 (대사 타이밍 정확해야 하므로), 음악 섹션만 quantize
- 씬과 음악 섹션이 약간 어긋나는 건 허용 (±0.5마디 이내)

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | `generate_music_script()`에 `_quantize_to_bar()` 추가 |
| `enometa_music_engine.py` | music_script sections의 start_sec/end_sec quantize |

### 난이도: 낮 | 영향도: 높 (사용자 체감 최대)

---

## 문제 5: 감정 전환 크로스페이드 부재 (Medium)

### 현상
- EMOTION_MAP은 정적 룩업 — "calm" → "explosion"으로 갑자기 점프
- continuous 악기는 `smooth_envelope`로 보간하지만, section 악기는 on/off 방식
- 씬 전환 시 section 텍스처 악기가 즉시 교체됨

### 영향
- 씬 전환 시 음악이 부자연스럽게 끊김
- 감정 변화가 점진적이지 않고 계단식

### 해결 방안
- section 텍스처 악기에 **fade-in/fade-out envelope** 추가:
  ```
  fade_duration = min(0.5, section_duration * 0.15)  # 최대 0.5초 또는 섹션 15%
  fade_in = np.linspace(0, 1, int(fade_duration * sr))
  fade_out = np.linspace(1, 0, int(fade_duration * sr))
  ```
- 인접 섹션의 텍스처가 겹치는 구간에서 크로스페이드:
  - 이전 섹션 마지막 0.5초: fade-out
  - 현재 섹션 처음 0.5초: fade-in

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | `_render_section_textures()`에 fade envelope 적용 |
| `enometa_music_engine.py` | `_add_stereo()/_add_mono()`에 optional fade 파라미터 |

### 난이도: 낮 | 영향도: 중

---

## 문제 6: 고정 BPM (Medium)

### 현상
- 한 에피소드 전체가 단일 BPM (예: techno=128, ikeda=60)
- `self.bpm`이 `__init__`에서 고정되어 변경 불가
- 실제 음악은 섹션별 템포 변화가 자연스러움

### 영향
- 조용한 구간과 격렬한 구간의 템포가 동일 → 단조로움
- 음악의 표현력 제한

### 해결 방안
- **섹션별 BPM 변조** (기본 BPM의 ±15% 범위):
  ```
  section_bpm = base_bpm × (0.85 + si_avg × 0.30)
  # si=0 → 85% BPM (느리게), si=1 → 115% BPM (빠르게)
  ```
- continuous 악기에는 **tempo curve** 적용 (BPM이 시간에 따라 부드럽게 변화)
- 리듬 악기(kick, hihat)의 타일링 간격을 섹션별 BPM에 맞춤
- ⚠ 주의: BPM 변화가 너무 크면 오히려 부자연스러움 → ±15% 제한

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | `_compute_tempo_curve()` 신규 — si 기반 BPM 곡선 |
| `enometa_music_engine.py` | `_render_continuous_rhythm()`에 가변 BPM 적용 |
| `enometa_music_engine.py` | `_render_section_textures()`에 섹션별 BPM 전달 |

### 난이도: 높 | 영향도: 중

---

## 문제 7: 에피소드 간 음악 진화 부재 (Low-Medium)

### 현상
- 핵심 철학: "매 에피소드가 시스템을 성장시킨다"
- 비주얼: `vocab_history.json`으로 이력 추적 + 중복 회피
- 음악: 매번 독립 생성 — 이전 에피소드 음악 특성 참조 없음

### 영향
- 에피소드 간 음악적 연속성 없음
- 같은 장르/감정 조합에서 비슷한 음악이 반복될 수 있음

### 해결 방안
- `music_history.json` 신규 — 에피소드별 음악 특성 기록:
  ```json
  {
    "episodes": {
      "ep005": {
        "genre": "ikeda",
        "bpm": 60,
        "key": "E_minor",
        "dominant_instruments": ["sine_interference", "data_click"],
        "energy_profile": [0.3, 0.5, 0.8, 0.4],
        "synthesis_used": ["sine_interference", "data_click", "ultrahigh_texture"]
      }
    }
  }
  ```
- `generate_music_script()`에서 최근 2개 에피소드 이력 참조:
  - 같은 장르 연속 시 → key 변경, 리드 악기 교체
  - 같은 악기 조합 반복 시 → 가중치 감소
- `lookback_window = 2` (vocab_history와 동일)

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | `music_history.json` 로딩/저장 로직 |
| `enometa_music_engine.py` | `generate_music_script()`에 이력 기반 중복 회피 |
| `enometa_music_engine.py` | `--episode` CLI 옵션으로 이력 기록 |

### 난이도: 중 | 영향도: 낮~중

---

## 문제 8: 연속 악기 항상 재생 (Low)

### 현상
- Phase 1 연속 악기(deep_bass_drone, fm_bass, sub_pulse 등)는 전체 duration 동안 항상 재생
- EMOTION_MAP volume으로 줄일 수는 있지만 완전히 끄려면 `force_inactive`만 가능
- 조용한 명상적 구간에서도 베이스가 깔리는 문제

### 영향
- 다이나믹 레인지 부족 (항상 "무언가" 재생 중)
- 진정한 정적(silence)을 만들 수 없음

### 해결 방안
- continuous 악기에 **si 기반 게이트** 추가:
  ```
  if segment_si < 0.15:
    continuous_volume *= 0.1  # 거의 무음
  elif segment_si < 0.3:
    continuous_volume *= 0.4  # 반감
  ```
- `silence_break` 악기처럼 의도적 정적 구간 자동 삽입:
  - si가 0.1 이하인 연속 2개 이상 세그먼트 → 자동 silence_break
- EMOTION_MAP에 `"silence"` 감정 추가 (모든 continuous 악기 volume 0.05)

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | `_render_continuous_*()`에 si 게이트 조건 |
| `enometa_music_engine.py` | EMOTION_MAP에 "silence" 감정 추가 |
| `enometa_music_engine.py` | 자동 silence_break 삽입 로직 |

### 난이도: 낮 | 영향도: 낮

---

## 문제 9: Pulse Train / Granular 합성 부재 (Medium)

### 현상
- Ikeda 특유의 "뚜두두두두" 고속 반복 사운드를 생성할 수 없음
- 현재 `data_click()`은 **개별 클릭 1개**만 생성 (0.003초) — 고속 반복 메커니즘 없음
- `stutter_gate()`는 BPM 기반 볼륨 게이팅일 뿐 — 실제 클릭 연타가 아님
- `glitch_texture()`는 랜덤 산발 배치 — 밀도 가속/감속 제어 불가

### Ikeda 실제 사운드와의 갭

| 기법 | 현재 엔진 | Ikeda 실제 |
|------|----------|-----------|
| **Pulse Train** | 없음 | 극초단 클릭을 20~200Hz로 연타 → "뚜두두두두" |
| **Granular** | 없음 | 소리를 1~50ms grain으로 쪼개서 재배열/반복 |
| **가변 밀도** | glitch_texture 고정 density | 시간에 따라 밀도 가속→감속 (si 연동 가능) |
| **음정 생성** | data_click 주파수만 변경 | 반복 속도 자체가 음정 (100Hz 반복 = ~G2) |

### 핵심 개념: Pulse Train의 3가지 영역

```
반복 속도(Hz)   청각적 효과
─────────────────────────────
~1-10 Hz        개별 클릭 인지 "뚝...뚝...뚝"
~10-50 Hz       연속 버즈 "뚜두두두두" (Ikeda 핵심 영역)
~50-200 Hz      음정 생성 (반복 자체가 주파수)
```

### 해결 방안

#### 9-1. `pulse_train()` 합성 함수 신규
```python
def pulse_train(click_freq, repeat_rate, duration,
                rate_curve=None, sr=SAMPLE_RATE):
    """Ikeda 스타일 펄스 트레인
    click_freq: 클릭 자체의 주파수 (음색)
    repeat_rate: 초당 반복 횟수 (Hz) — 10~200
    duration: 전체 길이 (초)
    rate_curve: 시간별 반복 속도 변화 (np.array, optional)
               → si 연동 시 가속/감속 가능
    """
```
- `data_click()`으로 단일 클릭 생성 → `repeat_rate` 간격으로 배치
- `rate_curve` 제공 시 시간에 따라 반복 속도 변화 (가속/감속)

#### 9-2. `granular_cloud()` 합성 함수 신규
```python
def granular_cloud(source_signal, grain_size_ms, density,
                   scatter=0.0, duration=None, sr=SAMPLE_RATE):
    """Microsound 그래뉼러 클라우드
    source_signal: 원본 오디오 (사인파, 노이즈 등)
    grain_size_ms: grain 크기 (1~50ms)
    density: 초당 grain 수
    scatter: grain 배치 랜덤성 (0=균일, 1=랜덤)
    """
```
- 원본 신호에서 grain_size_ms 크기로 잘라냄
- Hanning window 적용 → density에 따라 배치
- scatter로 규칙적/랜덤 배치 제어

#### 9-3. ikeda 장르 통합
- `GENRE_PRESETS["ikeda"]`에 `pulse_train` 악기 추가 (force_active)
- `_render_continuous_pulse_train()`: 연속 렌더러로 등록
- si 연동: `repeat_rate = 20 + si * 180` (si=0 → 20Hz 느린 클릭, si=1 → 200Hz 급속 버즈)
- script_data의 숫자 → click_freq 매핑 (기존 data_click 패턴 재사용)

#### 9-4. 전장르 확장 가능성
- techno: pulse_train을 하이햇 대체/보조로 사용
- harsh_noise: granular_cloud로 노이즈 텍스처 생성
- algorave: rate_curve를 유클리드 패턴에 동기화

### 변경 대상
| 파일 | 작업 |
|------|------|
| `enometa_music_engine.py` | `pulse_train()` 합성 함수 신규 |
| `enometa_music_engine.py` | `granular_cloud()` 합성 함수 신규 |
| `enometa_music_engine.py` | `_render_continuous_pulse_train()` 연속 렌더러 |
| `enometa_music_engine.py` | GENRE_PRESETS["ikeda"]에 pulse_train 추가 |
| `enometa_music_engine.py` | EMOTION_MAP에 pulse_train 파라미터 추가 |

### 난이도: 중 | 영향도: 높 (ikeda 장르 품질 결정적 개선)

---

## 구현 순서 (권장)

### Phase A: 기반 (문제 4 + 1 + 2) — 최우선
1. **문제 4**: 씬 경계 박자 정렬 ← **체감 최대, 독립, 즉시 구현 가능**
2. **문제 1**: semantic_intensity → 음악 연동
3. **문제 2**: Adaptive Song Arc

> 문제 4는 독립적이라 바로 시작 가능. 문제 1+2는 si 기반 삼위일체 기반.

### Phase B: 확장 (문제 5 + 3 + 9) — 중요
4. **문제 5**: 감정 전환 크로스페이드
5. **문제 3**: script_data 전장르 활용
6. **문제 9**: Pulse Train / Granular 합성 (ikeda 품질 결정적)

### Phase C: 고도화 (문제 8 + 7 + 6) — 후순위
7. **문제 8**: 연속 악기 si 게이트
8. **문제 7**: 에피소드 간 음악 이력 추적
9. **문제 6**: 가변 BPM (가장 어려움, 마지막)

---

## 의존 관계

```
문제 1 (si→음악) ──┬── 문제 2 (adaptive arc)에 si 데이터 필요
                   ├── 문제 3 (전장르 script_data)에 si 주입 패턴 재사용
                   ├── 문제 6 (가변 BPM)에 si 곡선 사용
                   ├── 문제 8 (연속 악기 게이트)에 si 데이터 필요
                   └── 문제 9 (pulse train)에 si→repeat_rate 변조 사용

문제 4 (박자 정렬) ── 독립 (다른 문제와 무관하게 구현 가능)
문제 5 (크로스페이드) ── 독립
문제 7 (음악 이력) ── 독립
문제 9 (pulse train) ── 문제 1(si 연동) 활용하면 더 효과적이나 독립 구현도 가능
```

→ **문제 1이 핵심 기반**. 먼저 구현하면 나머지가 훨씬 쉬워짐.

---

## 검증 방법

### Phase A 검증
- [ ] EP006 제작 시 script_data → 음악 파라미터 변조 확인
- [ ] si 높은 구간(>0.7)에서 음악 에너지 증가 → 비주얼과 동기 확인
- [ ] si 낮은 구간(<0.3)에서 음악 에너지 감소 확인
- [ ] Adaptive Arc와 si 곡선 비교 — 클라이맥스 위치 일치 확인

### Phase B 검증
- [ ] 씬 전환점에서 음악이 마디 경계에 맞는지 확인
- [ ] 씬 전환 시 텍스처 크로스페이드 자연스러운지 확인
- [ ] 각 장르에서 script_data 활용이 음악에 반영되는지 확인

### Phase C 검증
- [ ] 조용한 구간에서 연속 악기 볼륨 감소 확인
- [ ] 연속 에피소드 간 음악 다양성 확인
- [ ] BPM 변화가 자연스럽고 어색하지 않은지 확인
- [ ] ikeda 장르에서 pulse_train "뚜두두두두" 사운드 확인
- [ ] si 연동 시 조용한 구간(느린 클릭) ↔ 격렬한 구간(빠른 버즈) 전환 확인
- [ ] granular_cloud 텍스처가 기존 glitch_texture 대비 개선 확인

---

## 구현 추적 대시보드

### Phase A: 기반

| # | 문제 | 상태 | 구현일 | 비고 |
|---|------|------|--------|------|
| 4 | 씬 경계 박자 정렬 | ✅ 완료 | 2026-03-02 | `_quantize_to_bar()` + `generate_music_script()` 퀀타이즈 |
| 1 | semantic_intensity → 음악 연동 | ✅ 완료 | 2026-03-02 | `_build_si_envelope()` + 마스터버퍼 + 텍스처 밀도 변조 |
| 2 | Adaptive Song Arc | ✅ 완료 | 2026-03-02 | `_compute_adaptive_arc()` + si 곡선 기반 동적 phase 경계 |

### Phase B: 확장

| # | 문제 | 상태 | 구현일 | 비고 |
|---|------|------|--------|------|
| 5 | 감정 전환 크로스페이드 | ✅ 완료 | 2026-03-02 | 텍스처 delta fade-in/fade-out |
| 3 | script_data 전장르 활용 | ✅ 완료 | 2026-03-02 | `_script_data_enrichment()` — 6개 장르 대본 데이터 기반 파라미터 변조 |
| 9 | Pulse Train / Granular 합성 | ✅ 완료 | 2026-03-02 | `pulse_train()` + `granular_cloud()` + `_render_continuous_pulse_train()`, si 연동 20~200Hz |

### Phase C: 고도화

| # | 문제 | 상태 | 구현일 | 비고 |
|---|------|------|--------|------|
| 8 | 연속 악기 si 게이트 | ✅ 완료 | 2026-03-02 | `_build_si_gate()` — si<0.15→10%, si<0.30→40%, 0.3s 스무딩, 45x 다이나믹 레인지 |
| 7 | 에피소드 간 음악 이력 | ✅ 완료 | 2026-03-02 | KEY_PRESETS 7키 + music_history.json + --episode CLI |
| 6 | 가변 BPM | ✅ 완료 | 2026-03-02 | `_compute_tempo_curve()` + 이벤트 기반 리듬 배치 + ±15% BPM 변조 |

**상태 범례**: ⬜ 대기 → 🔄 진행중 → ✅ 완료 → ❌ 보류/취소

---

## 구현 이력

> 문제 해결 완료 시 아래에 날짜 + 변경 요약 + 변경 파일을 기록한다.

### 2026-03-02 — 문제 4: 씬 경계 박자 정렬 ✅ 완료

#### 변경 요약
- `generate_music_script()`에서 음악 섹션 경계를 가장 가까운 마디(bar) 경계로 퀀타이즈
- 비주얼 씬 경계는 그대로 유지 (나레이션 타이밍 정확), 음악 섹션만 마디 단위 정렬

#### 구현 상세
- `import math` 추가
- `_quantize_to_bar(time_sec, bar_duration)` 헬퍼 함수 신규 (반올림 퀀타이즈)
- `generate_music_script()` 내 sections 생성 후 박자 정렬 로직:
  - `bar_duration = (60.0 / base_bpm) * 4` (4/4 박자 기준)
  - 첫 섹션 start = 0.0 고정
  - 일반 섹션 end = `_quantize_to_bar()` (최소 1마디 보장)
  - outro end = `math.ceil()` 올림 퀀타이즈
  - 인접 섹션 연속성: `sections[i+1].start = sections[i].end`
  - 원본 경계 보존: `_original_start_sec`, `_original_end_sec`
  - `total_duration`도 퀀타이즈된 값으로 갱신

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `import math`, `_quantize_to_bar()` 신규, `generate_music_script()` 박자 정렬 로직 |

#### 검증 결과
- [x] 6개 전 장르 테스트: seamless=True, bar-aligned=True
- [x] 최소 1마디 길이 보장 확인
- [x] 인접 섹션 간 갭 0 확인
- [x] outro 올림 퀀타이즈 확인

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v6.6 진화로그 + 음악 엔진 섹션
- [x] Hybrid_Visual — last_updated
- [x] Music_Engine_Spec — 박자 정렬 섹션 추가
- [x] ClaudeCode_Brief — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

### 2026-03-02 — 문제 1: semantic_intensity → 음악 연동 ✅ 완료

#### 변경 요약
- script_data의 semantic_intensity(0~1)로 음악 전체 에너지를 실시간 변조
- 마스터 버퍼 볼륨 변조 (`0.7 + si × 0.6`) + 텍스처 악기 밀도 변조 (`0.5 + si`)

#### 구현 상세
- `_build_si_envelope()` 메서드 신규: segments → 시간 도메인 배열, 0.5초 cumsum 스무딩
- `generate()`에서 si envelope 빌드 + Song Arc 후 마스터 버퍼에 적용
- `_render_section_textures()`에서 si 기반 `si_density_mod` 계산, 클릭/글리치/노이즈/메탈릭 density에 적용
- script_data 없으면 si=0.5(neutral) → si_mod=1.0 (무변조, 하위호환)

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_build_si_envelope()` 신규, `generate()` si 적용, `_render_section_textures()` density 변조 |

#### 검증 결과
- [x] si=0.15 → 21% 볼륨 감소 (ratio 0.786)
- [x] si=0.55 → 거의 무변조 (ratio 1.004)
- [x] si=0.95 → 16% 볼륨 증가 (ratio 1.160)
- [x] script_data 없을 때 하위호환 확인

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P1 si→음악 연동 섹션 추가
- [x] Music_Engine_Spec — si 변조 시스템 섹션 추가
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가
- [x] ClaudeCode_Brief, Hybrid_Visual, Visual_Differentiation — last_updated

### 2026-03-02 — 문제 5: 감정 전환 크로스페이드 ✅ 완료

#### 변경 요약
- 섹션 텍스처 악기의 기여분(delta)에만 fade-in/fade-out을 적용하여 씬 전환 시 부드러운 크로스페이드

#### 구현 상세
- `_render_section_textures()` 시작: 마스터 버퍼 스냅샷 저장
- 렌더 후: delta(텍스처 기여분) = 현재 - 스냅샷 추출
- fade envelope 적용: `fade_duration = min(0.5, dur × 0.15)`
- delta에만 fade → 연속 악기(bass, arp 등) 영향 없음
- 스냅샷 + 페이드된 delta로 복원

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_render_section_textures()` 시작/끝에 스냅샷+delta fade |

#### 검증 결과
- [x] 5개 섹션 테스트: 섹션 시작/끝 RMS < 중간 RMS (fade 확인)
- [x] 연속 악기 영향 없음 확인

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P5 진화로그
- [x] Music_Engine_Spec — 크로스페이드 섹션 추가
- [x] ClaudeCode_Brief — last_updated
- [x] Hybrid_Visual — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

### 2026-03-02 — 문제 2: Adaptive Song Arc ✅ 완료

#### 변경 요약
- 고정 비율 Song Arc 대신 si 곡선에서 내러티브 구조를 자동 추출하여 음악 기승전결을 대본과 정렬

#### 구현 상세
- `SONG_ARC_PRESETS`에 `"adaptive"` 마커 추가 (동적 phases)
- `generate()`에서 si_env 빌드를 arc 계산 전으로 이동 (adaptive가 si 참조)
- `_build_arc_from_phases()` 공통 로직 분리 (DRY)
- `_compute_adaptive_arc()` 신규:
  - si 곡선 3s cumsum heavy smoothing → 매크로 구조 추출
  - 글로벌 피크 → 클라이맥스 중심 (30-80% 클램프)
  - si range < 0.08 → narrative fallback (플랫 대본)
  - 피크 기준 비례 배분: intro=peak×30%, climax=peak±8%
  - phases 저장 → `_get_arc_phase_at()` 호환
- `_get_arc_phase_at()`: adaptive phases 동적 참조 지원

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_compute_adaptive_arc()` 신규, `_build_arc_from_phases()` 분리, `SONG_ARC_PRESETS["adaptive"]`, `generate()` 순서 변경, `_get_arc_phase_at()` 확장 |

#### 검증 결과
- [x] Early peak (30%): climax 22-38% 정확 배치
- [x] Late peak (80%): climax 64-80% 정확 배치
- [x] Center peak (50%): climax 34-50% 정확 배치
- [x] Flat si (range<0.08): narrative fallback 정상
- [x] No script_data: narrative fallback 정상
- [x] Ikeda + adaptive: 정상 작동

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P2 섹션 + 진화로그
- [x] Music_Engine_Spec — Adaptive Song Arc 섹션 + 아크 테이블
- [x] ClaudeCode_Brief — --arc adaptive CLI 옵션
- [x] Hybrid_Visual — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

### 2026-03-02 — 문제 3: script_data 전장르 활용 ✅ 완료

#### 변경 요약
- ikeda만 쓰던 script_data를 6개 장르 전부에서 활용하여 음악이 대본 내용에 반응

#### 구현 상세
- `_script_data_enrichment(sections)` 신규 메서드:
  - techno: numbers → synth_lead pattern 비율, data_density → clicks density 변조
  - bytebeat: numbers 합 → BYTEBEAT_FORMULAS 인덱스 → formula 선택
  - algorave: data_density → metallic_hit density 변조
  - harsh_noise: si → feedback gain(0.5~0.95), iterations(4~12)
  - chiptune: numbers → chiptune_lead pattern 비율
  - ikeda: 기존 data_click 로직 유지
- `generate()`에서 si_env 빌드 후, arc 계산 전 호출

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_script_data_enrichment()` 신규, `generate()` 호출 삽입 |

#### 검증 결과
- [x] techno: 4개 enrichment (synth_lead pattern + clicks density)
- [x] bytebeat: 2개 enrichment (formula 선택)
- [x] algorave: 2개 enrichment (metallic_hit density)
- [x] harsh_noise: 2개 enrichment (feedback gain/iterations)
- [x] chiptune: 2개 enrichment (chiptune_lead pattern)
- [x] ikeda: 기존 로직 유지 확인

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P3 진화로그
- [x] Music_Engine_Spec — script_data 전장르 활용 섹션 추가
- [x] ClaudeCode_Brief — last_updated
- [x] Hybrid_Visual — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

### 2026-03-02 — 문제 9: Pulse Train / Granular 합성 ✅ 완료

#### 변경 요약
- Ikeda 특유의 "뚜두두두두" 고속 클릭 반복 사운드를 구현하는 2개 합성 함수 + 1개 연속 렌더러

#### 구현 상세
- `pulse_train(click_freq, repeat_rate, duration, rate_curve)` 합성 함수:
  - `data_click()` 템플릿을 가변 간격으로 배치, rate_curve로 시간별 반복 속도 변화
  - 클릭 겹침 방지: `pos += max(interval, click_len + 1)`
- `granular_cloud(source_signal, grain_size_ms, density, scatter)` 합성 함수:
  - Hanning window grain 추출 → 균일/랜덤 혼합 배치
- `_render_continuous_pulse_train(sections)` 연속 렌더러:
  - si 기반 rate_curve: `20 + si * 180` (si=0→20Hz, si=1→200Hz)
  - 대본 숫자 중앙값 → click_freq (40~2000Hz 클램프)
  - si 평균 > 0.3일 때 granular_cloud 서브레이어 추가
  - `smooth_envelope()` 모핑으로 섹션별 볼륨 변화
- GENRE_PRESETS["ikeda"]: `pulse_train` volume_scale=1.0, force_active 추가
- EMOTION_MAP: tension(0.3), tension_peak(0.5), awakening(0.35), awakening_climax(0.45), transcendent(0.2)
- `generate_music_script()`: 악기 키 리스트에 `"pulse_train"` 추가

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `pulse_train()`, `granular_cloud()` 합성 함수, `_render_continuous_pulse_train()`, GENRE_PRESETS/EMOTION_MAP/generate_music_script 확장 |

#### 검증 결과
- [x] pulse_train 기본: 1초, 50Hz 반복 정상
- [x] pulse_train rate_curve 가속: 2nd half energy > 1st half (가속 확인)
- [x] granular_cloud: sine/noise source 정상 grain 생성
- [x] ikeda 전체 렌더링: 5개 씬, si 연동 에너지 변화 확인 (neutral 0.063 → tension_peak 0.246)
- [x] non-ikeda 장르 (techno/bytebeat/chiptune): 정상 동작 확인 (pulse_train 미호출)

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P9 진화로그
- [x] Music_Engine_Spec — Pulse Train/Granular 섹션 추가
- [x] ClaudeCode_Brief — last_updated
- [x] Hybrid_Visual — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

### 2026-03-02 — 문제 8: 연속 악기 si 게이트 ✅ 완료

#### 변경 요약
- 조용한 구간(si 낮음)에서 연속 악기 볼륨 자동 감쇠 → 다이나믹 레인지 45.59x 달성

#### 구현 상세
- `_build_si_gate()` 메서드 신규:
  - si < 0.15 → gate = 0.1 (거의 무음)
  - si < 0.30 → gate = 0.4 (반감)
  - si ≥ 0.30 → gate = 1.0 (풀 볼륨)
  - 0.3초 cumsum 스무딩 (급격한 온/오프 방지)
- `generate()`에서 si_modulation 직후 `self._si_gate = self._build_si_gate()` 계산
- 7개 연속 렌더러 전부에 `self._si_gate` 적용:
  - `_render_continuous_bass`: drone *= vol_env * si_gate * 1.2
  - `_render_continuous_fm_bass`: fm *= vol_env * si_gate * 1.0
  - `_render_continuous_rhythm`: kick/hihat에 si_gate 곱셈
  - `_render_continuous_sub_pulse`: sub *= vol_env * si_gate * 0.7
  - `_render_continuous_arpeggio`: arp/arp2에 si_gate 곱셈
  - `_render_continuous_sine_interference`: total *= vol_env * si_gate
  - `_render_continuous_ultrahigh`: texture *= vol_env * si_gate
- script_data 없으면 gate = 1.0 전체 (무변조, 하위호환)

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_build_si_gate()` 신규, `generate()` si_gate 계산, 7개 `_render_continuous_*()` si_gate 적용 |

#### 검증 결과
- [x] quiet(si=0.1) RMS=0.0068, loud(si=0.9) RMS=0.3105 → 45.59x 다이나믹 레인지
- [x] script_data 없을 때 gate=1.0 (무변조 하위호환)
- [x] non-ikeda 장르(techno) 정상 동작

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P8 진화로그
- [x] Music_Engine_Spec — 연속 악기 si 게이트 섹션 추가
- [x] ClaudeCode_Brief — last_updated
- [x] Hybrid_Visual — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

### 2026-03-02 — 문제 7: 에피소드 간 음악 이력 추적 ✅ 완료

#### 변경 요약
- `music_history.json`으로 에피소드별 음악 특성(키, 아르페지오 패턴) 추적 + 자동 다양화

#### 구현 상세
- `KEY_PRESETS` 7키(C~Bb minor) + `KEY_PRIORITY` 선택 우선순위
- `ARP_PATTERNS` 5종 아르페지오 패턴 변형
- `_load_music_history()` / `_save_music_history()` — music_history.json I/O
- `_select_key_from_history()`: lookback=2, 최근 에피소드와 다른 키 자동 선택
- `_select_arp_pattern_from_history()`: 최근 에피소드와 다른 패턴 선택
- `--episode ep006` CLI 옵션 추가
- 하드코딩 `"key": "E_minor"` → KEY_PRESETS 기반 동적 선택

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | KEY_PRESETS/ARP_PATTERNS, _load/_save_music_history, _select_key/arp_from_history, generate_music_script 확장, --episode CLI |

#### 검증 결과
- [x] KEY_PRESETS 7키 순환 확인
- [x] ARP_PATTERNS 5종 순환 확인
- [x] music_history.json 저장/로딩 정상

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P7 진화로그
- [x] Music_Engine_Spec — 에피소드 간 음악 이력 섹션 추가
- [x] ClaudeCode_Brief — last_updated
- [x] Hybrid_Visual — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

### 2026-03-02 — 문제 6: 가변 BPM ✅ 완료

#### 변경 요약
- si 기반 섹션별 ±15% BPM 변조 + 이벤트 기반 가변 간격 리듬 배치

#### 구현 상세
- `_compute_tempo_curve()` 신규: si 기반 per-sample BPM 곡선 (0.85+si×0.30)
  - 0.5초 cumsum 스무딩으로 섹션 경계 자연스러운 전환
  - script_data 없으면 base_bpm 균일 (무변조 fallback)
- `_section_bpm(section)` 헬퍼: 섹션 평균 BPM 조회
- `_render_continuous_rhythm()` 전면 재작성: 정적 타일링 → 이벤트 기반 가변 간격 배치
  - 표준(4-on-the-floor) + 유클리드 모드 모두 가변 BPM 지원
  - `bpm_at(t)` 함수로 실시간 BPM 참조
- `_render_section_textures()`: acid_bass, chiptune_drum, stutter_gate에 섹션별 BPM 적용
- `generate()`: si_gate 후 `self._tempo_curve` 계산 + 템포 범위 로그 출력
- `export_raw_visual_data()`: `tempo_curve` 프레임별 BPM 배열 추가 (npz)

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_compute_tempo_curve()`, `_section_bpm()` 신규, `_render_continuous_rhythm()` 전면 재작성, `_render_section_textures()` BPM 3곳, `generate()` tempo 계산, `export_raw_visual_data()` tempo_curve 추가 |

#### 검증 결과
- [x] 6개 전 장르 렌더링: 모두 ±15% 범위 내 BPM 변조 확인
- [x] 조용한 구간(si=0.15) → 85% BPM, 격렬한 구간(si=0.85) → 115% BPM
- [x] 하위호환: script_data 없을 때 uniform BPM 확인
- [x] export: tempo_curve 프레임별 배열 정상 출력

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — v7-P6 진화로그
- [x] Music_Engine_Spec — 가변 BPM 시스템 섹션 추가
- [x] ClaudeCode_Brief — last_updated
- [x] Hybrid_Visual — last_updated
- [x] Visual_Differentiation — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md — 변경 이력 추가

<!-- 구현 완료 시 아래 형식으로 추가:
### YYYY-MM-DD — 문제 N: [제목] ✅ 완료

#### 변경 요약
- (1줄 요약)

#### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | ... |

#### 검증 결과
- [ ] 검증 항목 1
- [ ] 검증 항목 2

#### 마스터 문서 업데이트
- [x] SYSTEM_SNAPSHOT — ...
- [x] Hybrid_Visual — ...
- [x] Music_Engine_Spec — ...
- [x] ClaudeCode_Brief — ...
- [x] Visual_Differentiation — ...
- [x] MEMORY.md — ...
- [x] CHANGELOG.md — ...
-->

---

## 업그레이드 워크플로우 프로토콜

### 문제 발견 → 계획 갱신
```
1. 새 문제 발견 또는 기존 문제 수정 필요
2. 이 문서(Upgrade_Plan)에 문제 섹션 추가/수정
3. 구현 추적 대시보드에 항목 추가
4. 의존 관계 + 구현 순서 재검토
5. MEMORY.md 업그레이드 요약 갱신
```

### 구현 실행
```
1. 대시보드에서 다음 구현 대상 확인 (상태: ⬜ 대기 + 의존성 충족)
2. 대시보드 상태 → 🔄 진행중 변경
3. 코드 구현
4. 검증 (해당 Phase 검증 체크리스트 실행)
5. 대시보드 상태 → ✅ 완료 + 구현일 기록
6. "구현 이력" 섹션에 상세 기록 추가
7. ⚠ 마스터 문서 7종 강제 업데이트 프로토콜 실행
8. CHANGELOG.md에 기록
```

### 에피소드 피드백 → 계획 갱신
```
1. 에피소드 제작 후 음악 관련 피드백 수집
2. 피드백이 기존 문제에 해당 → 해당 문제 우선순위/해결방안 수정
3. 피드백이 새 문제 → 문제 섹션 신규 추가 + 대시보드 등록
4. 피드백이 구현 완료 항목 관련 → 구현 이력에 피드백 추가, 필요 시 재수정
```

---

*이 문서는 ENOMETA 음악 엔진 v7 업그레이드의 마스터 계획서이다.*
*구현 시 각 문제 해결 후 CHANGELOG.md + 마스터 문서 7종 업데이트 필수.*
*문제 발견/구현/피드백 시 이 문서를 먼저 갱신한 후 작업한다.*
