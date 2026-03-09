# ENOMETA 비주얼 아키텍처 상세 문서

> 마지막 업데이트: v22 (2026-03-10)
> 이 문서는 최종 영상을 구성하는 3개 비주얼 파트를 설명한다.

---

## 미학 원칙 — 백남준 DNA

ENOMETA 비주얼의 근본 미학. 모든 비주얼 구현은 이 원칙을 따른다.

| 원칙 | 설명 |
|------|------|
| **원초적 + 불완전** | 깔끔함을 거부. CRT 왜곡, 신호 글리치, 아날로그 노이즈가 기본 질감. 매끄러움은 적. |
| **너드 + 키치** | 데이터아트의 진지함과 8bit 레트로의 장난기가 공존. 터미널 미학. |
| **고감도 반응** | 오디오→비주얼 반응은 과감하게. onset/bass/rms 감도를 높게 유지. 미세함보다 강렬함. |
| **ASCII/픽셀은 크고 거칠게** | 작고 섬세한 것이 아닌, 화면을 채우는 존재감. 최소 fontSize 32px+. |
| **죽은 코드 금지** | 구현한 코드는 반드시 파이프라인에서 실제 호출·렌더링. 스텁·미연결 코드 절대 금지. |

### 참조 미학

- **백남준**: CRT 왜곡, 신호 글리치, 비디오 피드백, 아날로그 노이즈
- **Ryoji Ikeda**: 극한 데이터 밀도, 흑백 미니멀, 숫자/코드 스트림
- **Max Cooper**: 유기적 파티클, 수학적 구조, 자연+알고리즘 융합
- **8bit/레트로**: Commodore 64, Game Boy, 픽셀 스프라이트, 블록 문자

### PostProcess 미학 수치 (v22)

| 효과 | v21 | v22 | 변화 |
|------|-----|-----|------|
| 스캔라인 opacity | 0.04 × 0.6 = 2.4% | 0.12 × 0.8 = ~9.6% | **4배** |
| 색수차 너비 | 3px | 12-20px | **5배** |
| 색수차 opacity | 4-14% | 8-26% | **2배** |
| onset 플래시 | 25-60% | 30-70% | 강화 |
| CRT 티어링 | 없음 | onset 시 5개 수평 스트립 | **신규** |
| 노이즈 그레인 | 없음 | 항상 30-50% overlay | **신규** |
| 인터레이스 플리커 | 없음 | 3프레임 주기 | **신규** |

---

## 전체 구조 요약

최종 영상은 **3개 파트가 위에서 아래로 겹쳐지는** 구조다.

```
파트 1 — Python 배경 PNG     : numpy + Pillow로 그린 배경 이미지
     ↑ 그 위에
파트 2 — Vocab 오버레이      : Remotion React 컴포넌트 (30종 애니메이션)
     ↑ 그 위에
파트 3 — PostProcess         : 항상 적용되는 마무리 효과 5종
```

Python이 그린 배경 PNG는 매 프레임마다 `frames/000000.png~` 파일로 저장되고,
Remotion이 `PythonFrameBackground` 컴포넌트로 불러와 화면 뒤에 깐다.
그 위에 Vocab 애니메이션과 PostProcess를 겹쳐서 최종 프레임이 완성된다.

---

## 파트 1 — Python 배경 레이어

**담당 파일**: `scripts/visual_renderer.py`, `scripts/visual_layers/`

### 어떻게 작동하나?

1. `visual_renderer.py`가 에피소드 비주얼 장르를 읽어 **레이어 목록**을 결정
2. 각 레이어가 `render(ctx)` → `np.ndarray (1080×1080×3 uint8)` 반환
3. 레이어들을 **additive 블렌딩**으로 차례로 합성
4. 완성된 배경을 PNG로 저장

```
SineWaveLayer.render(ctx)   → 배경 파형 이미지
        + (additive)
WaveformLayer.render(ctx)   → 음악 파형 이미지
        + (additive)
ParticleLayer.render(ctx)   → 입자 이미지
        + ...
        = 최종 배경 PNG
```

### 10개 레이어 설명

