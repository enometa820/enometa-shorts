# ENOMETA System Snapshot v6
> 최종 업데이트: 2026-03-02
> 상태: v8 ikeda 단일 장르 + Hybrid 전용화 + ikeda 확장
> **last_updated**: 2026-03-02 — v8 + 글쓰기 스킬 v11 + script_data v2 (사전 대폭 확장 + custom_dictionary + 미등록 단어 감지)

---

## 1. 프로젝트 개요

**ENOMETA**는 대본 하나로 YouTube Shorts 영상을 자동 생성하는 **진화하는 디지털 아트 시스템**이다.

- **장르**: 철학/자기인식/존재론 — "존재와 사유, 그 경계를 초월하다"
- **비주얼**: 디지털 데이터아트 + 8bit 레트로 (프로시저럴 그래픽, 장르 연동)
- **음악**: Raw Synthesis 전자음악 (Pure Python v8 엔진, ikeda 단일 장르 + 텍스처 모듈, GPU 불필요)
- **나레이션**: 한국어 여성 TTS (Edge-TTS)
- **비용**: 0원 (Claude Max 구독만 필요)
- **GPU**: RTX 3060 Laptop 6GB

### 핵심 철학: 진화하는 시스템
매 에피소드가 시스템 자체를 성장시킨다.
- 새 대본이 요구하는 감정/개념 → 새 비주얼 vocab 컴포넌트 탄생
- 새 감정 아크 → 새 악기/합성법이 음악 엔진에 추가
- 같은 비주얼 패턴 반복 금지 — 에피소드마다 다른 시각 전략
- **목표**: 에피소드가 100개가 되면, 100가지 다른 비주얼 언어를 구사하는 시스템

---

## 2. 콘텐츠 제작 워크플로우

```
[STEP 1] 주제 협의 → 스타일/분량 결정
[STEP 0] 주제 추천 → 3~5개 (도메인 교차점 + 핵심 팩트 + 추천 이유)
[STEP 1] 주제 선택/협의 → 스타일/분량 결정
[STEP 2] 대본 작성 → enometa-writing 스킬(v11) 적용, 본문 + 시스템 최적화 점수(100점) 자동 첨부
[STEP 3] ★ 글 컨펌 게이트 ★ → 사용자 명시적 승인 필수
         ⚠ 컨펌 전: 제목/음악/비주얼 제안 일체 금지
         → 수정 요청 시 STEP 2 재제출
[STEP 4] 제목 추천 → 5개 후보 (컨펌 후)
[STEP 5] 팩트체크 → 과학적 주장 근거 확인
[STEP 6] publish.md 생성 (업로드 메타데이터)
         → 태그: 카테고리 상위 5개만 (#쇼츠/#shorts/#ENOMETA/#이노메타/#데이터아트 제외)
         → 설명란/고정댓글 하단에 시스템 소개 고정 멘트 자동 삽입:
           "존재와 사유, 그 경계를 초월하다 / 대본→바이트+주파수 분해 / SI가 음악 텍스처+비주얼 파티클 실시간 제어 / 3중 리액티브(시간×오디오×의미) / 코드로 쓰는 철학. 데이터로 그리는 존재론."
[STEP 7] 영상 제작 파이프라인
         → script.txt → TTS → BGM(+raw_visual_data.npz) → 믹싱
         → Python 비주얼 렌더링(hybrid) 또는 FFT(legacy) → Remotion 합성
```

---

## 3. 기술 파이프라인 (영상 제작 7단계)

### 3-0. 대본 데이터 추출 (v6 신규)
- `scripts/script_data_extractor.py` — narration_timing.json → script_data.json
- 대본 텍스트에서 숫자/화학물질/키워드 추출 + UTF-8 바이트 인코딩 + 한글 분해
- **음악과 비주얼 양쪽에 데이터 공급** (대본 → 사운드 파라미터 + 비주얼 패턴 결정)
- v6 **구현 완료**: `semantic_intensity` (0-1) 추출 — 단어/문장의 의미 강도가 움직임 세기 결정
  - `compute_semantic_intensity()`: VERB_ENERGY(101개) + EMOTION_INTENSITY(68개) + SCIENCE_TERMS(85개) + 문장구조 + density 가중합산 (v11.1 대폭 확장)
  - `custom_dictionary.json`: 사용자 추가 단어 외부 사전 (모듈 로드 시 자동 머지)
  - `detect_unregistered_words()`: 미등록 단어 자동 감지 + 리포트 + `--update-dict` 대화형 업데이트
  - 키워드별 `intensity` 필드 자동 부여, visual_renderer.py ctx에 주입
