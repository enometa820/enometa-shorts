# ENOMETA Audiovisual Art Reference

> 궁극적으로 지향하는 오디오비주얼 아트의 장르, 용어, 비주얼/사운드 특성, 도구, 레퍼런스 아티스트를 정리한 문서.

---

## 1. 장르 분류 & 용어 사전

### 핵심 장르

| 용어 | 정의 | ENOMETA 연관도 |
|------|------|----------------|
| **Data Art** | 데이터 자체를 시각/청각 소재로 변환하는 예술. 이케다가 대표 | ★★★★★ |
| **Audiovisual Art** | 사운드와 비주얼이 분리 불가능한 통합 예술 | ★★★★★ |
| **Generative Art** | 코드/알고리즘으로 생성되는 비주얼. 사람이 규칙을 설계하고 시스템이 결과를 만듦 | ★★★★★ |
| **Creative Coding** | 코딩 자체가 예술적 표현 수단. Processing, p5.js, py5 등 사용 | ★★★★☆ |
| **Glitch Art** | 디지털 오류/깨진 데이터의 미학을 의도적으로 활용 | ★★★☆☆ |
| **New Media Art** | 미술관/갤러리 맥락에서 디지털 기술 기반 예술을 분류하는 용어 | ★★★☆☆ |
| **Sound Art** | 소리 자체를 조형적 소재로 다루는 예술 | ★★★☆☆ |

### 관련 용어

| 용어                           | 설명                                                  |
| ---------------------------- | --------------------------------------------------- |
| **Datamatics**               | 이케다가 만든 프로젝트명이자 장르 용어. 데이터를 미학적으로 변환하는 행위 전체        |
| **Databending**              | 데이터를 의도적으로 왜곡해서 비주얼/사운드를 만드는 기법                     |
| **Datamoshing**              | 영상 압축 데이터를 조작해 프레임 간 글리치를 만드는 기법                    |
| **Terminal Aesthetic**       | 터미널/콘솔 화면 느낌의 모노스페이스 타이포 비주얼                        |
| **Microsound**               | 극도로 미세한 음향 입자를 다루는 전자음악 장르. 이케다의 음악 분류              |
| **Morphogenesis**            | 생물학적 형태 발생 과정을 시뮬레이션한 비주얼. 쿠퍼의 시그니처                 |
| **Sine Wave (사인파)**          | 가장 순수한 톤. 모든 소리의 기본 구성요소. 이케다의 핵심 소재                |
| **Difference Tone (차이음)**    | 두 주파수가 겹칠 때 발생하는 제3의 진동 (예: 449Hz + 442Hz → 7Hz 진동) |
| **OSC (Open Sound Control)** | 소프트웨어 간 실시간 데이터 통신 프로토콜. Python ↔ 비주얼 엔진 연결에 사용     |
| **MIDI**                     | 음악 장비/소프트웨어 간 연주 데이터 통신 규격                          |
| **BPM (Beats Per Minute)**   | 분당 비트 수. 음악 분석 및 비주얼 싱크의 기준 단위                      |
| **Onset Detection**          | 오디오에서 비트/공격음 시작점을 자동 감지하는 기술                        |
| **Particle System**          | 수천 개의 작은 입자를 생성/소멸시켜 유기적 비주얼을 만드는 기법                |
| **Perlin Noise**             | 자연스러운 무작위 패턴을 생성하는 알고리즘. 제너러티브 아트의 기본 도구            |
| **Shader (GLSL)**            | GPU에서 실행되는 그래픽 프로그램. 실시간 비주얼에 필수 (고급)               |

---

## 2. 레퍼런스 아티스트 비교

### Ryoji Ikeda (료지 이케다)

- **포지션**: Data Art + Sound Art + Minimal
- **배경**: 도쿄 클럽씬 DJ → 미니멀 테크노 → 데이터 아트
- **사운드 특성**: 사인파, 글리치 노이즈, 디지털 클릭, 초고주파 톤. 멜로디/화성 없음. 데이터의 순수한 물리적 체험 추구
- **비주얼 특성**: 흑백 모노크롬, 바코드 패턴, 바이너리(0/1), 초고속 프레임(초당 수백 프레임), 스트로브 플래시
- **작업 방식**: 커스텀 소프트웨어로 데이터를 실시간 변환. 텍스트/사운드/사진 → 바이너리 패턴 → 시청각 출력
- **핵심 프로젝트**: test pattern, Datamatics, spectra, superposition
- **ENOMETA에 가져올 것**: 미학적 레퍼런스 — 흑백 데이터 패턴, 미니멀리즘, 데이터 변환의 순수성

