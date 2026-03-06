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
  ├─ enometa_music_engine   → bgm.wav                 (numpy 직접 합성, 9무드, 10레이어)
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
pip install numpy scipy Pillow edge-tts kiwipiepy

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
py scripts/enometa_render.py episodes/ep010 --title "제목" --palette phantom --music-mood raw
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

### 음악 무드 (`--music-mood`)

| 값 | 특성 |
|----|------|
| `raw` | 거친 전자음, 하이패스 노이즈 (기본) |
| `ambient` | 공간감, 리버브 중심 |
| `ikeda` | 정밀 펄스, Ryoji Ikeda 레퍼런스 |
| `experimental` | 비정형 리듬, 글리치 |
| `minimal` | 극도로 절제된 텍스처 |
| `chill` | 느린 템포, 부드러운 패드 |
| `glitch` | 비트 크러시, 노이즈 버스트 |
| `intense` | 고에너지, 빠른 BPM |
| `techno` | 4-on-the-floor, TB-303 arp |

### 비주얼 무드 (`--visual-mood`)

| 값 | 특성 |
|----|------|
| `ikeda` | 데이터아트 격자 (기본) |
| `cooper` | 유기적 파형 |
| `abstract` | 기하 추상 |
| `data` | 시각화 데이터 스트림 |

### 드럼 (`--drum`)

드럼을 강제로 ON / OFF 할 수 있다. 기본값은 무드 자동 결정.

```bash
py scripts/enometa_render.py episodes/ep010 --title "제목" --drum on   # 강제 ON
py scripts/enometa_render.py episodes/ep010 --title "제목" --drum off  # 강제 OFF
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
│   ├── enometa_music_engine.py    # BGM 합성 (9무드, 10레이어, ~5000줄)
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
│       └── 005-music-engine-monolith.md
└── CLAUDE.md                      # AI 협업 가이드 (파이프라인 전체 규칙)
```

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