- CLI: `py scripts/script_data_extractor.py episodes/epXXX/narration_timing.json`

### 3-1. 대본 → visual_script.json
- `scripts/visual_script_generator.py`가 대본 + 나레이션 타이밍 + 장르 → JSON 자동 생성
- v5: `--genre` 옵션으로 8bit 비주얼 자동 주입 (bytebeat/chiptune → gameboy 팔레트 + PixelGrid/PixelWaveform)
- v8: 모든 에피소드 항상 `render_mode: "hybrid"` 자동 설정 + `frames_dir`/`total_frames` 자동 계산
- 장르: 항상 ikeda (v8 단일 장르)

### 3-2. TTS 생성
- **필수 스크립트**: `scripts/generate_voice_edge.py` (Edge-TTS 전용)
- 음성: ko-KR-SunHiNeural, rate=+5%~+10% (차분한 여성 톤)
- 실행: `py scripts/generate_voice_edge.py episodes/epXXX/narration_timing.json episodes/epXXX/narration.wav`
- 실행 후 narration_timing.json이 **실측 타이밍**으로 자동 업데이트됨
- **Chatterbox(`generate_voice.py`) 절대 사용 금지** — 품질 불안정, 타이밍 추정 불가

### 3-3. BGM 생성
- `enometa_music_engine.py` v6 (numpy + scipy)
- **합성법 9종**: 기존 6 + sine_interference, data_click, ultrahigh_texture (v6 ikeda)
- **악기 26종**: 기존 23 + sine_interference, data_click, ultrahigh_texture
- **장르 1종**: ikeda(60) — v8 단일 장르 (techno/bytebeat/algorave/harsh_noise/chiptune 제거)
- **ikeda 확장**: 사인파 간섭 + 데이터 클릭 + 초고주파 텍스처 + 텍스처 모듈(TEXTURE_MODULES) + 멜로딕 사인 시퀀스(SINE_MELODY_SEQUENCES 5종)
- **ikeda 마스터링**: tanh(1.2) 부드러운 새츄레이션, RMS -10dB (기존 -14dB보다 높음 — 음악 존재감)
- **최적화**: smooth_envelope O(n) cumsum, 패턴 타일링
- **음량 가이드라인**: algorave/harsh_noise energy ≤ 0.72, bytebeat/feedback/stutter_gate 최소화, ikeda는 리듬/멜로디 구조 필수
- **`--export-raw`**: raw_visual_data.npz 동시 출력 (sine_interference_values, data_click_positions 포함)
- **`--script-data`**: script_data.json 입력 → 대본 데이터 기반 음악 파라미터 자동 설정

### 3-4. 자막 그루핑 (v5.1)
- `scripts/subtitle_grouper.py` — narration_timing.json → subtitle_groups.json (2줄씩)

### 3-5. 오디오 믹싱 / FFT
- 오디오 믹싱: **TTS:BGM = 4:6** (나레이션 67% + BGM 100%), 음악이 더 큰 비율
- **사이드체인 덕킹** (v6): narration_timing.json 기반 — 나레이션 구간 BGM -3dB, 무음 구간 풀 볼륨
- **CLI**: `--bgm-volume 1.0 --sidechain episodes/epXXX/narration_timing.json`
- FFT 분석: 30fps, bass/mid/high/rms/onset (legacy 모드용)

### 3-6. Python 비주얼 렌더링 (Hybrid 모드, v6.1 Dual-Source)
- `scripts/visual_renderer.py` — raw_visual_data.npz + script_data.json → frames/000000.png~
- `scripts/visual_layers/` — **9개 레이어 모듈** + `tts_effects.py` 공유 모듈 + `composite_dual_source()`:
  - **Music layers**: BytebeatLayer, WaveformLayer, ParticleLayer, FeedbackLayer, SineWaveLayer
  - **TTS layers**: DataMatrixLayer, BarcodeLayer, DataStreamLayer, TextDataLayer
  - **tts_effects.py** (v6.2 신규): 10개 공유 이펙트 함수 — get_scaled_font, intensity_color, hue_shift_color, chromatic_aberration, scanlines, glitch_blocks, text_glow, vertical_wave_distortion, scale_pulse, data_click_explosion