| 레이어 | 역할 | 그리는 것 |
|--------|------|----------|
| `SineWaveLayer` | 신호 배경 | 정현파(sin) 곡선 여러 겹. 에피소드 분위기의 기저 |
| `WaveformLayer` | 음악 반응 | 오디오 파형을 막대 또는 선으로 시각화 |
| `ParticleLayer` | 입자 시스템 | SI에 따라 흩어지고 모이는 점들 |
| `TextDataLayer` | 텍스트 데이터 | 나레이션 키워드를 데이터 형식으로 배치 |
| `BarcodeLayer` | 바코드 스캔 | 세로줄 바코드 패턴, 데이터 밀도 표현 |
| `DataStreamLayer` | 터미널 스트림 | 터미널처럼 흘러내리는 ASCII 텍스트 |
| `DataMatrixLayer` | 행렬 패턴 | 격자 형태로 배치된 수치/기호 |
| `FeedbackLayer` | 화면 잔상 | 이전 프레임이 흐릿하게 남는 피드백 효과 |
| `BytebeatLayer` | 알고리즘 신호 | bytebeat 수식으로 생성된 픽셀 패턴 (8bit 감성) |
| `AsciiBackgroundLayer` | ASCII 배경 | 12×12px 셀 그리드에 SI 기반 문자 밀도 표현 |

### SI (Semantic Intensity)가 레이어 강도를 바꾼다

`semantic_intensity`는 나레이션 대본의 "감정 강도" 값이다 (0.0 ~ 1.0).
SI가 높으면 = 긴장감 높은 문장. 낮으면 = 잔잔한 문장.

레이어마다 SI에 반응하는 방식이 다르다:

| 레이어 | SI 반응 방식 | 의도 |
|--------|------------|------|
| `SineWaveLayer` | SI 높을수록 **약해짐** `max(0.35, 1.0 - si × 0.45)` | 텍스트 클라이맥스 때 배경이 물러남 |
| `WaveformLayer` | SI에 **비례** `0.25 + si × 0.75` | 긴장감 구간에 음악 강조 |
| `ParticleLayer` | SI에 **비선형 비례** `si^1.5` | 클라이맥스 직전에 입자 폭발 |
| `TextDataLayer` | **항상 강함** `0.88 + si × 0.12` | 핵심 레이어라 항상 80% 이상 |
| `BarcodeLayer` | SI에 비례 `0.60 + si × 0.40` | 데이터 밀도 상승 표현 |
| `DataStreamLayer` | SI에 비례 `0.50 + si × 0.50` | 정보 흐름 가속 |
| `DataMatrixLayer` | SI에 약한 곡선 `si^0.6` | 최소 55% 보장 |
| `AsciiBackgroundLayer` | **항상 은은함** `0.15 + si × 0.15` | 최대 30%로 배경에 머뭄 |

### 비주얼 장르별 레이어 조합

에피소드 음악 장르가 비주얼 장르를 결정한다.

```
음악 장르          비주얼 장르
──────────────────────────────────────
acid / glitch  →  enometa  (데이터아트)
ambient/dub    →  cooper   (유기적 파티클)
minimal/IDM    →  abstract (기하학적 신호)
techno/indus   →  data     (수치 분석)
```

비주얼 장르마다 레이어 조합이 다르다:

**enometa** — 데이터아트 중심, 모든 레이어 균형 배치

| 레이어 | 기본 intensity | 역할 |
|--------|-------------|------|
| SineWaveLayer | 0.70 | 신호 배경 |
| WaveformLayer | 0.40 | 음악 반응 |
| ParticleLayer | 0.30 | 입자 보조 |
| TextDataLayer | 1.20 | 주요 텍스트 |
| BarcodeLayer | 0.85 | 데이터 스트림 |
| DataStreamLayer | 0.75 | 터미널 아트 |
| DataMatrixLayer | 0.90 | 행렬 패턴 |
| AsciiBackgroundLayer | 0.20 | 은은한 배경 |

**cooper** — 유기적 파티클 중심, 데이터 최소화

