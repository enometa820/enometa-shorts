---
name: enometa-produce
description: >
  ENOMETA 에피소드 제작 파이프라인 실행 스킬.
  대본 컨펌 후 TTS → script_data → visual_script → BGM → 렌더링 → 믹싱 → FFT → Remotion 합성.
  8단계 CLI 명령 순차 실행 + 각 단계별 검증 체크리스트 포함.
  트리거 키워드 - 제작 시작, 파이프라인, 영상 만들자, produce, 에피소드 제작
---

# ENOMETA Episode Production Pipeline

## 전제 조건
- ★ 대본이 **컨펌 완료** 상태여야 함 (글 컨펌 게이트 통과)
- ★ 제목이 **확정** 상태여야 함
- 에피소드 폴더 준비: `episodes/epXXX/`
- 필수 입력 파일: `episodes/epXXX/narration_timing.json` (대본 + 타이밍)

## 실행 순서

사용자에게 현재 에피소드 번호(epXXX)와 제목을 확인한 후 아래 순서대로 실행한다.
**각 단계 완료 후 검증을 반드시 수행하고, 실패 시 다음 단계로 넘어가지 않는다.**

### [1] TTS 생성
```bash
py scripts/generate_voice_edge.py \
  episodes/epXXX/narration_timing.json \
  episodes/epXXX/narration.wav
```
- Edge-TTS 전용 (ko-KR-SunHiNeural)
- **generate_voice.py(Chatterbox) 절대 사용 금지**
- 검증: narration.wav 생성 확인 + narration_timing.json 실측 타이밍 업데이트 확인

### [2] 대본 데이터 추출
```bash
py scripts/script_data_extractor.py \
  episodes/epXXX/narration_timing.json
```
- 검증: script_data.json 내 `semantic_intensity` 값이 0.1~0.9 범위에 분포
- 검증: `keywords[].intensity` 필드 존재 (0-1)
- 검증: 미등록 단어 리포트 확인 → 필요 시 `--update-dict`

### [3] 비주얼 스크립트 생성
```bash
py scripts/visual_script_generator.py \
  episodes/epXXX/narration_timing.json \
  --strategy ikeda --episode epXXX --title "에피소드 실제 제목"
```
- ⚠ `--title` 필수! 미지정 시 "제목 미지정"이 영상에 표시됨
- 검증: visual_script.json 내 `meta.render_mode` = `"hybrid"` 확인
- 검증: 씬마다 다른 vocab 조합인지 확인 (단조 반복 금지)

### [4] BGM 생성
```bash
py scripts/enometa_music_engine.py \
  --from-visual episodes/epXXX/visual_script.json \
  --export-raw --arc narrative \
  --script-data episodes/epXXX/script_data.json \
  --episode epXXX \
  episodes/epXXX/narration_timing.json \
  episodes/epXXX/bgm.wav
```
- v8: 항상 ikeda 단일 장르 (--genre 옵션 없음)
- `--arc` 옵션: narrative(기본) | crescendo | flat | adaptive
- 검증: bgm.wav + raw_visual_data.npz 생성 확인

### [5] Python 비주얼 렌더링
```bash
py scripts/visual_renderer.py \
  episodes/epXXX/visual_script.json \
  episodes/epXXX/raw_visual_data.npz \
  episodes/epXXX/script_data.json \
  episodes/epXXX/frames/
```
- 렌더 완료 후: `frames/`를 `public/epXXX/frames/`에 복사 (Remotion staticFile용)
- 검증: 조용한 대사(si≈0.1) vs 극적 대사(si≈0.9) 프레임 비교 → 시각 차이 확인

### [6] 오디오 믹싱
```bash
py scripts/audio_mixer.py \
  episodes/epXXX/narration.wav \
  episodes/epXXX/bgm.wav \
  public/epXXX/mixed.wav \
  --sidechain episodes/epXXX/narration_timing.json
```
- TTS:BGM = 4:6 (narration_volume=0.67, bgm_volume=1.0)
- 사이드체인 덕킹: 나레이션 구간 BGM -3dB

### [7] FFT 분석
```bash
py scripts/audio_analyzer.py \
  public/epXXX/mixed.wav \
  episodes/epXXX/audio_analysis.json 30
```

### [8] Remotion 합성
```bash
# Root.tsx durationInFrames 업데이트 필요
npx remotion render EP00X episodes/epXXX/output.mp4 --concurrency=4
```
- hybrid: Python 배경 + vocab 오버레이 + 제목 + 자막 + PostProcess
- 검증: output.mp4 재생 확인

## 완료 후
1. 사용자에게 최종 영상 확인 요청
2. `enometa-publish` 스킬로 업로드 메타데이터 생성
3. `enometa-feedback` 스킬로 피드백 수집