- **Dual-Source 아키텍처**: Music/TTS 레이어 독립 렌더 후 `composite_dual_source()` 합성
  - `arc_energy`가 음악 레이어 강도를 변조 (기승전결 반영)
  - `blend_ratio`: 장르별 0.45~0.6 (GENRE_LAYER_PRESETS v2)
- **GENRE_LAYER_PRESETS v2**: 모든 6개 장르에 TTS 4레이어(Barcode/DataStream/TextData/DataMatrix) 기본 장착, 음악 레이어 3개 확장, 장르별 평균 7.0개 레이어(78% 활용률), 장르 차별화는 intensity 분배 + blend_ratio + palette 기반
- **semantic_intensity 다이나믹 TTS 비주얼** (v6.2 구현):
  - visual_renderer.py ctx에 `semantic_intensity`, `current_keywords`, `reactive_level` 주입
  - TTS 레이어 3종 전면 리라이트: 폰트/카드/선폭 대폭 확대 + si 비례 색상/이펙트
  - TextDataLayer: 폰트 16→48px, 카드 90→200px, intensity 연동 색상/jitter/glow/scanlines/chromatic/glitch/wave/data_click
  - DataStreamLayer: 폰트 16→36px, 행별 jitter, 스크롤 si 비례 가속, glow/scanlines/chromatic
  - BarcodeLayer: 선폭 2→12px, BPM 맥동, 선높이 60~100%, scanlines/chromatic/glitch
- 장르별 레이어 자동 조합 + **ikeda 팔레트: 씬별 accent_color 전환** (공포→빨강, 각성→시안, 몰입→흰)
- 1080x1080, numpy+Pillow, CPU 렌더링

### 3-7. Remotion 합성
- **Hybrid 모드 전용 (v8)**: PythonFrameBackground(프레임 시퀀스) + **Remotion vocab 오버레이** + 제목 + 자막 + PostProcess → MP4
- Legacy 모드 제거 (v8) — `meta.render_mode`는 항상 `"hybrid"`
- **✅ Hybrid Vocab Overlay 구현 완료**: VisualSection.tsx hybrid 모드에서 Python 배경 위에 vocab 시맨틱 레이어 자동 렌더링. visual_script.json의 씬별 vocab entries가 Python 프레임 위에 오버레이됨
- **⚠ 다양성 규칙**: 씬마다 다른 비주얼 전략 적용, 단조로운 반복 금지
- **LogoEndcard v2**: 엔드카드 타이밍 리디자인 + 파티클 다이나미즘 강화
  - 검정 화면 축소: scatterEnd 0.15→0.03초, 초기 radius 672~1072→384~584px, alpha 0.15→0.35
  - 수렴 가속: convergeDuration 2.5→2.0초
  - 태그라인 풀 노출: 0.2→1.7초 (등장 4.2→2.8초, max opacity 0.35→0.5)
  - 파티클 다이나미즘: 호흡 진폭 2.5px + 웨이브 효과 + 크기 펄스(±30%) + 색상 깜빡임
  - 글로우 강화 (반경 8x, alpha 0.06) + 연결선 강화 (거리 90px, alpha 0.08)
  - TitleSection fade-out 연동: 엔드카드 시작 1초 전부터 제목 fade-out → 엔드카드 종료 후 제목 노출 버그 수정

---

## 4. 비주얼 시스템 — 3중 리액티브

매 프레임의 비주얼 = **시간** x **오디오** x **의미**

### 구현된 Vocab 컴포넌트 (22 + 1)

| 카테고리 | 컴포넌트 | 의미 |
|---------|----------|------|
| **파티클** | ParticleBirth | 생성, 탄생, 시작 |
| | ParticleScatter | 확산, 자유, 해방 |
| | ParticleConverge | 수렴, 집중, 압축 |
| | ParticleOrbit | 궤도, 반복, 순환 |
| | ParticleEscape | 탈출, 각성, 돌파 |
| | ParticleChainAwaken | 연쇄 각성, 전파 |
| | ParticleSplitRatio | 비율 분할, 대비 |
| **배경/효과** | FlowField | 흐름, 방향성, 배경 텍스처 |
| | CounterUp | 숫자 카운트, 데이터 시각화 |
| | ColorShift | 색상 전환, 감정 변화 |
| | BrightnessPulse | 명암 맥동, 긴장감 |
| **대본 의미** | NeuralNetwork | 뇌, 신경망, 생각의 연결 |
| | LoopRing | 루프, 반복, 동심원 |
| | FractalCrack | 균열, 각성, 깨어남 |
| | LightSource | 빛, 희망, 초월 |
| **타이포그래피** | TextReveal | 텍스트 애니메이션 (4모드) |
| **데이터 시각화** | DataBar | 바/링 차트 |
| **Max Cooper** | GridMorph | 격자 왜곡 (3모드) |
| **오디오 파형** | WaveformVisualizer | 파형 시각화 (4모드) |
| **v5 8bit** | PixelGrid | 8bit 격자 (fill/outline/life/rain 4모드) |
| | PixelWaveform | 8bit 파형 (bars/steps/cascade 3모드) |
| **오버레이** | PostProcess | 비네트, 스캔라인, onset 플래시 |