### Max Cooper (맥스 쿠퍼)

- **포지션**: Audiovisual Art + Electronica + Science Communication
- **배경**: 계산생물학 PhD (유전학 연구자) → 전자음악 프로듀서
- **사운드 특성**: 일렉트로니카/테크노/앰비언트. 멜로디, 하모니, 감정적 서사 존재. 과학적 개념을 감성으로 번역
- **비주얼 특성**: 풀 컬러, 유기적 형태, 모포제네시스, 프랙탈, 자연 시뮬레이션. 앨범마다 다른 비주얼 아티스트와 협업
- **작업 방식**: Ableton Live + Max for Live로 사운드 제작, MIDI로 Resolume VJ에 비주얼 트리거. 앨범 = 오디오비주얼 내러티브
- **핵심 프로젝트**: Emergence, Yearning for the Infinite, One Hundred Billion Sparks
- **ENOMETA에 가져올 것**: 워크플로우 & 방법론 — 내러티브 기반 구조, 데이터→감성 번역, 협업 모델, 도구 체인

### 비교 매트릭스

| 항목 | 이케다 | 쿠퍼 | ENOMETA 방향 |
|------|--------|------|-------------|
| 감정 | 배제 | 핵심 | **핵심** (철학적 각성 + 감정) |
| 색상 | 흑백 모노크롬 | 풀 컬러, 유기적 | **하이브리드** (모노크롬 베이스 + 포인트 컬러) |
| 비주얼 | 혼자 시스템 설계 | 아티스트 협업 | **Python 자체 생성** |
| 데이터 | 데이터 그 자체가 작품 | 데이터는 내러티브의 재료 | **대본(텍스트) → 데이터 → 비주얼** |
| 관객 경험 | 지각의 한계 테스트 | 감정적 몰입 | **철학적 사유 + 감정적 몰입** |
| 음악 | 사인파/노이즈 | 일렉트로니카/테크노 | **enometa** (대본 리액티브 댄스 뮤직) |
| 도구 | 커스텀 소프트웨어 | Ableton + Resolume | **Python 음악엔진 + Remotion** |
| 포맷 | 갤러리 설치작 | 라이브 쇼 + 앨범 | **쇼츠(1080x1920) + 유튜브** |

---

## 3. 비주얼 요소 레퍼런스

### 이케다 계열 (데이터/미니멀)

- 바코드 패턴 — 데이터를 흑백 수직선 패턴으로 변환
- 바이너리 그리드 — 0과 1의 매트릭스 배열
- 스캔라인 — 수평 주사선이 화면을 훑는 모션
- 스트로브/플리커 — 극도로 빠른 명멸 (주의: 광과민성 고려)
- 포인트 클라우드 — 데이터 좌표를 3D 점군으로 표현
- 파형 시각화 — 사운드 웨이브를 실시간 선형 그래프로 표시

### 쿠퍼 계열 (유기적/과학적)

- 모포제네시스 — 세포 분열/성장 시뮬레이션
- 프랙탈 — 자기유사성 패턴의 무한 줌
- 파티클 시스템 — 수천 개 입자의 군집 행동 (별똥별, 꽃잎, 먼지)
- 플로우 필드 — 벡터장을 따라 흐르는 선/입자
- Lissajous 곡선 — 두 사인파의 위상 차이로 생기는 기하학적 패턴
- 보로노이 다이어그램 — 공간 분할 패턴. 자연물(잎맥, 거북 등딱지) 닮음

### ENOMETA 구현 비주얼 시스템 (v11)

#### Python 렌더링 레이어 (1080×1080)

