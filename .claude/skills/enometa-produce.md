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

Claude가 아래 순서로 물어본 뒤 명령을 조합해서 실행한다.

1. **팔레트** — `phantom` / `neon_noir` / `cold_steel` / `ember` / `synapse` / `gameboy` / `c64` / `enometa`
2. **음악 무드** — `raw` / `ambient` / `ikeda` / `experimental` / `minimal` / `chill` / `glitch` / `intense` / `techno`
3. **비주얼 무드** — 자동(생략 가능) / `ikeda` / `cooper` / `abstract` / `data`
4. **드럼** — 무드 기본값(생략) / `--drum` 강제 ON / `--no-drum` 강제 OFF
5. **제목** — 입력받으면 kiwipiepy가 키워드 자동 추출

수집 완료 후 실행:

```bash
py scripts/enometa_render.py episodes/epXXX \
  --title "제목" \
  --palette phantom \
  --music-mood techno \
  --visual-mood ikeda \
  --drum
```

## 특정 단계만 재실행

```bash
py scripts/enometa_render.py episodes/epXXX --title "제목" --step bgm --force
py scripts/enometa_render.py episodes/epXXX --title "제목" --step mix --force
py scripts/enometa_render.py episodes/epXXX --title "제목" --step render --force
```

`--step` 선택지: `gen_timing` / `tts` / `script_data` / `visual_script` / `bgm` / `mix` / `audio_analysis` / `python_frames` / `render`

## 검증

- `episodes/epXXX/output.mp4` 생성 확인
- 음악 이상 시: `--step bgm --force` 재실행
- 자막 오류 시: `--step render --force` 재실행

## 완료 후

1. 사용자에게 최종 영상 확인 요청
2. `enometa-publish` 스킬로 업로드 메타데이터 생성
3. `enometa-feedback` 스킬로 피드백 수집