| 레이어 | 기본 intensity |
|--------|-------------|
| SineWaveLayer | 0.90 |
| WaveformLayer | 0.60 |
| ParticleLayer | 0.70 ← 강화 |
| TextDataLayer | 0.70 |
| DataStreamLayer | 0.90 |
| AsciiBackgroundLayer | 0.18 |

**abstract** — 기하학적 신호 극대화, 파티클 없음

| 레이어 | 기본 intensity |
|--------|-------------|
| SineWaveLayer | 1.00 ← 최강 |
| WaveformLayer | 0.80 |
| TextDataLayer | 0.60 |
| DataMatrixLayer | 0.95 ← 강화 |
| AsciiBackgroundLayer | 0.22 |

**data** — 수치/텍스트 극대화, 신호 최소화

| 레이어 | 기본 intensity |
|--------|-------------|
| WaveformLayer | 0.50 |
| SineWaveLayer | 0.40 ← 최소 |
| TextDataLayer | 1.00 ← 최강 |
| BarcodeLayer | 1.00 ← 최강 |
| DataStreamLayer | 0.95 |
| DataMatrixLayer | 0.90 |
| AsciiBackgroundLayer | 0.25 |

### blend_ratio: 음악 반응 vs 텍스트 반응 비율

배경은 두 소스의 합성이다:
- **음악 레이어**: `raw_visual_data` (오디오 분석 데이터로 그림)
- **TTS 레이어**: `script_data` (나레이션 텍스트 데이터로 그림)

```
blend_ratio = 0.45 → 음악 45% + 텍스트 55%
blend_ratio = 0.55 → 음악 55% + 텍스트 45%
blend_ratio = 0.35 → 음악 35% + 텍스트 65%
```

| 장르 | blend_ratio | 성격 |
|------|------------|------|
| enometa | 0.45 | 균형 |
| cooper | 0.55 | 음악 반응 강조 |
| abstract | 0.50 | 동등 |
| data | 0.35 | 텍스트 데이터 강조 |

---

## 파트 2 — Vocab 오버레이

**담당 파일**: `src/VisualSection.tsx`, `src/components/`

### 어떻게 작동하나?

`visual_script.json`의 각 씬에는 `vocab` 배열이 있다.

```json
{
  "vocab": ["particle_birth", "lissajous"],
  "start_sec": 3.2,
  "end_sec": 7.8
}
```

`VisualSection.tsx`가 이 배열을 읽어 해당 씬 구간에 Remotion `<Sequence>`로 컴포넌트를 마운트한다.
모든 vocab 컴포넌트는 `useCurrentFrame()`으로 오디오 데이터를 받아 실시간으로 반응한다.

### Vocab 30종 카테고리별 정리

#### 입자 시스템 (7종)
| vocab | 설명 |
|-------|------|
| `particle_birth` | 중심에서 입자가 탄생해 퍼짐 |
| `particle_scatter` | 입자가 사방으로 흩어짐 |
| `particle_converge` | 외곽 입자가 중심으로 수렴 |
| `particle_orbit` | 입자들이 중심 주위를 공전 |
| `particle_escape` | 입자들이 화면 밖으로 탈출 |
| `particle_chain_awaken` | 입자들이 연결되며 깨어남 |
| `particle_split_ratio` | 입자 집단이 비율에 따라 분리 |

#### 흐름/색상 (8종)
| vocab | 설명 |
|-------|------|
| `flow_field_calm` | 잔잔한 흐름 벡터 필드 |
| `flow_field_turbulent` | 격렬한 흐름 벡터 필드 |
| `color_shift` | 전체 색상 전환 |
| `color_shift_warm` | 따뜻한 계열로 색상 전환 |
| `color_shift_cold` | 차가운 계열로 색상 전환 |
| `color_drain` | 색상이 빠져나가며 탈색 |
| `color_bloom` | 색상이 피어오름 |
| `brightness_pulse` | 밝기가 맥박처럼 박동 |
| `light_source` | 이동하는 광원 효과 |

