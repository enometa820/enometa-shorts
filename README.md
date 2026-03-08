# enometa-shorts

YouTube Shorts 자동 생성 파이프라인. 대본 한 편으로 TTS · BGM · 비주얼 · 영상 렌더링까지 완전 자동.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Node](https://img.shields.io/badge/Node-18+-green)
![Remotion](https://img.shields.io/badge/Remotion-4.0.431-red)
![License](https://img.shields.io/badge/License-Private-lightgrey)

---

## 파이프라인

```
script.txt
  │
  ├─ gen_timing.py          → narration_timing.json  (TTS 실측 기반 연속 배치)
  ├─ generate_voice_edge.py → narration.wav           (Edge-TTS ko-KR-SunHiNeural)
  ├─ script_data_extractor  → script_data.json        (kiwipiepy 형태소 분석 + SI 커브)
  ├─ enometa_music_engine   → bgm.wav + music_script  (numpy 합성, 10장르, Vertical Remixing)
  ├─ audio_mixer.py         → mixed.wav               (narration 0.90 + bgm 1.0, -14 LUFS)
  ├─ visual_script_gen      → visual_script.json      (씬/감정/vocab 매핑)
  ├─ visual_renderer.py     → frames/000000.png~      (1080×1080, numpy+Pillow)
  ├─ audio_analyzer.py      → audio_analysis.json     (RMS/onset/beat 분석)
  └─ Remotion (React)       → output.mp4              (1080×1920 YouTube Shorts)
```

---

## 비주얼 아키텍처 — 누가 뭘 그리나

> 📄 상세 문서: [docs/visual-architecture.md](docs/visual-architecture.md) — 레이어별 역할, SI 반응, 팔레트, 비주얼 장르/무드, PostProcess 효과 상세 설명

최종 영상(1080x1920)의 비주얼은 **Python + Remotion 두 엔진이 합성**한다:

```
 ┌─────────────────────────────────────────────────────────┐
 │                                                         │
 │   TitleSection  "우리의 뇌는 지금..."     ← Remotion    │
 │                                                         │
 ├─────────────────────────────────────────────────────────┤
 │                                                         │
 │   ╔═══════════════════════════════════╗                  │
 │   ║                                   ║                  │
 │   ║   Python 배경 PNG (1080x1080)     ║  ← numpy+Pillow │
 │   ║   10개 레이어 합성                ║    SineWave,     │
 │   ║   frames/000000.png~             ║    Particle,     │
 │   ║                                   ║    TextData,     │
 │   ╠═══════════════════════════════════╣    ASCII 등      │
 │   ║                                   ║                  │
 │   ║   Vocab 오버레이 (30종)           ║  ← Remotion     │
 │   ║   Lissajous, DataBar,            ║    오디오        │
 │   ║   ParticleBirth ...              ║    리액티브      │
 │   ║                                   ║                  │
 │   ╠═══════════════════════════════════╣                  │
 │   ║   PostProcess                     ║  ← Remotion     │
 │   ║   스캔라인 / 글리치               ║    항상 적용     │
 │   ╚═══════════════════════════════════╝                  │
 │                                                         │
 ├─────────────────────────────────────────────────────────┤
 │                                                         │
 │   SubtitleSection  "도파민은..."       ← Remotion       │
 │   나레이션 싱크 자막                                     │
 │                                                         │
 └─────────────────────────────────────────────────────────┘

                 마지막 6초 → LogoEndcard 로 전환
```

> **핵심**: Python이 배경을 그리고 → Remotion이 그 위에 애니메이션 + 자막을 겹친다.

### Python 배경 레이어 (scripts/visual_layers/)

배경 이미지를 구성하는 10개 레이어. `visual_renderer.py`가 장르별로 조합한다.

| 레이어 | 그리는 것 | 데이터 소스 |
|--------|-----------|-------------|
| TextDataLayer | 터미널 스타일 키워드 카드 (품사/바이트/해시) | script_data |
| BarcodeLayer | 토큰 UTF-8 → 수직 바코드 스트라이프 | script_data |
| DataStreamLayer | 수평 스크롤 데이터 텍스트 8~12줄 | script_data |
| DataMatrixLayer | 악기 에너지 매트릭스/그리드 (Ikeda 스타일) | music_script |
| SineWaveLayer | 사인파 배경 (SI 낮을수록 강함) | 내부 수학 |
| WaveformLayer | 오디오 파형 시각화 | audio RMS |
| ParticleLayer | 부유 파티클 시스템 | 내부 물리 |
| BytebeatLayer | bytebeat 공식 → 픽셀 | 내부 수학 |
| FeedbackLayer | 이전 프레임 피드백 루프 | 자기참조 |
| AsciiBackgroundLayer | SI 기반 ASCII 문자 텍스처 (12×12px 셀 그리드) | script_data + SI |

**장르별 레이어 조합** (`GENRE_LAYER_PRESETS`):

| visual genre | 음악 레이어 | TTS 레이어 | 특성 |
|-------------|------------|-----------|------|
| `enometa` | SineWave + Waveform + Particle | TextData + Barcode + DataStream + DataMatrix + AsciiBackground | 풀 세트 데이터아트 |
| `cooper` | SineWave + Particle | DataStream + AsciiBackground | 미니멀 유기적 |
| `abstract` | SineWave | DataMatrix + AsciiBackground | 정제된 기하 |
| `data` | Waveform + SineWave | TextData + Barcode + DataStream + DataMatrix + AsciiBackground | 최고 밀도 |

### Remotion Vocab 컴포넌트 (src/components/vocab/)

`visual_script.json`의 vocab 문자열 → `VOCAB_MAP` → React 컴포넌트. 모두 오디오 리액티브 (bass/mid/high/rms/onset).

| 카테고리 | vocab 문자열 | 컴포넌트 | 설명 |
|---------|-------------|---------|------|
| **파티클** | `particle_birth` `_scatter` `_converge` `_orbit` `_escape` `_chain_awaken` `_split_ratio` | ParticleBirth 외 6종 | 파티클 생명 주기 |
| **흐름/색** | `flow_field_calm` `_turbulent` `color_shift` `_warm` `_cold` `_drain` `_bloom` `brightness_pulse` `light_source` | FlowField, ColorShift, BrightnessPulse, LightSource | 유동장 + 색상 변조 |
| **데이터** | `counter_up` `neural_network` `loop_ring` `fractal_crack` `data_bar` `data_ring` `grid_morph` `grid_mesh` | CounterUp, NeuralNetwork, LoopRing, FractalCrack, DataBar, GridMorph | 데이터 시각화 |
| **파형** | `waveform` `_spectrum` `_circular` `lissajous` `_complex` | WaveformVisualizer, Lissajous | 수학적 곡선 |
| **텍스트** | `text_reveal` `_wave` `_glitch` `_scatter` | TextReveal | 4모드 타이포그래피 |
| **심볼** | `symbol_morph` | SymbolMotion | 품사→추상도형 (noun→육각형, verb→화살표) |
| **ASCII** | `ascii_block` `_shape` `_matrix` | AsciiArt | 비트맵 블록 / 품사 패턴 / 터미널 스트림 |
| **레트로** | `pixel_grid` `_outline` `_life` `_rain` `pixel_waveform` `_steps` `_cascade` | PixelGrid, PixelWaveform | 8bit 레트로 |
| **3D** | `terra_globe` `_data` `terra_flythrough` `_tunnel` `_terrain` `_terrain_bars` | TerraGlobe, TerraFlythrough, TerraTerrain | @remotion/three 3D (씬당 최대 1개) |
| **자동** | `post_process` | PostProcess | 항상 렌더링 (vocab에 추가 불필요) |

### 합성 흐름

```
visual_script.json
  └── scenes[0].layers.semantic = [
        { vocab: "lissajous", ... },     VOCAB_MAP["lissajous"]  →  <Lissajous>
        { vocab: "data_bar",  ... }      VOCAB_MAP["data_bar"]   →  <DataBar>
      ]

최종 화면 (1080×1920):
  ┌──────────────────┐
  │   TitleSection   │  ← 제목 (fitText 자동 조절)
  ├──────────────────┤
  │  Python 배경 PNG │  ← 1080×1080 정사각
  │  + Vocab 오버레이│  ← React 컴포넌트
  │  + PostProcess   │  ← 스캔라인/글리치
  ├──────────────────┤
  │  SubtitleSection │  ← 나레이션 싱크 자막
  └──────────────────┘
  (마지막 6초: LogoEndcard)
```

---

## Claude 개입 지점 (3-Gate 시스템)

파이프라인은 자동이지만, Claude가 **4개 지점**에서 개입하여 다양성과 품질을 보장한다.

```
대본 작성 (enometa-writing 스킬)
  │
  ├─ Gate 0: 주제 선택
  │    "글쓰기 시작하자" → 5대 도메인 교차점에서 3~5개 주제 추천
  │    사용자가 선택 → 대본 작성 → 컨펌
  │
  └─ publish.md 생성 → enometa-produce 스킬 자동 invoke
       │
       ├─ Gate 1: 비주얼 다양성 개입 (visual_script 생성 후)
       │    - 이전 EP와 vocab 중복 검사
       │    - ascii_block에 맥락 맞는 ascii_text 영어 삽입
       │    - 필요 시 vocab 교체/추가
       │
       ├─ Gate 2: seq_config 음색 설계 (music_script 생성 후)
       │    - 이전 EP와 seq_config 비교 (BPM/킥/필터/코러스 등)
       │    - mood_layers는 편집하지 않음 (장르 정체성)
       │    - seq_config 파라미터만 조정하여 음색 차별화
       │
       └─ Gate 3: BGM 청취 확인
            - 사용자가 bgm.wav 듣고 OK → 나머지 자동 진행
            - (mix → audio_analysis → python_frames → render)
```

**핵심**: Gate 1~2는 Claude가 자동 개입. Gate 0/3은 사용자 승인 필요.

---

## 옵션 레퍼런스

### 팔레트 (`--palette`)

| 값 | 분위기 | accent | 특성 |
|----|--------|--------|------|
| `phantom` | 보라/청색 (기본) | 보라 | 몽환적 |
| `neon_noir` | 네온 누아르 | 민트 | 사이버펑크 |
| `cold_steel` | 차가운 철색 | 슬레이트 | 무채색 금속 |
| `ember` | 붉은 불꽃 | 오렌지 | 따뜻한 에너지 |
| `synapse` | 신경망 청록 | 에메랄드 | 생명/과학 |
| `gameboy` | 게임보이 그린 | GB 라임 | 8bit 레트로 |
| `c64` | Commodore 64 | 연보라 | 홈컴퓨터 레트로 |
| `enometa` | 흑백 모노크롬 | 순수 흰색 | 미니멀 |

### 음악 장르 (`--music-mood`) — v20

| 값 | 레퍼런스 | BPM | 핵심 악기 |
|----|----------|-----|-----------|
| `acid` | Phuture, DJ Pierre | 126–138 | TB-303 acid bass |
| `ambient` | Brian Eno | 60–72 | 공간감, 리버브 |
| `microsound` | Ryoji Ikeda, Alva Noto | 85–100 | 정밀 펄스, 초단파 클릭 |
| `IDM` | Aphex Twin, Autechre | 100–155 | 비정형 폴리리듬 |
| `minimal` | Robert Hood, Richie Hawtin | 124–132 | 절제된 텍스처 |
| `dub` | Basic Channel | 110–125 | tape delay, chord stab |
| `glitch` | Oval, Farmers Manual | 92–108 | E(5,16), 비트크러시 |
| `industrial` | Perc, Ansome | 138–155 | 왜곡 킥, 고에너지 |
| `techno` | Jeff Mills, UR | 128–138 | 4-on-the-floor |
| `house` | Larry Heard | 118–126 | Rhodes 패드(minor 9), 오프비트 하이햇 |

### 비주얼 무드 (`--visual-mood`)

`--visual-mood` 생략 시 `--music-mood`에서 자동 결정:

| music-mood | → visual genre |
|------------|----------------|
| `ambient` / `microsound` / `dub` / `house` | `cooper` |
| `IDM` / `minimal` | `abstract` |
| `techno` / `industrial` | `data` |
| `acid` / `glitch` | `enometa` |

### seq_config 파라미터 (ep_seed 자동 파생)

`music_script.json`의 `metadata.seq_config`에 저장. 에피소드마다 ep_seed에서 자동 결정.

| 파라미터 | 범위 | 영향 |
|---------|------|------|
| `drum_seq_type` | 0–2 | Thue-Morse / Norgard / Rudin-Shapiro 수열 선택 |
| `drum_rotation` | 0–7 | 드럼 패턴 회전 |
| `pitch_rotation` | 0–7 | 음정 패턴 회전 |
| `pitch_length` | 3–6 | 음정 시퀀스 길이 |
| `bpm` | 장르 범위 | 장르별 고정 범위 내 결정 |
| `saw_harmonics` | {1: 1.0, ...} | 톱니파 배음 구성 (음색 결정) |
| `filter_cutoff_base` | 800–4000 Hz | LP 필터 컷오프 기본값 |
| `chorus_depth_ms` | 1.5–5.0 | 코러스 딜레이 깊이 |
| `fm_mod_ratio` | 1.5–3.5 | FM 베이스 변조 비율 |
| `bass_detune` | 0.001–0.008 | 드론 베이스 디튜닝 |
| `kick_character` | 0/1/2 | tight / boomy / punchy |
| `arp_pattern` | [배수 배열] | 아르페지오 음정 패턴 |
| `arp_division` | 3–6 | 아르페지오 박자 분할 |
| `melody_scale_offset` | 0–6 | 사인 멜로디 스케일 시작 음계 회전 |
| `melody_beat_base` | 2.0–8.0 Hz | 사인 간섭 맥놀이 기본 주파수 |
| `melody_norgard_offset` | 0–15 | Norgard 수열 시작점 오프셋 (피치 모듈레이션) |

### 다양성 시스템 (Vertical Remixing)

에피소드마다 음악과 비주얼이 자동으로 달라지는 3축 구조:

| 축 | 결정 요소 | 결과 |
|----|-----------|------|
| **음색** | `ep_seed` → `seq_config` (13개 파라미터) | 드럼 패턴, 배음, 필터, 코러스, 킥 등 에피소드마다 고유 |
| **레이어 조합** | `_GENRE_SPECS`의 required + optional풀 | 같은 장르라도 ep_seed로 다른 레이어 ON/OFF + 볼륨 |
| **비주얼 전략** | genre → strategy 동적 매핑 + SI 승격 | SI ≥ 0.80이면 전략 한 단계 상향 (밀도 증가) |

### 드럼 모드 (`--drum-mode`)

| 값 | 동작 |
|----|------|
| `default` | 무드 기본값 따름 (기본) |
| `on` | 풀 드럼 강제 ON |
| `off` | 드럼 강제 OFF |
| `simple` | 4-on-the-floor 킥 + 8분 하이햇 + 스네어 2,4박, 필인 없음 |
| `dynamic` | 풀 드럼 + SI 최대 + 필인 2배 (4/8바 주기) |

### 특정 단계만 재실행 (`--step --force`)

```bash
py scripts/enometa_render.py episodes/ep010 --title "제목" --step bgm --force
```

| step 값 | 실행 범위 |
|---------|-----------|
| `tts` | TTS 생성 |
| `bgm` | BGM 합성 |
| `mix` | 오디오 믹싱 |
| `visual` | 비주얼 스크립트 + 프레임 렌더 |
| `render` | Remotion 최종 렌더 |

---

## 빠른 시작

### 1. 사전 조건

```bash
# Python 의존성
pip install numpy scipy Pillow edge-tts kiwipiepy soynlp

# Node 의존성
npm install

# 환경 확인 (python이 아닌 py 사용 — Windows Store alias 문제)
py --version
node --version
```

### 2. 에피소드 폴더 생성

```
episodes/
└── ep013/
    └── script.txt   # 대본 파일 (빈 줄로 문단 구분)
```

### 3. 전체 파이프라인 실행

```bash
py scripts/enometa_render.py episodes/ep013 --title "제목" --palette phantom --music-mood acid
```

### 4. Remotion 프리뷰

```bash
npx remotion studio --port 3000
```

---

## 프로젝트 구조

```
enometa-shorts/
├── scripts/
│   ├── enometa_render.py          # 전체 파이프라인 진입점
│   ├── enometa_music_engine.py    # BGM 합성 (10장르, 13+레이어, ~5000줄)
│   ├── visual_script_generator.py # 대본 → 씬/감정/vocab 매핑
│   ├── visual_renderer.py         # numpy+Pillow 프레임 렌더링
│   ├── visual_strategies.py       # 비주얼 전략 6종 프리셋
│   ├── gen_timing.py              # TTS 실측 기반 타이밍 생성
│   ├── generate_voice_edge.py     # Edge-TTS 나레이션 생성
│   ├── script_data_extractor.py   # 형태소 분석 + SI 커브 추출
│   ├── audio_mixer.py             # narration + bgm 믹싱
│   ├── audio_analyzer.py          # RMS/onset/beat 분석
│   ├── sequence_generators.py     # Thue-Morse / Norgard / Rudin-Shapiro 수열
│   └── visual_layers/             # Python 배경 레이어 10종 (위 표 참조)
├── src/
│   ├── Root.tsx                   # Remotion Composition 정의
│   ├── EnometaShorts.tsx          # 메인 레이아웃 컴포넌트
│   ├── components/
│   │   ├── VisualSection.tsx      # Python 프레임 + vocab 오버레이 합성
│   │   ├── SubtitleSection.tsx    # 나레이션 싱크 자막
│   │   ├── TitleSection.tsx       # 제목 (fitText 자동 조절)
│   │   ├── ShapeMotion.tsx        # emotion별 기하 도형
│   │   ├── LogoEndcard.tsx        # 엔드카드 (파티클 수렴 애니메이션)
│   │   └── vocab/                 # Vocab 컴포넌트 30종 (위 표 참조)
│   │       └── three/             # 3D Three.js vocab (Terra 계열)
│   └── utils/palettes.ts          # 팔레트 8종 색상 정의
├── episodes/ep001~ep012/          # 에피소드별 산출물
├── public/                        # Remotion 정적 에셋 (mixed.wav 등)
├── docs/
│   ├── CHANGELOG.md
│   └── decisions/                 # 아키텍처 결정 기록 (ADR)
└── CLAUDE.md                      # AI 협업 가이드
```

---

## 스택

| 역할 | 기술 |
|------|------|
| 영상 합성 | [Remotion](https://remotion.dev) (React) + [@remotion/three](https://www.remotion.dev/docs/three) (3D) |
| TTS | Edge-TTS `ko-KR-SunHiNeural` |
| BGM | Python (numpy) 직접 합성 |
| 비주얼 프레임 | Python (numpy + Pillow) |
| 형태소 분석 | [kiwipiepy](https://github.com/bab2min/kiwipiepy) |
| 오디오 믹싱 | FFmpeg (EBU R128 `-14 LUFS`) |

---

## 오디오 경로 주의

Remotion은 `public/epXXX/mixed.wav`를 참조한다.
`episodes/epXXX/mixed.wav`와 **별개의 파일**이므로, 수동 재믹스 시 반드시 동기화 필요.
(`enometa_render.py`는 자동 처리)

---

## 아키텍처 결정 (ADR)

주요 기술 선택의 이유는 [`docs/decisions/`](docs/decisions/) 에 기록되어 있다.

| 번호 | 결정 |
|------|------|
| [001](docs/decisions/001-kiwipiepy-vs-konlpy.md) | 형태소 분석: kiwipiepy 선택 |
| [002](docs/decisions/002-edge-tts-vs-chatterbox.md) | TTS: Edge-TTS 선택 |
| [003](docs/decisions/003-hybrid-render.md) | 비주얼: 하이브리드 렌더 |
| [004](docs/decisions/004-fixed-volume-no-cr.md) | 볼륨 고정 + 콜앤리스폰스 제거 |
| [005](docs/decisions/005-music-engine-monolith.md) | 음악 엔진 모놀리스 유지 |
| [006](docs/decisions/006-genre-rename-v18.md) | 프로토타입 무드 → 실존 언더그라운드 장르 리네이밍 |

---

## 변경 이력

[docs/CHANGELOG.md](docs/CHANGELOG.md)

---

## 참조 문서

| 문서 | 내용 |
|------|------|
| [docs/visual-architecture.md](docs/visual-architecture.md) | 비주얼 3파트 상세 — Python 배경 레이어, Vocab 30종, PostProcess 5효과, 팔레트, 비주얼 장르/무드, 감정 색상 |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | 버전별 변경 이력 |
| [docs/decisions/](docs/decisions/) | 아키텍처 결정 기록 (ADR) |
