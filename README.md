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
  ├─ script_data_extractor  → script_data.json        (kiwipiepy 형태소 분석 + soynlp 전처리 + SI 커브)
  ├─ enometa_music_engine   → bgm.wav                 (numpy 직접 합성, 9장르(v18), 10레이어)
  ├─ audio_mixer.py         → mixed.wav               (narration 0.90 + bgm 1.0, -14 LUFS)
  ├─ visual_script_gen      → visual_script.json      (씬/감정/vocab 매핑)
  ├─ visual_renderer.py     → frames/000000.png~      (1080×1080, numpy+Pillow)
  ├─ audio_analyzer.py      → audio_analysis.json     (RMS/onset/beat 분석)
  └─ Remotion (React)       → output.mp4              (1080×1920 YouTube Shorts)
```

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
└── ep010/
    └── script.txt   # 대본 파일 (빈 줄로 문단 구분)
```

### 3. 전체 파이프라인 실행

```bash
py scripts/enometa_render.py episodes/ep010 --title "제목" --palette phantom --music-mood acid
```

### 4. Remotion 프리뷰

```bash
npx remotion studio --port 3000
```

---

## 옵션 레퍼런스

### 팔레트 (`--palette`)

| 값 | 분위기 |
|----|--------|
| `phantom` | 어두운 보라/청색 (기본) |
| `neon_noir` | 네온 누아르 |
| `cold_steel` | 차가운 철색 |
| `ember` | 붉은 불꽃 |
| `synapse` | 신경망 청록 |
| `gameboy` | 게임보이 그린 |
| `c64` | Commodore 64 |
| `enometa` | 흑백 모노크롬 |

### 음악 장르 (`--music-mood`) — v18

| 값 | 레퍼런스 | 특성 |
|----|----------|------|
| `acid` | Phuture, DJ Pierre | TB-303 acid bass, BPM 126–138 (기본) |
| `ambient` | Brian Eno | 공간감, 리버브 중심, BPM 72–88 |
| `microsound` | Ryoji Ikeda, Alva Noto | 정밀 펄스, 초단파 클릭, BPM 80–96 |
| `IDM` | Aphex Twin, Autechre | 비정형 리듬, 폴리리듬, BPM 100–155 |
| `minimal` | Robert Hood, Richie Hawtin | 극도로 절제된 텍스처, BPM 124–132 |
| `dub` | Basic Channel, Rhythm & Sound | tape delay, 보이드 킥, BPM 110–125 |
| `glitch` | Oval, Farmers Manual | Euclidean E(5,16) 패턴, 비트크러시, BPM 92–108 |
| `industrial` | Perc, Ansome, Surgeon | 왜곡 킥, 고에너지, BPM 138–155 |
| `techno` | Jeff Mills, Underground Resistance | 4-on-the-floor, TB-303 arp, BPM 128–138 |

### 비주얼 무드 (`--visual-mood`)

Python 배경 프레임과 Remotion vocab 레이어를 동시에 제어한다.

| 값 | Python 레이어 | Remotion vocab | 팔레트 |
|----|--------------|----------------|--------|
| `ikeda` (기본) | TextData + Barcode + DataStream + DataMatrix | 데이터아트 | 에피소드 선택 |
| `cooper` | Particle + DataStream | 유기적 파형 | phantom |
| `abstract` | DataMatrix 단일 | 기하 추상 | synapse |
| `data` | TextData + Barcode + DataStream + DataMatrix (최대) | 시각화 데이터 스트림 | cold_steel |

### 드럼 모드 (`--drum-mode`)

| 값 | 동작 |
|----|------|
| `default` | 무드 기본값 따름 (기본) |
| `on` | 풀 드럼 강제 ON |
| `off` | 드럼 강제 OFF |
| `simple` | 킥+하이햇만, 필인 최소 (32바마다 1회) |
| `dynamic` | 풀 드럼+SI 최대+필인 2배 (4/8바 주기) |

```bash
py scripts/enometa_render.py episodes/ep010 --title "제목" --drum-mode simple
```

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

## 스택