#### 데이터/수학 (5종)
| vocab | 설명 |
|-------|------|
| `counter_up` | 숫자가 빠르게 카운팅 |
| `neural_network` | 뉴럴 네트워크 노드 연결 시각화 |
| `loop_ring` | 링 형태의 루프 애니메이션 |
| `fractal_crack` | 프랙탈 균열 패턴 |
| `data_bar` | 데이터 막대 차트 |
| `data_ring` | 데이터 링 차트 |

#### 격자/파형 (5종)
| vocab | 설명 |
|-------|------|
| `grid_morph` | 격자가 변형되며 흔들림 |
| `grid_mesh` | 메쉬 격자 (격자 선 강조) |
| `waveform` | 기본 파형 시각화 |
| `waveform_spectrum` | 주파수 스펙트럼 막대 |
| `waveform_circular` | 원형 파형 시각화 |

#### 텍스트/타이포그래피 (4종)
| vocab | 설명 |
|-------|------|
| `text_reveal` | 타이프라이터 효과로 텍스트 등장 |
| `text_wave` | 텍스트가 물결처럼 흔들림 |
| `text_glitch` | 텍스트 글리치 (노이즈, 색 분리) |
| `text_scatter` | 글자들이 흩어졌다가 모임 |

> 4종 모두 `TextReveal` 컴포넌트를 공유하며, vocab 값이 모드를 결정한다.

#### 기호/ASCII (4종) — v22 백남준 미학 강화

| vocab | 설명 |
|-------|------|
| `symbol_morph` | **v2: ASCII 아트 그리드** — 품사별 대형 문자 패턴 (28col×14row, fontSize 32). noun=밀도 블록, verb=방향 흐름, adj=파동, science=데이터 격자, philosophy=이원성. onset 시 40% 글리치. |
| `ascii_block` | **강화**: cellSize 42px, 글리치 60%, 이중 glow, 한글 80px |
| `ascii_shape` | **강화**: fontSize 36+bass*16, 호흡 ±8%+rms, 글리치 55%, onset flash 50% |
| `ascii_matrix` | **강화**: fontSize 34, 키워드 1.25em, 이중 glow 강화 |

> `symbol_morph`는 v22에서 SVG 추상 도형 → ASCII 캐릭터 그리드로 전면 교체됨.
> `ascii_block`은 `ascii_text` 파라미터로 표시할 영어 텍스트를 받는다.
> Claude가 파이프라인 개입 시 맥락에 맞는 영어를 직접 삽입한다.

#### 8bit/레트로 (7종)
| vocab | 설명 |
|-------|------|
| `pixel_grid` | 기본 픽셀 격자 |
| `pixel_grid_outline` | 아웃라인만 있는 픽셀 격자 |
| `pixel_grid_life` | Game of Life 셀룰러 오토마타 |
| `pixel_grid_rain` | Matrix 스타일 픽셀 비 |
| `pixel_waveform` | 픽셀 아트 파형 |
| `pixel_waveform_steps` | 계단식 픽셀 파형 |
| `pixel_waveform_cascade` | 폭포처럼 쏟아지는 픽셀 파형 |

#### 3D/Terra (6종)
| vocab | 설명 |
|-------|------|
| `terra_globe` | 3D 지구본 회전 |
| `terra_globe_data` | 지구본 + 데이터 포인트 |
| `terra_flythrough` | 3D 공간 비행 |
| `terra_tunnel` | 터널 돌진 효과 |
| `terra_terrain` | 3D 지형 시각화 |
| `terra_terrain_bars` | 지형 + 데이터 막대 |

> Terra 씬은 `@remotion/three` 기반 WebGL 렌더링. 씬당 최대 1개 사용.

### Vocab이 선택되는 방식

`visual_script_generator.py`가 각 씬의 emotion, SI, 키워드를 분석해 vocab을 자동 선택한다.
Claude가 Gate 1 개입 시 직접 수정할 수 있다.

| SI 범위 | 최대 vocab 수 |
|---------|------------|
| ≤ 0.25 | 1개 |
| 0.25~0.72 | 2개 |
| ≥ 0.72 | 3개 |
| ≥ 0.80 | 전략 승격 (더 강한 vocab 선택) |

---

## 파트 3 — PostProcess