### VOCAB_MAP (37 vocab 키)
```
기존 30개 + v5 7개:
pixel_grid, pixel_grid_outline, pixel_grid_life, pixel_grid_rain,
pixel_waveform, pixel_waveform_steps, pixel_waveform_cascade
```

### Variant 시스템 (v5.1)

같은 vocab도 variant를 통해 다른 시각적 변형을 표현.

| 컴포넌트 | variants |
|---------|----------|
| ParticleBirth | default, triangles_rise, lines_scatter, dots_grid |
| ParticleScatter | default, directional_wind, spiral_out |
| ParticleConverge | default, multi_point, collapse_line |
| ParticleOrbit | default, ellipse_drift, figure_eight |
| ParticleEscape | default, chain_break, explosion |
| FractalCrack | default, edge_shatter, web_crack |
| NeuralNetwork | default, tree_branch, constellation |
| FlowField | default, vortex, opposing |
| GridMorph | default, wave_propagation, pixel_dissolve |

- `visual_script.json`의 각 vocab entry에 `"variant": "..."` 필드 추가
- variant 없는 기존 EP → `"default"` 동작 (하위 호환)
- Python `select_variant()`이 이력 기반 중복 회피

### 비주얼 전략 프리셋 (v5.1)

에피소드 전체의 비주얼 밀도/리듬/구성을 결정하는 상위 전략.

| 전략 | 설명 | 레이어 | 파티클 밀도 |
|------|------|--------|------------|
| dense | 압도적 시각 밀도 | 4 | 1.5x |
| breathing | 여백 + 명상적 | 2 | 0.5x |
| collision | 충돌/분열/대비 | 3 | 1.2x |
| layered | 깊이감 (배경-중경-전경) | 3 | 1.0x |
| minimal | 단일 포커스/집중 | 1 | 0.4x |
| glitch | 글리치+노이즈/긴장 | 3 | 1.0x |

- `--strategy` CLI 옵션 또는 장르 자동 매핑 (techno→dense, algorave→collision 등)
- `visual_script.json`에 `"meta"` 필드로 전략 정보 기록

### Vocab 이력 추적 (v5.1)

`vocab_history.json`에 에피소드별 vocab:variant 사용 이력 자동 기록.
- lookback=2: 최근 2개 에피소드 조합 후순위 처리
- `--episode` CLI 옵션으로 이력 기록 (경로에서 자동 추출도 가능)

### 장르 → 비주얼 연동 (v8: ikeda 단일)

ikeda 팔레트(흑백+씬별 accent_color) + hybrid 전용.
GENRE_LAYER_PRESETS: Music 3 + TTS 4 = 7레이어.

| 장르 | Music (리드+보조) | TTS (강조+기본) | blend | palette |
|------|------------------|----------------|-------|---------|
| ikeda | SineWave(0.7)+Waveform(0.4)+Particle(0.3) | TextData(0.7)+Barcode(0.6)+DataStream(0.5)+DataMatrix(0.4) | 0.45 | ikeda |

---

## 5. 음악 엔진 v8

### 장르 프리셋 (v8: ikeda 단일)

| 장르 | BPM | 핵심 | 비고 |
|------|-----|------|------|
| **ikeda** | **60** | **사인파 간섭 + 데이터 클릭 + 초고주파 + 텍스처 모듈** | **v8 단일 장르** |

- v8 확장: 유클리드 리듬(from algorave) + 피드백 텍스처(from harsh_noise) + bytebeat 미세 텍스처 + 킥/리듬 백본(from techno) + 멜로딕 사인 시퀀스(SINE_MELODY_SEQUENCES 5종)
- TEXTURE_MODULES 시스템: 에피소드별 3~4개 텍스처 모듈 자동 선택 (music_history.json 기반)

