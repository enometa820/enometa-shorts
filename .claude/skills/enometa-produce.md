---
name: enometa-produce
description: >
  ENOMETA 에피소드 제작 파이프라인 실행 스킬.
  대본 컨펌 후 대화로 옵션 수집 → enometa_render.py 비인터랙티브 단일 명령 실행.
  트리거 키워드 - 제작 시작, 파이프라인, 영상 만들자, produce, 에피소드 제작
---

# ENOMETA Episode Production Pipeline

## 전제 조건
- ★ 대본이 **컨펌 완료** 상태여야 함 (글 컨펌 게이트 통과)
- ★ 제목이 **확정** 상태여야 함
- 에피소드 폴더 준비: `episodes/epXXX/`
- 필수 입력 파일: `episodes/epXXX/script.txt` (대본 원문)

## 표준 실행 — 대화로 옵션 수집

Claude가 아래 순서로 **모든 옵션을 표 형태로 전부 보여주고** 사용자 선택을 받는다.
일부만 추천하거나 생략하지 말 것 — 반드시 전체 테이블을 출력한다.

### 1. 팔레트 (필수)
| # | 값 | 분위기 |
|---|-----|--------|
| 1 | `phantom` | 어두운 보라/청색 (기본) |
| 2 | `neon_noir` | 핑크/붉은 네온 |
| 3 | `cold_steel` | 차가운 청록 |
| 4 | `ember` | 붉은/주황 불꽃 |
| 5 | `synapse` | 파란/신경망 |
| 6 | `gameboy` | 8비트 초록 |
| 7 | `c64` | 레트로 보라 |
| 8 | `enometa` | 흑백 모노크롬 |

### 2. 음악 장르 (필수)
| # | 값 | 레퍼런스 | BPM |
|---|-----|----------|-----|
| 1 | `acid` | Phuture, DJ Pierre | 126–138 (기본) |
| 2 | `ambient` | Brian Eno | 60–72 |
| 3 | `microsound` | Ryoji Ikeda, Alva Noto | 85–100 |
| 4 | `IDM` | Aphex Twin, Autechre | 100–155 |
| 5 | `minimal` | Robert Hood, Richie Hawtin | 124–132 |
| 6 | `dub` | Basic Channel, Rhythm & Sound | 110–125 |
| 7 | `glitch` | Oval, Farmers Manual | 92–108 |
| 8 | `industrial` | Perc, Ansome, Surgeon | 138–155 |
| 9 | `techno` | Jeff Mills, Underground Resistance | 128–138 |
| 10 | `house` | Larry Heard, Frankie Knuckles | 118–126 (Rhodes 패드) |

### 3. 비주얼 무드 (선택, 생략=자동)
| # | 값 | Python 레이어 | 전략 | 특성 |
|---|-----|--------------|------|------|
| 0 | (자동) | music_mood에서 결정 | — | 기본 |
| 1 | `cooper` | Particle + DataStream | breathing | 미니멀, Barcode 없음 |
| 2 | `abstract` | DataMatrix 단일 | cinematic | 정제된 기하학 |
| 3 | `data` | 전체 레이어 최대 | dense | 최고 밀도 |
| 4 | `enometa` | TextData+Barcode+DataStream+DataMatrix | enometa | 데이터아트 풀 세트 |

### 4. 드럼 모드 (필수)
| # | 값 | 동작 |
|---|-----|------|
| 1 | `default` | 무드 기본값 따름 (기본) |
| 2 | `on` | 풀 드럼 강제 ON |
| 3 | `off` | 드럼 강제 OFF |
| 4 | `simple` | 킥+하이햇만, 필인 최소 (32바마다 1회) |
| 5 | `dynamic` | 풀 드럼+SI 최대+필인 2배 (4/8바 주기) |

### 5. 제목 (필수)
입력받으면 kiwipiepy가 키워드 자동 추출

---

## 파이프라인 실행 — 3-Gate 다양성 개입 시스템

**최상위 목표**: 에피소드마다 비주얼과 BGM이 확실히 달라야 한다.
코드 자동화는 "안전한 기본값"을 만들고, Claude가 "이전과 다르게"를 강제한다.

```bash
# 1단계: visual_script까지 실행 후 중단
py scripts/enometa_render.py episodes/epXXX \
  --title "제목" \
  --palette phantom \
  --music-mood techno \
  --drum-mode default \
  --stop-after visual_script
```

---

### ★ Gate 1: 비주얼 다양성 개입 (visual_script 생성 후) — 필수

**목표**: 이전 에피소드와 다른 비주얼 조합 강제

**A. vocab 중복 제거 (필수)**
이전 EP의 `visual_script.json`을 읽어 vocab 빈도표를 만들고, 현재 EP와 비교.
같은 vocab이 50% 이상 겹치면 대체 vocab으로 교체.

```python
# 비교 방법: 이전 EP vocab 집계
prev = episodes/ep{N-1}/visual_script.json
curr = episodes/epXXX/visual_script.json
# vocab별 사용 횟수 비교 → 겹치는 상위 vocab 교체
```