**담당 파일**: `src/PostProcess.tsx`

### 어떻게 작동하나?

PostProcess는 모든 씬에 **항상 적용**된다 (zIndex=10, 가장 위).
vocab에 넣을 필요 없이 자동으로 렌더링된다.

5가지 효과를 오디오 데이터에 실시간으로 반응하며 겹쳐 그린다.

```
오디오 데이터 구조:
  audio.onset  : boolean — 킥 드럼 감지 여부
  audio.rms    : 0~1     — 전체 음량 에너지
  audio.bass   : 0~1     — 저주파 (킥, 베이스)
  audio.high   : 0~1     — 고주파 (하이햇, 심벌)
```

### 8가지 효과 상세 (v22 백남준 미학)

#### 1. 비네트 (Vignette)
화면 가장자리를 어둡게 해서 중앙으로 시선을 모은다.
bass가 강해질수록 가장자리가 더 어두워진다.

```
강도 = 0.5 + audio.bass × 0.25
bass 0.0 → 50% 어두움
bass 1.0 → 75% 어두움
```

#### 2. 스캔라인 (Scanline) — v22 강화
3px 주기 수평선. rms 반응 추가.

```
효과: 3px 주기 수평선 → CRT 텍스처
opacity: 0.12 × (0.75 + rms × 0.15) = ~9-10%
음악 반응: rms → opacity 변화
```

#### 3. 비트 플래시 (Beat Flash)
킥 드럼이 감지되는 순간 화면 전체가 흰색으로 순간 밝아진다.

```
조건: audio.onset === true 일 때만 발동
강도 = 0.25 + audio.rms × 0.35
약한 킥 → 25% 흰색
강한 킥 → 60% 흰색
```

#### 4. RMS 글로우 (RMS Glow)
음악이 커질수록 화면 중앙에서 황금빛 글로우가 방사된다.
`screen` 블렌딩 모드로 배경색과 자연스럽게 합성된다.

```
강도 = 0.05 + audio.rms × 0.15
RMS 0.0 → 5% 글로우
RMS 1.0 → 20% 글로우
```

#### 5. 색수차 (Chromatic Aberration) — v22 강화
화면 좌우 가장자리에서 빨강(왼쪽) / 파랑(오른쪽) 색 분리. 폭 5배, opacity 2배.

```
너비 = 12 + audio.high × 8 (12~20px)
강도 = 0.08 + audio.high × 0.18
고주파 없음 → 8% 색 분리, 12px
강한 고주파 → 26% 색 분리, 20px
```

#### 6. CRT 수평 티어링 (v22 신규)
onset 시 수평 줄이 어긋나는 백남준 스타일 신호 왜곡.

```
조건: onset === true 일 때만
스트립 수: 5개
높이: 2~10px (랜덤)
수평 이동: ±30px (랜덤)
opacity = 0.06 + rms × 0.14
```

#### 7. 노이즈 그레인 (v22 신규)
SVG feTurbulence 기반 필름 그레인. 2프레임마다 시드 변경.

```
항상 켜짐
opacity = 0.3 + rms × 0.2
blend: overlay
```

#### 8. 인터레이스 플리커 (v22 신규)
3프레임마다 미세 어두움. CRT 인터레이스 감성.

```
주기: 3프레임마다 발동
opacity: 3% 검정 오버레이
```

### PostProcess 효과 한눈에 보기

| 효과 | 항상 켜짐 | 오디오 반응 | 반응 대상 |
|------|---------|-----------|---------|
| 비네트 | ✓ | ✓ | bass |
| 스캔라인 | ✓ | ✓ | rms |
| 비트 플래시 | 킥 감지 시만 | ✓ | onset + rms |
| RMS 글로우 | ✓ | ✓ | rms |
| 색수차 | ✓ | ✓ | high |
| CRT 티어링 | 킥 감지 시만 | ✓ | onset + rms |
| 노이즈 그레인 | ✓ | ✓ | rms |
| 인터레이스 | 3프레임 주기 | ✗ | — |

---

---

## 팔레트 시스템

**담당 파일**: `scripts/visual_renderer.py` → `PALETTES`, `GENRE_PALETTE`