### v6 ikeda 합성 함수 (3개 신규)
- **sine_interference**: 순수 사인파 2개 합 → 맥놀이, script_data의 숫자가 주파수 결정
- **data_click**: 극초단(0.003s) 1사이클 사인파 버스트, 대본 숫자를 주파수로 인코딩
- **ultrahigh_texture**: 8-20kHz 대역통과 노이즈, 매우 조용한 디지털 공기 역할
- **⚠ EP005 교훈**: 위 3개만으로는 음악이 아닌 노이즈. 최소한의 리듬(kick/click 패턴)+멜로디(sine 시퀀스) 필수

### v8 마스터링 체인 (ikeda 전용)
```
피크 노멀라이즈 → 소프트 새츄레이션 (tanh drive=1.2) → RMS 노멀라이즈 (-10dB) → 피크 리미팅 (0.95) → 16bit WAV
```

### v6.1 Song Arc 시스템 (기승전결)
음악 1곡 풀버전에 매크로 에너지 엔벨로프 적용 (기존 섹션 시스템 위의 상위 레이어)

| 아크 | 구간 | 설명 |
|------|------|------|
| **narrative** | intro(0-15%)→buildup(15-55%)→climax(55-80%)→outro(80-100%) | 기승전결 |
| crescendo | grow(0-85%)→release(85-100%) | 점진 성장 |
| flat | constant(0-100%) | 아크 없음 (하위호환) |

- CLI: `--arc narrative|crescendo|flat` (기본: narrative)
- `export_raw_visual_data()`에 `arc_energy`(float), `arc_phases`(string) 배열 포함
- 비주얼 렌더러가 `arc_energy`로 음악 레이어 강도를 변조

### v7-P4 박자 정렬 시스템
- `generate_music_script()`에서 음악 섹션 경계를 마디(bar) 경계로 퀀타이즈
- 비주얼 씬 경계는 유지 (나레이션 타이밍 정확), 음악만 마디 단위 정렬
- `_quantize_to_bar()` 헬퍼: `round(time / bar_duration) * bar_duration`
- 6개 전 장르 지원, 인접 섹션 연속성 + 최소 1마디 보장

### v7-P1 semantic_intensity → 음악 연동
- script_data의 si(0~1) → 음악 마스터 볼륨 변조 (0.7+si×0.6) + 텍스처 밀도 변조 (0.5+si)
- `_build_si_envelope()`: 시간 도메인 si 배열, 0.5초 스무딩
- **음악-비주얼-대사 삼위일체**: 비주얼과 동일한 si 소스를 음악이 공유

### v7-P2 Adaptive Song Arc
- si 곡선에서 내러티브 구조 자동 추출 → 음악 기승전결을 대본과 정렬
- `_compute_adaptive_arc()`: 3s heavy smoothing → 피크 탐지 → 동적 phase 경계
- `_build_arc_from_phases()`: phase→에너지 엔벨로프 공통 로직 분리
- **Fallback**: script_data 없거나 si range < 0.08 → narrative preset
- CLI: `--arc adaptive` (기존 narrative/crescendo/flat에 추가)

---

## 6. UI 레이아웃 (9:16, 1080x1920)

```
┌──────────────────────────┐  y=0
│     상태바 (가려짐)        │  ~100px
├──────────────────────────┤  y=180
│    제목 (72px, 900weight) │  190px
├──────────────────────────┤  y=370
│     비주얼 영역            │
│     1080x1080             │
│     Canvas 2D + SVG       │
│     + PostProcess 오버레이 │
├──────────────────────────┤  y=1450
│     자막 (54px/62px)      │  비주얼 안쪽 하단
├──────────────────────────┤
│     YouTube UI 영역       │  ~470px (가려짐)
└──────────────────────────┘  y=1920
```

---

## 7. 컬러 팔레트 (7종)

| 이름 | 배경 | 액센트 | 용도 |
|------|------|--------|------|
| phantom | #06060A | #8B5CF6 | 성찰/명상 (기본) |
| neon_noir | #050508 | #FF2D55 | 긴장/경고/algorave |
| cold_steel | #08080C | #00F0FF | 분석/논리/harsh_noise |
| ember | #0A0806 | #FF6B00 | 따뜻함/위로 |
| synapse | #060618 | #4169E1 | 각성/연결 |
| gameboy | #0f380f | #9bbc0f | v5 8bit (bytebeat/chiptune) |
| c64 | #40318D | #A59ADE | v5 레트로 대안 |
| **ikeda** | **#000000** | **#FFFFFF (씬별 전환)** | **v6 데이터아트 (모노크롬+감정색)** |