**B. ascii_text 번역 (필수)**
`visual_script.json`에서 `ascii_text: ""` 항목을 찾아 대본 맥락에 맞는 영어 삽입.
- 5자 이하 (비트맵 렌더링 제한)
- "코드" → CODE / PROGRAM / SCRIPT 중 선택
- "자연" → NATURE / WILD / BIO 중 에피소드 톤에 맞게

**C. highlightWords 보강 (권장)**
자동 추출된 `highlightWords` 배열에서 누락된 핵심어 추가.
형태소 분석은 "출력값으로"의 "출력값" 같은 펀치라인 핵심어를 놓침.

**D. terra vocab 강제 삽입 (선택)**
SI 피크 씬 중 하나에 `terra_globe` 또는 `terra_terrain` vocab을 수동으로 semantic 레이어에 추가.
씬당 terra_* 는 최대 1개 제한.

개입 완료 후:
```bash
# 2단계: BGM 생성
py scripts/enometa_render.py episodes/epXXX --title "제목" --step bgm
```

---

### ★ Gate 2: seq_config 음색 설계 (music_script 생성 후) — 필수

**목표**: 이전 에피소드와 다른 음색 + 대본 테마 반영

> ⚠️ `mood_layers`는 편집 금지 (코드가 자동 재생성해서 무시됨)
> ⚠️ `episode`, `duration` 절대 변경 금지

**A. seq_config 비교 (필수)**
`episodes/ep{N-1}/music_script.json`의 `seq_config`와 현재를 비교:

| 비교 항목 | 허용 범위 | 개입 기준 |
|-----------|-----------|-----------|
| `base_bpm` | ±15 BPM 이상 차이 권장 | 같으면 BPM 조정 |
| `kick_character` | 이전과 다른 값 | 같으면 0↔1↔2 교체 |
| `filter_cutoff_base` | ±500 Hz 이상 차이 | 같은 톤이면 조정 |
| `saw_harmonics` | 배음 구성 1개 이상 다름 | 동일이면 교체 |
| `bass_detune` | ±0.002 이상 차이 | 같은 두께면 조정 |

**B. 대본 테마 기반 seq_config 설계 (권장)**

| 대본 테마 | 음색 방향 |
|-----------|-----------|
| 뇌과학/복잡계 | 홀수 배음 강조(1,3,5), `filter_cutoff_base` 낮게(1500~2500) |
| 철학/명상 | `bass_detune` 크게(0.006~0.008), `chorus_depth_ms` 크게(2.5~3.0) |
| 컴퓨팅/데이터 | `kick_character=0`(tight), `filter_cutoff_base` 높게(4000~6000) |
| 인문/감성 | `fm_mod_ratio` 낮게(1.5~2.0), `kick_character=1`(boomy) |

수정 가능한 파라미터 범위:
```json
"seq_config": {
  "kick_character": 0,          // 0=tight / 1=boomy / 2=punchy
  "filter_cutoff_base": 2500,   // 1000~6000 Hz
  "fm_mod_ratio": 1.8,          // 1.5~3.5
  "bass_detune": 0.005,         // 0.001~0.008
  "chorus_depth_ms": 2.0,       // 0.1~3.0
  "saw_harmonics": {"1":1.0, "3":0.6, "5":0.2}  // 배음 구성 자유 설계
}
```

**C. 섹션 볼륨 내러티브 조율 (선택)**
클라이맥스 섹션에서 주요 악기 volume 강조:
```json
"instruments": {
  "acid_bass":    {"active": true, "volume": 0.95},
  "arp_sequence": {"active": true, "volume": 0.80}
}
```

음악 조정 완료 후 사용자에게 BGM 확인 요청:

---

### ★ Gate 3: BGM 청취 확인

사용자가 BGM을 듣고 OK 하면 나머지 진행:

```bash
# 3단계: mix + 나머지
py scripts/enometa_render.py episodes/epXXX --title "제목" --step mix
py scripts/enometa_render.py episodes/epXXX --title "제목" --step audio_analysis
py scripts/enometa_render.py episodes/epXXX --title "제목" --step python_frames
py scripts/enometa_render.py episodes/epXXX --title "제목" --step render
```

---

## 특정 단계만 재실행

```bash
# 단일 단계 재실행
py scripts/enometa_render.py episodes/epXXX --title "제목" --step bgm --force

# 캐스케이드: 해당 단계 + 하위 단계 전부 재실행
py scripts/enometa_render.py episodes/epXXX --title "제목" --step bgm --force --cascade
```

`--step` 선택지: `gen_timing` / `tts` / `script_data` / `visual_script` / `bgm` / `mix` / `audio_analysis` / `python_frames` / `render`

`--stop-after` 선택지: `gen_timing` / `tts` / `script_data` / `visual_script` / `bgm` / `mix` / `audio_analysis` / `python_frames`

## 검증

- `episodes/epXXX/output.mp4` 생성 확인
- 음악 이상 시: `--step bgm --force --cascade` 재실행
- 자막 오류 시: `--step render --force` 재실행

## 완료 후

1. 사용자에게 최종 영상 확인 요청
2. `enometa-publish` 스킬로 업로드 메타데이터 생성
3. `enometa-feedback` 스킬로 피드백 수집