팔레트는 Python 배경 레이어의 **색상 톤**을 결정한다.
3가지 색상 키(`bg`, `accent`, `mid`)로 구성된다.

```
bg     = 배경 기본 색 (캔버스 초기 색)
accent = 강조색 (레이어 그릴 때 기본 색)
mid    = 중간 톤 (그라디언트/보조에 사용)
```

### 8종 팔레트

| 이름 | bg | accent | 분위기 |
|------|-----|--------|--------|
| `phantom` | 거의 검정 (6,6,10) | 보라 (139,92,246) | 신비로운 보라 — 어두운 클럽 |
| `neon_noir` | 거의 검정 (5,5,8) | 핫핑크 (255,45,85) | 네온사인 느낌 |
| `cold_steel` | 거의 검정 (8,8,12) | 시안 (0,240,255) | 차갑고 기계적인 파랑 |
| `ember` | 어두운 갈색 (10,8,6) | 주황 (255,107,0) | 불씨, 따뜻한 에너지 |
| `synapse` | 어두운 남색 (6,6,24) | 로얄블루 (65,105,225) | 뇌 시냅스, 전기 신호 |
| `gameboy` | 짙은 초록 (15,56,15) | 연초록 (155,188,15) | Game Boy 레트로 |
| `c64` | 보라색 (64,49,141) | 연보라 (165,154,222) | Commodore 64 레트로 |
| `enometa` | 순검정 (0,0,0) | 순백 (255,255,255) | 흑백 미니멀 — ENOMETA 시그니처 |

### 팔레트 선택 흐름

에피소드 제작 시 `--palette` 옵션으로 지정한다. 지정하지 않으면 비주얼 장르에 따라 자동 선택된다.

```
파이프라인 명령의 --palette 옵션
         ↓
visual_script_generator.py → visual_script.json에 palette 기록
         ↓
visual_renderer.py → PALETTES[palette_name] 로드
         ↓
모든 레이어가 동일 팔레트 색상으로 그림
```

비주얼 장르별 기본 팔레트 (--palette 미지정 시):

| 비주얼 장르 | 기본 팔레트 | 이유 |
|------------|-----------|------|
| `enometa` | `enometa` | 흑백 미니멀, 데이터아트 시그니처 |
| `cooper` | `phantom` | 어두운 보라, 유기적 파티클에 어울림 |
| `abstract` | `synapse` | 청록/남색, 기하학적 구조 |
| `data` | `cold_steel` | 차가운 시안, 수치 분석 |

---

## 비주얼 장르 & 비주얼 무드

### 비주얼 장르 (Visual Genre)

비주얼 장르는 Python 배경 레이어 조합을 결정하는 4가지 분류다.
`visual_renderer.py`의 `GENRE_LAYER_PRESETS`에 정의되어 있다.

음악 장르에서 자동 매핑된다:

```
음악 장르          →  비주얼 장르  →  팔레트       배경 레이어 조합
──────────────────────────────────────────────────────────────────
acid / glitch     →  enometa   →  enometa    데이터아트 중심, 풀레이어
ambient / dub     →  cooper    →  phantom    파티클 중심, 데이터 최소
minimal / IDM     →  abstract  →  synapse    사인파 극대화, 기하학적
techno/industrial →  data      →  cold_steel 텍스트+바코드 극대화
house / microsound→  enometa   →  enometa    기본
```

### 비주얼 무드 (Visual Mood)

비주얼 무드는 Remotion Vocab 선택 전략을 오버라이드하는 4가지 모드다.
`visual_script_generator.py`의 `VISUAL_MOOD_OVERRIDES`에 정의되어 있다.

`--visual-mood` 옵션으로 지정한다 (선택 사항).
지정하면 비주얼 장르 자동 선택보다 우선 적용된다.