---

## 8. 프로젝트 파일 구조

```
enometa-shorts/
├── src/
│   ├── components/
│   │   ├── VisualSection.tsx           # VOCAB_MAP (37키) + hybrid 전용 (Python배경+vocab오버레이)
│   │   ├── PythonFrameBackground.tsx   # v5.1: Hybrid 모드 프레임 배경
│   │   ├── LogoEndcard.tsx             # v2: 파티클 수렴 엔드카드 (다이나미즘 강화)
│   │   ├── TitleSection.tsx            # 제목 표시 (endcardStartFrame fade-out 연동)
│   │   └── vocab/                      # 22개 비주얼 컴포넌트
│   │       ├── (기존 20개)
│   │       ├── PixelGrid.tsx           # v5: 8bit 격자 (4모드)
│   │       └── PixelWaveform.tsx       # v5: 8bit 파형 (3모드)
│   ├── types.ts                        # VisualScriptMeta (render_mode 등)
│   └── utils/
│       └── palettes.ts                 # 7종 팔레트 (gameboy/c64 추가)
├── scripts/
│   ├── enometa_music_engine.py         # v8 (ikeda 단일, 텍스처 모듈 확장)
│   ├── script_data_extractor.py        # v6: 대본 데이터 추출기
│   ├── visual_renderer.py              # v5.1+v6: Python 비주얼 렌더러
│   ├── visual_layers/                  # v5.1+v6: 비주얼 레이어 모듈 (9개 + 공유 이펙트)
│   │   ├── bytebeat_layer.py           # bytebeat→픽셀 직접 변환
│   │   ├── waveform_layer.py           # 오디오 파형 직접 렌더링
│   │   ├── particle_layer.py           # numpy 벡터 파티클
│   │   ├── data_matrix_layer.py        # Ryoji Ikeda 스타일 데이터 시각화
│   │   ├── feedback_layer.py           # 자기참조 피드백 루프
│   │   ├── sine_wave_layer.py          # v6: 오실로스코프 사인파
│   │   ├── barcode_layer.py            # v6: UTF-8 바이트 바코드 (v6.2 si 다이나믹)
│   │   ├── data_stream_layer.py        # v6: 데이터 스트림 스크롤 (v6.2 si 다이나믹)
│   │   ├── text_data_layer.py          # v6: 터미널 텍스트 카드 (v6.2 si 다이나믹)
│   │   ├── tts_effects.py              # v6.2 신규: 10개 공유 이펙트 함수
│   │   └── composite.py               # additive blend 합성
│   ├── visual_script_generator.py      # v8 (--strategy --episode, ikeda 전용)
│   ├── visual_strategies.py            # v5.1 (6종 전략 프리셋)
│   ├── subtitle_grouper.py             # v5.1 (자막 2줄 그루핑)
│   └── (기타 generate_voice_edge, audio_mixer 등)
├── vocab_history.json                  # v5.1 (에피소드별 vocab 이력)
├── episodes/ep001~004/
└── package.json
```

---

## 9. 에피소드 진화 로그

### EP001 — "당신의 뇌는 어제를 복사하고 있다"
- 기반 구축: 20 vocab, 10 악기, 15 감정

### EP002 — "당신의 오답이 뇌를 가장 크게 깨운다"
- 어휘 활용 + BGM 장르 다양화 피드백

### EP003 — (제작 완료)
- 음악 v3→v4: 19악기, 22감정, 5장르, 리액티비티 2배

### EP004 — "우리의 선택은 몇 번이나 우리의 것이었을까"
- 주제: 의사결정 소진 (Decision Fatigue)
- 나레이션 93.37초, edge-tts, 2982프레임
- 음악: techno 128bpm D_minor
- 비주얼: neon_noir 팔레트, 11씬, counter_up+data_bar
- 비주얼 차별화 시스템(variant/strategy/history) 도입 시점