| 역할 | 기술 |
|------|------|
| 영상 합성 | [Remotion](https://remotion.dev) (React) |
| TTS | Edge-TTS `ko-KR-SunHiNeural` |
| BGM | Python (numpy) 직접 합성 |
| 비주얼 프레임 | Python (numpy + Pillow) |
| 오디오 분석 | Python (librosa-free, scipy) |
| 형태소 분석 | [kiwipiepy](https://github.com/bab2min/kiwipiepy) |
| 오디오 믹싱 | FFmpeg (EBU R128 `-14 LUFS`) |

---

## 프로젝트 구조

```
enometa-shorts/
├── scripts/
│   ├── enometa_render.py          # 전체 파이프라인 진입점
│   ├── enometa_music_engine.py    # BGM 합성 (9장르(v18), 10레이어, ~5000줄)
│   ├── visual_script_generator.py # 대본 → 씬/감정/vocab 매핑
│   ├── visual_renderer.py         # numpy+Pillow 프레임 렌더링
│   ├── gen_timing.py              # TTS 실측 기반 타이밍 생성
│   ├── generate_voice_edge.py     # Edge-TTS 나레이션 생성
│   ├── script_data_extractor.py   # 형태소 분석 + SI 커브 추출
│   ├── audio_mixer.py             # narration + bgm 믹싱
│   ├── audio_analyzer.py          # RMS/onset/beat 분석
│   └── sequence_generators.py     # Thue-Morse / Norgard / Rudin-Shapiro 수열
├── src/
│   ├── Root.tsx                   # Remotion Composition 정의
│   ├── EnometaShorts.tsx          # 메인 컴포넌트
│   ├── components/
│   │   ├── VisualSection.tsx      # Python 프레임 + vocab 오버레이
│   │   ├── SubtitleSection.tsx    # 나레이션 싱크 자막
│   │   ├── TextReveal.tsx         # 4모드 타이포그래픽 모션
│   │   ├── LogoEndcard.tsx        # 엔드카드 애니메이션
│   │   ├── TitleSection.tsx       # 제목 (fitText 자동 조절)
│   │   └── ShapeMotion.tsx        # emotion별 기하 도형
│   └── utils/
│       └── palettes.ts            # 팔레트 정의
├── episodes/
│   └── ep001~ep009/               # 에피소드별 산출물
├── public/                        # Remotion 정적 에셋 (mixed.wav 등)
├── docs/
│   ├── CHANGELOG.md               # 변경 이력
│   ├── dev-concepts.md            # 개발 개념 사전
│   └── decisions/                 # 아키텍처 결정 기록 (ADR)
│       ├── 001-kiwipiepy-vs-konlpy.md
│       ├── 002-edge-tts-vs-chatterbox.md
│       ├── 003-hybrid-render.md
│       ├── 004-fixed-volume-no-cr.md
│       ├── 005-music-engine-monolith.md
│       └── 006-genre-rename-v18.md
└── CLAUDE.md                      # AI 협업 가이드 (파이프라인 전체 규칙)
```

---

## 코드 파일 가이드

각 파일이 무슨 일을 하는지 한 줄 설명 + 링크.

### Python 스크립트 (scripts/)

| 파일 | 역할 |
|------|------|
| [enometa_render.py](scripts/enometa_render.py) | **파이프라인 진입점** — 아래 모든 단계를 순서대로 자동 실행 |
| [gen_timing.py](scripts/gen_timing.py) | 대본 문장 → TTS 실측 길이 기반 타이밍 배치 → `narration_timing.json` |
| [generate_voice_edge.py](scripts/generate_voice_edge.py) | `narration_timing.json` → Edge-TTS 음성 합성 → `narration.wav` |
| [script_data_extractor.py](scripts/script_data_extractor.py) | 대본 형태소 분석(kiwipiepy) + 문장별 감정 강도(SI) 계산 → `script_data.json` |
| [enometa_music_engine.py](scripts/enometa_music_engine.py) | **BGM 합성** — numpy로 직접 음파 생성 (9장르, 10레이어, ~5000줄) → `bgm.wav` |
| [audio_mixer.py](scripts/audio_mixer.py) | `narration.wav` + `bgm.wav` → FFmpeg 믹싱 + -14 LUFS 정규화 → `mixed.wav` |
| [visual_script_generator.py](scripts/visual_script_generator.py) | `script_data.json` → 씬/감정/vocab 선택 → `visual_script.json` |
| [visual_strategies.py](scripts/visual_strategies.py) | 비주얼 전략 6종 프리셋 정의 (dense/breathing/cinematic 등) — visual_script_generator가 참조 |
| [visual_renderer.py](scripts/visual_renderer.py) | `visual_script.json` → Python(Pillow)으로 배경 프레임 이미지 생성 → `frames/` |
| [audio_analyzer.py](scripts/audio_analyzer.py) | `mixed.wav` → 프레임별 bass/mid/high/rms/onset 분석 → `audio_analysis.json` |
| [sequence_generators.py](scripts/sequence_generators.py) | 음악 패턴용 수열 생성 (Thue-Morse, Norgard, Rudin-Shapiro) |

### Remotion / React (src/)

| 파일 | 역할 |
|------|------|
| [src/Root.tsx](src/Root.tsx) | 모든 에피소드 Composition 등록 + calcMeta (영상 길이 자동 계산) |
| [src/EnometaShorts.tsx](src/EnometaShorts.tsx) | **메인 레이아웃** — TitleSection / VisualSection / SubtitleSection / LogoEndcard 조합 |
| [src/types.ts](src/types.ts) | 전체 TypeScript 타입 정의 (Scene, VisualScript, VocabEntry, VocabComponentProps 등) |
| [src/hooks/useAudioData.ts](src/hooks/useAudioData.ts) | `audio_analysis.json` → 현재 프레임의 `AudioFrame`(bass/mid/high/rms/onset) 반환 |
| [src/ep001Script.ts](src/ep001Script.ts) | EP001 데이터 모듈 — json 파일 import + 타입 캐스팅 export (EP002~010도 동일 패턴) |
| [src/components/VisualSection.tsx](src/components/VisualSection.tsx) | Python 배경 프레임 + vocab 컴포넌트 오버레이 — `VOCAB_MAP`으로 문자열→컴포넌트 변환 |
| [src/components/SubtitleSection.tsx](src/components/SubtitleSection.tsx) | `narration_timing` 기반 자막 싱크 표시 (EP005 레퍼런스 유지) |
| [src/components/TitleSection.tsx](src/components/TitleSection.tsx) | 제목 표시 — `fitText`로 글자 수에 따라 fontSize 자동 조절 (최대 72px) |
| [src/components/ShapeMotion.tsx](src/components/ShapeMotion.tsx) | emotion별 기하 도형 애니메이션 (tension/climax/awakening/intro/buildup) |
| [src/components/LogoEndcard.tsx](src/components/LogoEndcard.tsx) | 영상 마지막 엔드카드 (로고 + 태그라인 + 파티클 180개) |
| [src/components/vocab/TextReveal.tsx](src/components/vocab/TextReveal.tsx) | 타이포그래피 모션 4종 (typewriter/wave/glitch/scatter) |
| [src/components/vocab/DataBar.tsx](src/components/vocab/DataBar.tsx) | 오디오 리액티브 수직 바 차트 (`data_bar` / `data_ring`) |
| [src/components/vocab/Lissajous.tsx](src/components/vocab/Lissajous.tsx) | 리사주 곡선 (수학 패턴, bass→위상/rms→선굵기/onset→교차점) |
| [src/components/vocab/PixelGrid.tsx](src/components/vocab/PixelGrid.tsx) | 8bit 레트로 픽셀 그리드 (life/rain/outline 변형) |
| [src/components/vocab/NeuralNetwork.tsx](src/components/vocab/NeuralNetwork.tsx) | 신경망 노드-엣지 애니메이션 |
| [src/components/vocab/FlowField.tsx](src/components/vocab/FlowField.tsx) | 유동장 파티클 (`flow_field_calm` / `flow_field_turbulent`) |
| [src/components/vocab/ParticleBirth.tsx](src/components/vocab/ParticleBirth.tsx) | 파티클 탄생 — scatter/converge/orbit/escape/chain/split 등 6종 변형도 동일 폴더 |
| [src/utils/palettes.ts](src/utils/palettes.ts) | 팔레트 8종 색상 정의 |

### Vocab이란?

**vocab** = 씬마다 화면에 그려지는 시각 어휘. `visual_script.json`의 `scenes[].layers.semantic[]`에 문자열로 지정되면 [VisualSection.tsx](src/components/VisualSection.tsx)의 `VOCAB_MAP`이 해당 React 컴포넌트를 찾아 렌더링한다.

```
visual_script.json                VisualSection.tsx           화면
scenes[0].layers.semantic = [     VOCAB_MAP["lissajous"]  →  <Lissajous>
  { vocab: "lissajous", ... },    VOCAB_MAP["data_bar"]   →  <DataBar>
  { vocab: "data_bar",  ... }
]
```

오디오 반응형 — 모든 vocab 컴포넌트는 `AudioFrame(bass/mid/high/rms/onset)`을 받아 실시간 움직임에 반영한다.

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

## 오디오 경로 주의

Remotion은 `public/epXXX/mixed.wav`를 참조한다.
`episodes/epXXX/mixed.wav`와 **별개의 파일**이므로, 수동 재믹스 시 반드시 동기화 필요.

```bash
# 수동 동기화 (enometa_render.py는 자동 처리)
copy episodes\ep010\mixed.wav public\ep010\mixed.wav
```

---

## 변경 이력

[docs/CHANGELOG.md](docs/CHANGELOG.md)