| 레이어 | 역할 | SI 반응 |
|--------|------|---------|
| SineWaveLayer | 사인파 간섭 패턴 (배경) | SI 낮을수록 강함 |
| WaveformLayer | 파형 시각화 | SI 비례 |
| ParticleLayer | 파티클 에너지 | SI^1.5 (민감) |
| TextDataLayer | 데이터 카드 | 0.70 + SI×0.30 |
| BarcodeLayer | 바이트 스트라이프 | 0.60 + SI×0.40 |
| DataStreamLayer | 데이터 스트림 | 0.50 + SI×0.50 |
| DataMatrixLayer | 매트릭스 패턴 | SI^0.8 |

#### Remotion 모션 컴포넌트

| 컴포넌트 | 역할 | 특징 |
|----------|------|------|
| ShapeMotion | 감정별 기하학 도형 | tension=회전사각형, climax=동심원, awakening=스캔라인 |
| TextReveal | 타이포그래피 (4모드) | typewriter/wave/glitch/scatter, 오디오 리액티브 |
| Lissajous | Lissajous 곡선 | Canvas 2D, rms→선굵기, bass→위상 |
| PixelGrid | 픽셀 그리드 | zIndex:5, 7가지 변형 (outline/life/rain/waveform 등) |
| PostProcess | 후처리 효과 | zIndex:10 |

#### 비주얼 어휘 (vocab) 23종

- **파티클** (7): birth, scatter, converge, orbit, escape, chain_awaken, split_ratio
- **타이포** (1): text_reveal (wave/glitch/scatter/typewriter)
- **그리드** (2): grid_morph, grid_mesh
- **네트워크** (1): neural_network
- **링** (1): loop_ring
- **프랙탈** (1): fractal_crack
- **데이터** (3): data_bar, data_ring, counter_up
- **파형** (3): waveform, waveform_spectrum, waveform_circular
- **색상** (5): color_shift, color_drain, color_bloom, color_shift_warm, color_shift_cold
- **조명** (2): brightness_pulse, light_source
- **픽셀** (7): pixel_grid, pixel_grid_outline, pixel_grid_life, pixel_grid_rain, pixel_waveform, pixel_waveform_steps, pixel_waveform_cascade

#### 감정 → 비주얼 매핑

- **tension** → 글리치/스트로브 + 회전사각형 + 빨강 계열
- **climax** → 파티클 폭발 + 동심원 + 초록 계열
- **awakening** → 스캔라인 + 시안 계열
- **intro** → 부유점 + 흰색 계열
- **buildup** → 삼각형 펄스 + flash

#### 팔레트 8종

`phantom` · `neon_noir` · `cold_steel` · `ember` · `synapse` · `gameboy` · `c64` · `enometa`

---

## 4. 사운드 특성 레퍼런스

### 이케다 사운드 팔레트

| 요소 | 설명 |
|------|------|
| 사인파 (Sine Wave) | 가장 순수한 톤. 주파수 간 간섭으로 차이음 생성 |
| 글리치/클릭 | 디지털 에러 사운드. 짧은 임펄스성 노이즈 |
| 화이트/핑크 노이즈 | 전 주파수 대역의 랜덤 신호 |
| 초고주파 톤 | 인간 지각 경계(18-20kHz) 부근의 소리 |
| 비트 패턴 | 드럼머신적 리듬이지만 정적 텍스처로 기능 |
| 무음/침묵 | 소리의 부재 자체를 소재로 활용 |

### ENOMETA 사운드 팔레트 (v11 구현)

| 요소 | 레이어 | 설명 |
|------|--------|------|
| 킥 드럼 | rhythm | 사인파 body(60Hz) + 어택 클릭. 16-step 패턴 10종 |
| 하이햇 | rhythm | 필터드 노이즈. 오픈/클로즈 변형 |
| 스네어 | rhythm | 톤 바디(200Hz) + 노이즈 테일 + 어택 클릭 (0.18초) |
| 쏘우파 시퀀스 | saw_sequence | 게이트 시퀀서. 메인 멜로디 역할. 레벨별 2~3 변형 |
| 아르페지오 | arpeggio | 고음역 반복 음형. 3음/4음/8음 비대칭 패턴 10종 |
| 딥 베이스 | bass | 사인파 기반 저음역 드론 |
| 서브 펄스 | sub_pulse | 서브 베이스 영역 펄스 |
| 사인파 간섭 | sine_interference | 두 주파수 간섭 — enometa 시그니처 텍스처 |
| 펄스 트레인 | pulse_train | 극초단 클릭 (데이터 음각) |
| 초고주파 | ultrahigh | 8~20kHz 텍스처 |
| 게이트 스터터 | gate_stutter | 리듬 게이팅 + 스터터 효과 |
| 갭 버스트 | gap_stutter_burst | 나레이션 공백에 임팩트 |