### EP005 — "공포와 각성의 화학식은 같다"
- 주제: 공포/각성의 화학적 동일성 → 몰입 전환 (데이터아트형)
- 나레이션 123.602초, edge-tts, 3888프레임 (+ 6s 엔드카드)
- 음악: ikeda 60bpm (sine_interference + data_click + ultrahigh_texture)
- 비주얼: ikeda 팔레트(흑백+씬별 accent_color), hybrid 렌더, 13씬
- Hybrid Visual Architecture 첫 적용 에피소드
- **피드백 (rating 5/10)**:
  - 음악이 노이즈에 가까움 → ikeda라도 최소 리듬/멜로디 필수
  - 비주얼 패턴 단조/반복 → 파티클+다양한 패턴 혼합 필요
  - Remotion vocab 미활용 → hybrid에서도 vocab 오버레이 필수
  - 오디오 민감도 과포화 → semantic_intensity 기반 다이나믹 레인지 필요

### v5 업그레이드 (EP003 이후)
- 음악 v4→v5: 6개 Raw Synthesis 함수, 장르 전면 교체 (bytebeat/algorave/harsh_noise/chiptune)
- 비주얼 v5: PixelGrid + PixelWaveform 8bit 컴포넌트, 장르-비주얼 자동 연동
- 팔레트 v5: gameboy + c64 추가
- 성능: smooth_envelope O(n) 최적화

### 진화 방향
```
EP001  [███░░░░░░░] 기반 구축 (20 vocab, 10 악기, 15 감정)
EP002  [████░░░░░░] 어휘 활용 + 피드백 수집
EP003  [█████░░░░░] 음악 v4 (19 악기, 22 감정, 5 장르)
v5     [██████░░░░] Raw Synthesis (23 악기, 6 합성법) + 8bit 비주얼 (22 vocab)
EP004  [██████░░░░] 비주얼 차별화 (variant/strategy/history)
v5.1   [███████░░░] Hybrid Visual Architecture (Python+Remotion)
EP005  [████████░░] ikeda 장르, script_data 파이프라인, 피드백 루프
v6     [████████░░] ikeda 3합성+4레이어, hybrid vocab 규칙
v6.2   [████████░░] semantic_intensity 구현 완료, TTS 다이나믹 비주얼, tts_effects 공유 모듈
v6.3   [████████░░] GENRE_LAYER_PRESETS v2: 모든 장르 7레이어, blend_ratio 재조정
v6.4   [████████░░] LogoEndcard v2: 타이밍 리디자인 + 파티클 다이나미즘 + 제목 fade-out 버그 수정
v6.5   [████████░░] 볼륨 밸런스: TTS:BGM = 4:6 (음악 우선 믹싱)
v7-P4  [████████░░] 박자 정렬: 음악 섹션 경계를 마디 경계로 퀀타이즈
v7-P1  [████████░░] si→음악 연동: semantic_intensity로 볼륨+밀도 실시간 변조 (삼위일체)
v7-P2  [████████░░] Adaptive Song Arc: si 곡선 기반 적응형 기승전결 자동 추출
v7-P5  [████████░░] 감정 전환 크로스페이드: 텍스처 delta fade-in/fade-out
v7-P3  [████████░░] script_data 전장르 활용: 6개 장르 대본 데이터 기반 악기 파라미터 변조
v7-P9  [████████░░] Pulse Train/Granular: ikeda 펄스 트레인(si→20~200Hz) + 그래뉼러 클라우드
v7-P8  [████████░░] 연속 악기 si 게이트: si<0.15→10%, si<0.30→40% 자동 감쇠 (45x 다이나믹 레인지)
v7-P7  [█████████░] 에피소드 간 음악 이력: KEY_PRESETS 7키 + music_history.json + 키/패턴 자동 다양화
v7-P6  [█████████░] 가변 BPM: si 기반 섹션별 ±15% 템포 변조 + 이벤트 기반 리듬 배치 (v7 9/9 완료)
v6.6   [█████████░] Hybrid Vocab Overlay: VisualSection.tsx hybrid 모드에서 vocab 시맨틱 레이어 오버레이 활성화
v8     [█████████░] ikeda 단일 장르 + Hybrid 전용화 + ikeda 확장 (5개 장르 제거, SINE_MELODY_SEQUENCES, TEXTURE_MODULES)
EP010  [█████████░] 표현 다양화 (35+ vocab, GPU 가속 레이어)
EP020+ [██████████] 디지털 아트 완성체 (Remotion 제거 → Python only)
```

---

## 10. 환경

| 항목 | 버전 |
|------|------|
| Node.js | v24.14.0 |
| Remotion | 4.0.431 |
| React | 19.2.4 |
| Python | 3.11.9 |
| FFmpeg | 8.0.1 |
| OS | Windows 11 Pro |
| GPU | RTX 3060 Laptop 6GB |