| 무드 | 팔레트 | 주입 Vocab | 주입 확률 | 느낌 |
|------|--------|-----------|---------|------|
| `ikeda` | cold_steel | pixel_grid, pixel_waveform, data_bar, waveform_spectrum | 80% | 이케다 류이치 스타일. 흑백, 밀도 높은 격자, 미니멀 데이터 |
| `cooper` | phantom | particle_birth, fractal_crack, neural_network, color_shift | 70% | 쿠퍼 스타일. 유기적 파티클, 자연 성장, 네트워크 |
| `abstract` | phantom | color_shift, loop_ring, lissajous, grid_morph | 75% | 추상/기하학. 색상 전환 + 리사주 곡선 + 격자 변형 |
| `data` | cold_steel | counter_up, data_ring, waveform_spectrum, data_bar | 85% | 수치 분석 중심. 카운터, 스펙트럼, 데이터 바 |

> **"주입 확률"**: 해당 무드의 특화 vocab을 각 씬에 추가할 확률.
> 0.85면 85% 씬에 data 특화 vocab이 자동 추가된다.

### 비주얼 무드 vs 비주얼 장르 차이

| | 비주얼 장르 | 비주얼 무드 |
|-|-----------|-----------|
| 영향 범위 | Python 배경 레이어 조합 | Remotion Vocab 선택 |
| 설정 방법 | 음악 장르에서 자동 매핑 | `--visual-mood` 수동 지정 |
| 우선순위 | 낮음 (자동) | 높음 (오버라이드) |
| 비유 | 방의 벽지와 조명 | 방 안에 놓는 가구 |

---

## 씬별 감정 색상 (Emotion Color)

씬마다 `emotion` 필드가 있고, 이에 따라 accent 색이 바뀐다.
`ENOMETA_EMOTION_COLORS`에서 emotion → RGB 매핑을 한다.
씬 전환 시 5프레임에 걸쳐 부드럽게 페이드된다.

| emotion 그룹 | 색상 | 느낌 |
|-------------|------|------|
| `neutral` / `flow` | 순백 (255,255,255) | 안정, 흐름 |
| `curious` / `neutral_curious` | 연보라 (200,200,255) | 궁금증, 탐구 |
| `neutral_analytical` | 연파랑 (180,220,255) | 분석, 이성 |
| `tension` / `fear` | 빨강 (255,30,60) | 긴장, 공포, 위기 |
| `awakening` | 시안 (0,240,255) | 각성, 발견 |
| `climax` | 초록 (0,255,65) | 데이터 클라이맥스 |
| `resolution` | 연보라 (180,180,255) | 해소, 마무리 |
| `somber` | 회색 (120,120,160) | 무거움, 슬픔 |
| `fade` | 진회색 (100,100,100) | 사라짐 |

---

## 3파트 합성 순서 (zIndex)

| 레이어 | 담당 | zIndex |
|--------|------|--------|
| Python 배경 PNG | PythonFrameBackground | 0 (가장 뒤) |
| Vocab 컴포넌트들 | VisualSection | 1~9 |
| PostProcess | PostProcess | 10 (최상단) |
| SubtitleSection (자막) | SubtitleSection | 50 |
| LogoEndcard (마지막 6초) | LogoEndcard | 100 |

> SubtitleSection이 zIndex 50이므로 항상 비주얼 위에 표시된다.

---

## 씬 하나가 완성되는 흐름

```
나레이션 "도파민은 보상을 기대할 때 분비된다"
    ↓
script_data: emotion="climax", SI=0.85, keywords=["도파민","보상"]
    ↓
Python 배경 (프레임마다):
  SineWave(intensity=0.55)  ← SI=0.85라 약해짐
  Particle(intensity=0.74)  ← SI^1.5=0.74, 강해짐
  TextData(intensity=1.10)  ← 항상 강함
  AsciiBackground(intensity=0.28)  ← 은은하게 유지
  → 합성 → frames/001234.png
    ↓
Remotion Vocab (씬 구간 동안):
  particle_birth  ← 클라이맥스 감정에 맞게 선택
  lissajous       ← 고주파 패턴 추가
    ↓
PostProcess (매 프레임):
  비트 플래시 발동 (킥 드럼 감지 순간)
  RMS 글로우 강함 (음악 에너지 높음)
  색수차 약간 (하이햇 중간)
    ↓
최종 프레임 완성
```