### 쿠퍼 사운드 팔레트

| 요소 | 설명 |
|------|------|
| 레이어드 신디사이저 | 여러 층의 패드/리드로 공간감 구축 |
| 아르페지오 | 반복적 음형이 점진적으로 변주 |
| 앰비언트 텍스처 | 긴 릴리스의 패드, 리버브 공간 |
| 4-on-the-floor 킥 | 클럽 테크노 기반의 추진력 있는 리듬 |
| 피아노/스트링 | 클래식 악기와 일렉트로닉의 융합 (Tom Hodge 협업) |
| 바이노럴/이머시브 오디오 | Dolby Atmos 3D 공간 음향 |

### ENOMETA 사운드 방향 (v11)

ENOMETA의 음악은 독자적인 장르 — **"대본 리액티브 댄스 뮤직"**. DAW 없이 Python(NumPy + SciPy)으로 직접 합성한다.

- **장르**: enometa (구 ikeda). Ryoji Ikeda "Matrix"를 미학적 레퍼런스로 하되, 리듬/멜로디를 추가한 독자 노선
- **엔진**: `enometa_music_engine.py` — 10레이어 연속 합성 (44100Hz)
- **리듬**: 드럼 패턴(킥/하이햇/스네어) 중심. 16-step × 10패턴 (four_on_floor, euclidean, offbeat 등)
- **멜로디**: 쏘우파 게이트 시퀀서 + 아르페지오 (레벨당 2~3 변형, 4바 로테이션)
- **텍스처**: 사인파 간섭 + 펄스 트레인(데이터 클릭) + 초고주파(8~20kHz) + gate_stutter
- **구조**: Song Arc(매크로) × SI 변조(미드) × 호흡 시스템(마이크로) — 3중 에너지 변조
- **BPM**: 기본 135 (±20%), 에피소드 해시 시드 기반 변동
- **특수 요소**: highlight_words → 킥+스네어 악센트, 나레이션 갭 → gap_burst 임팩트
- **마스터링**: EBU R128 -14 LUFS, narration 0.90 + BGM 1.0, 사이드체인 미사용

---

## 5. 도구 & 기술 스택

### 음악 생성 (Python 직접 합성)

| 도구 | 용도 | 비고 |
|------|------|------|
| **enometa_music_engine.py** | 10레이어 BGM 합성 (44100Hz) | DAW 없이 Python으로 직접 생성 |
| **NumPy** | 파형 합성, 수학적 패턴 생성 | 사인파, 쏘우파, 노이즈 합성 |
| **SciPy** | 오디오 필터링, WAV 출력 | 버터워스 필터, signal processing |
| **audio_mixer.py** | 나레이션 + BGM 믹싱 | ffmpeg 기반. loudnorm -14 LUFS |

### TTS (나레이션)

| 도구 | 용도 | 비고 |
|------|------|------|
| **Edge-TTS** | 대본 → 나레이션 WAV 생성 | `generate_voice_edge.py` 전용. 비용 0원 |

### 비주얼 생성 (Hybrid 파이프라인)

| 도구 | 용도 | 비고 |
|------|------|------|
| **visual_renderer.py** | 제너러티브 아트 프레임 렌더링 (1080×1080 PNG) | PIL + NumPy. 7레이어(음악 3 + TTS 4) |
| **visual_script_generator.py** | 대본 → 비주얼 스크립트 생성 | 감정/SI 기반 vocab 매핑. 23종 vocab |
| **script_data_extractor.py** | 대본 → semantic_intensity + 키워드 추출 | 씬별 SI값, highlight_words |
| **NumPy** | 수학적 패턴 생성, 오디오 데이터 처리 | 사인파, 노이즈, 파티클 궤적 |
| **Pillow (PIL)** | 프레임 이미지 생성/합성 | 레이어별 드로잉 + 알파 블렌딩 |

### 최종 컴포지션 (Remotion)