---

## 11. 사용자 선호

- Python 코딩으로 음악 생성 (AI 모델 의존 대신 직접 제어)
- 음악: Raw Synthesis 전자음악 — bytebeat/algorave/harsh_noise/chiptune/techno
- 8bit/칩튠 사운드 좋아함
- 패드 사운드 원하지 않음 — raw하고 자극적인 전자음악 본연의 매력 선호
- 비주얼: 디지털 데이터아트 + 8bit 레트로 (Max Cooper / TouchDesigner 영감)
- 글쓰기: "담백한 격조" — 팩트로 위로하는 철학 (Writing v11: SI 안무 + 비주얼 vocab 연동 + 시스템 최적화 점수 + 글 컨펌 게이트)
- 효율: 비용 0원, 로컬 실행 우선

---

## 12. Feedback Loop 시스템

매 에피소드 완료 후 피드백을 구조적으로 기록·반영·전파하는 3계층 시스템.

### 구조
```
[1] episodes/epXXX/feedback.json  →  에피소드별 리뷰 기록
[2] scripts/feedback_defaults.json  →  시스템 누적 학습 (기본값)
[3] ENOMETA_ClaudeCode_Brief + MEMORY.md + SYSTEM_SNAPSHOT  →  문서 최신화
```

### 에피소드 feedback.json 스키마
- `overall_rating` / `music.rating` / `visual.rating` / `narration.rating` / `script.rating` (1-5)
- `issues[]`: `{type, target, detail, severity: minor|major}`
- `liked[]` / `disliked[]`: 자유 텍스트
- `system_suggestions[]`: 시스템 변경 제안

### 시스템 전파 규칙

| 조건 | 행동 |
|------|------|
| severity = major | 즉시 feedback_defaults.json에 반영 |
| 같은 issue type+target 2회 이상 반복 | feedback_defaults.json에 반영 |
| 사용자가 "항상/절대" 표현 사용 | 즉시 feedback_defaults + MEMORY.md |

### 워크플로우
1. 사용자가 에피소드 확인 후 구두 피드백
2. Claude가 `episodes/epXXX/feedback.json` 구조화 작성
3. 이전 에피소드 feedback.json 스캔 → 반복 패턴 확인
4. 해당 시 `scripts/feedback_defaults.json` 업데이트
5. **모든 마스터 문서 + SYSTEM_SNAPSHOT + MEMORY.md 최신화** (v6 워크플로우 규칙)
6. "이번 EP에서 배운 것" + "다음 EP에 반영될 변경" 요약

### 리액티비티 규칙 (v6, EP005 피드백) — **v6.2 구현 완료**
- `semantic_intensity`(0-1) 추출 **구현 완료** — `compute_semantic_intensity()` 4요소 가중합산
  - VERB_ENERGY **101개** 동사 ("폭발" 0.9 ~ "있" 0.1) — 파괴/변혁/인지/상태 전 범위
  - EMOTION_INTENSITY **68개** 감정어 ("공포" 0.9 ~ "정적" 0.1) — 극단~잔잔함 5단계
  - SCIENCE_TERMS **85개** 용어 — 컴퓨팅/데이터/뇌과학/철학 도메인
  - CHEMICALS **19개**, BODY_PARTS **30개**
  - **custom_dictionary.json** — 사용자 커스텀 단어 외부 사전 (자동 로드/머지)
  - **미등록 단어 감지**: `--update-dict` 대화형 사전 업데이트, `--report-only` 리포트만
  - 문장 구조: 짧은 문장(+0.2), 느낌표(+0.15), 물음표(+0.1)
  - byte_variance 정규화 (0-1)
- visual_renderer.py ctx 확장: `semantic_intensity`, `current_keywords`, `reactive_level`
- TTS 레이어 3종 전면 리라이트: si 비례 크기/색상/이펙트 다이나믹
- tts_effects.py 공유 모듈: 10개 이펙트 함수 (scanlines, chromatic_aberration, glitch 등)
- `semantic_intensity`가 기본 레벨(0.1~0.8), rms는 ±20% 미세 변조만
- `byte_variance` 노이즈 임계값 상향 (현재 2000은 거의 모든 단어 초과)

---

*이 문서는 Claude 웹/코드 간 컨텍스트 전달용. 프로젝트 경로: `C:\옵시디언\enometa\enometa-shorts\`*
