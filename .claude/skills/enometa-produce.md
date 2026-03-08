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

수집 완료 후 **BGM 확인 게이트 포함**해서 실행:

```bash
# 1단계: BGM까지 실행 후 중단 (확인용)
py scripts/enometa_render.py episodes/epXXX \
  --title "제목" \
  --palette phantom \
  --music-mood techno \
  --drum-mode default \
  --stop-after bgm
```

BGM 확인 후 OK → 믹스까지:
```bash
# 2단계: mix까지 실행 후 중단
py scripts/enometa_render.py episodes/epXXX --title "제목" --step mix
# 믹스 확인 후 OK → 나머지 전체
py scripts/enometa_render.py episodes/epXXX --title "제목" --step visual_script
```

## 특정 단계만 재실행

```bash
py scripts/enometa_render.py episodes/epXXX --title "제목" --step bgm --force
py scripts/enometa_render.py episodes/epXXX --title "제목" --step mix --force
py scripts/enometa_render.py episodes/epXXX --title "제목" --step render --force
```

`--step` 선택지: `gen_timing` / `tts` / `script_data` / `visual_script` / `bgm` / `mix` / `audio_analysis` / `python_frames` / `render`

`--stop-after` 선택지: `gen_timing` / `tts` / `script_data` / `visual_script` / `bgm` / `mix` / `audio_analysis` / `python_frames`

## 검증

- `episodes/epXXX/output.mp4` 생성 확인
- 음악 이상 시: `--step bgm --force` 재실행
- 자막 오류 시: `--step render --force` 재실행

## 완료 후

1. 사용자에게 최종 영상 확인 요청
2. `enometa-publish` 스킬로 업로드 메타데이터 생성
3. `enometa-feedback` 스킬로 피드백 수집