| 도구 | 용도 | 비고 |
|------|------|------|
| **Remotion** | 모션 그래픽, 타이포, 자막, 최종 합성 | React + TypeScript. 1080×1920 출력 |
| **@remotion/layout-utils** | fitText — 제목 fontSize 자동 조절 | 글자수 기반 최적 크기 |
| **Pretendard Variable** | 한글 폰트 | 자막 54~62px, 태그라인 48px |

### 자동화 파이프라인

| 도구 | 용도 | 비고 |
|------|------|------|
| **enometa_render.py** | 7단계 파이프라인 단일 명령 실행 | TTS→데이터→비주얼→BGM→믹스→프레임→렌더 |
| **ffmpeg** | 오디오 믹싱, loudnorm, 포맷 변환 | audio_mixer.py 내부 사용 |

### 향후 확장 가능

| 도구 | 용도 | 비고 |
|------|------|------|
| **TouchDesigner** | 실시간 인터랙티브 비주얼 | Python 연동 가능 (OSC/MIDI). 라이브 퍼포먼스 시 |
| **GLSL Shader** | GPU 기반 실시간 비주얼 | Remotion Three.js 연동 가능 |
| **@remotion/three** | 3D 비주얼 | Three.js + React Three Fiber |

---

## 6. ENOMETA 파이프라인 설계

단일 명령으로 전체 자동 실행: `py scripts/enometa_render.py <episode_dir> --title "제목" --palette phantom`

```
[1] TTS (Edge-TTS)
    │  generate_voice_edge.py → narration.wav
    ▼
[2] Script Data
    │  script_data_extractor.py → script_data.json
    │  (세그먼트별 semantic_intensity, 키워드, highlight_words)
    ▼
[3] Visual Script
    │  visual_script_generator.py → visual_script.json
    │  (씬별 감정 + vocab 매핑 + SI 기반 reactivity)
    ▼
[4] BGM
    │  enometa_music_engine.py → bgm.wav + bgm_raw_visual_data.npz
    │  (10레이어 합성 + SI 변조 + Song Arc + 드럼 패턴)
    ▼
[5] Audio Mix
    │  audio_mixer.py → mixed.wav
    │  (narration 0.90 + BGM 1.0, loudnorm -14 LUFS)
    ▼
[6] Python Frames
    │  visual_renderer.py → frames/*.png (1080×1080)
    │  (7레이어: SineWave/Waveform/Particle + TextData/Barcode/DataStream/DataMatrix)
    ▼
[7] Remotion Render
    │  React + TypeScript → output.mp4 (1080×1920)
    │  (Title + VisualSection + Subtitle + ShapeMotion + TextReveal + Endcard)
    ▼
[최종 출력] ── YouTube Shorts 1080×1920 세로 mp4
```

### 데이터 흐름

```
대본(텍스트)
  ├─→ script_data.json (SI값, 키워드, 감정)
  │     ├─→ visual_script.json (비주얼 결정)
  │     ├─→ BGM의 SI 변조 + highlight_words 악센트
  │     └─→ Remotion의 자막 싱크 + ShapeMotion 감정
  ├─→ narration.wav (Edge-TTS)
  └─→ bgm_raw_visual_data.npz (프레임별 RMS/bass/onset → Remotion 오디오 리액티브)
```

---

## 7. 레퍼런스 검색 키워드

비주얼 레퍼런스를 찾을 때 사용할 검색어 모음:

- `glitch art generative` — 글리치 + 제너러티브 스타일
- `data visualization art` — 데이터 아트 전반
- `creative coding p5.js` — 코드 기반 비주얼 레퍼런스
- `audiovisual performance` — 라이브 오디오비주얼 공연
- `generative particle system` — 파티클 기반 비주얼
- `terminal aesthetic design` — 터미널/해커 미학
- `Ryoji Ikeda test pattern` — 이케다 시그니처 스타일
- `Max Cooper emergence visual` — 쿠퍼 비주얼 레퍼런스
- `procedural animation python` — Python 기반 절차적 애니메이션
- `data sonification` — 데이터를 소리로 변환하는 기법

---

*최종 업데이트: 2026.03.04*
*ENOMETA — 존재와 사유, 그 경계를 초월하다*
